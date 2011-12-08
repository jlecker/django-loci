from django.conf import settings
from django.core.cache import cache
from django.template.defaultfilters import slugify
from django.db.models.loading import get_model

from simplegeo import Client
from simplegeo.util import APIError


def _geo_query(query, query_type=None):
    query = str(query)
    cache_key = 'geo:' + slugify(query)
    location_data = cache.get(cache_key)
    
    if not location_data:
        # data not in cache, do an API query
        client = Client(
            settings.LOCI_SIMPLEGEO_OAUTH_KEY,
            settings.LOCI_SIMPLEGEO_SECRET
        )
        try:
            if query_type == 'address':
                data = client.context.get_context_by_address(query)
            elif query_type == 'ip':
                data = client.context.get_context_by_ip(query)
            else:
                (lat, lon) = query
                data = client.context.get_context(lat, lon)
        except APIError:
            data = {}
        
        # for now, we only need coords and address, but more is available
        query = data.get('query', {})
        location = (query.get('latitude'), query.get('longitude'))
        aprops = data.get('address', {}).get('properties', {})
        address_data = (
            aprops.get('address'),
            aprops.get('city'),
            aprops.get('province'),
            aprops.get('postcode')
        )
        
        location_data = (location, address_data)
        cache.set(cache_key, location_data, 86400)
    
    # get the model here to prevent circular import
    Place = get_model('loci', 'place')

    (location, (address, city, state, zip_code)) = location_data    

    unsaved_place = Place(
        address=address,
        city=city,
        state=state,
        zip_code=zip_code,
        location=location
    )
    
    return unsaved_place


def geocode(address):
    return _geo_query(address, query_type='address')


def geolocate(ip):
    return _geo_query(ip, query_type='ip')


def geolocate_request(request, default_dist=None):
    found = False
    geo_query = request.GET.get('geo')
    if geo_query:
        # if the user has submitted an address, attempt to look it up
        geolocation = geocode(geo_query)
        if geolocation.latitude != None:
            # geolocation found from address, save the query only
            # lookup data should be cached, so no need to save it in session
            request.session['geolocation'] = geo_query
            found = True
    if not found and request.session.get('geolocation'):
        # there is an existing geo_query in the session
        geolocation = geocode(request.session['geolocation'])
        if geolocation.latitude != None:
            found = True
        else:
            # the query did not find anything, remove it from the session
            del request.session['geolocation']
    if not found:
        # no query submitted, or geolocation not found
        # attempt to geolocate from ip address
        # this implementation may be too specific, maybe a setting would work
        ip = request.META.get('HTTP_X_FORWARDED_FOR') or request.META['REMOTE_ADDR']
        geolocation = geolocate(ip)
        if geolocation.latitude != None:
            found = True
    if not found:
        # could not otherwise find location data, fall back to station ZIP code
        geolocation = geocode(settings.DEFAULT_ZIP_CODE)
    geolocation.nearby_distance = 160
    if found:
        try:
            geolocation.nearby_distance = int(request.GET.get('dist', ''))
        except ValueError:
            if default_dist:
                geolocation.nearby_distance = default_dist
    return geolocation
