from django.conf import settings
from django.core.cache import cache
from django.template.defaultfilters import slugify
from django.db.models.loading import get_model

from simplegeo import Client
from simplegeo.util import APIError


MAX_DIST = 160


def _geo_query(query, query_type=None):
    cache_key = 'geo:' + slugify(str(query))
    location_data = cache.get(cache_key)
    
    if not location_data:
        # data not in cache, do an API query
        client = Client(
            settings.LOCI_SIMPLEGEO_OAUTH_KEY,
            settings.LOCI_SIMPLEGEO_SECRET
        )
        try:
            if query_type == 'address':
                data = client.context.get_context_by_address(str(query))
            elif query_type == 'ip':
                data = client.context.get_context_by_ip(str(query))
            else:
                (lat, lon) = query
                data = client.context.get_context(lat, lon)
        except APIError:
            data = {}
        
        # for now, we only need coords and address, but more is available
        query = data.get('query', {})
        location = (query.get('latitude'), query.get('longitude'))
        aprops = data.get('address', {}).get('properties', {})
        state = aprops.get('province')
        zip_code = aprops.get('postcode')
        
        # alternate ways to get get state and ZIP
        # because address is not always available
        if not (state and zip_code):
            for feature in data.get('features', []):
                for classifier in feature.get('classifiers', []):
                    if classifier.get('subcategory') == 'State':
                        state = feature.get('abbr')
                    if classifier.get('category') == 'Postal Code':
                        zip_code = feature.get('name')
        
        address_data = (
            aprops.get('address'),
            aprops.get('city'),
            state,
            zip_code,
        )
        location_data = (location, address_data)
        if data:
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

def get_geo(location):
    return _geo_query(location)


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
        ip = ip.rsplit(',')[-1].strip()
        geolocation = geolocate(ip)
        defloc = geocode(settings.DEFAULT_ZIP_CODE)
        if geolocation.latitude != None:
            if geolocation.distance_to(defloc.latitude, defloc.longitude) <= MAX_DIST:
                found = True
    if not found:
        # could not otherwise find location data, fall back to station ZIP code
        geolocation = defloc
    geolocation.nearby_distance = MAX_DIST
    if found:
        try:
            geolocation.nearby_distance = int(request.GET.get('dist', ''))
        except ValueError:
            if default_dist:
                geolocation.nearby_distance = default_dist
    return geolocation
