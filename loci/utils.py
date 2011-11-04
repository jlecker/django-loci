from django.conf import settings
from django.core.cache import cache
from django.template.defaultfilters import slugify

from simplegeo import Client
from simplegeo.util import APIError


def _geo_query(query, query_type=None):
    query = str(query)
    cache_key = 'geo:' + slugify(query)
    location = cache.get(cache_key)
    if location:
        return location
    
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
    address = (
        aprops.get('address'),
        aprops.get('city'),
        aprops.get('province'),
        aprops.get('postcode')
    )
    
    # not sure if tuple-izing everything is the best way
    cache.set(cache_key, (location, address), 86400)
    return (location, address)


def geocode(address):
    return _geo_query(address, query_type='address')


def geolocate(ip):
    return _geo_query(ip, query_type='ip')


def smart_geo(request):
    geo_query = request.GET.get('geo')
    if geo_query:
        # if the user has submitted an address, attempt to look it up
        geolocation = geocode(geo_query)
        if geolocation[0][0] is not None:
            # geolocation found from address, save it
            request.session['geolocation'] = geolocation
            return geolocation
        if request.session.get('geolocation'):
            # there is existing geolocation data in the session
            return request.session.get('geolocation')
    # no query submitted, or geolocation not found
    # attempt to geolocate from ip address
    # this implementation may be too specific, maybe a setting would work
    ip = request.META.get('HTTP_X_FORWARDED_FOR') or request.META['REMOTE_ADDR']
    geolocation = geolocate(ip)
    if geolocation[0][0] is not None:
        return geolocation
    # could not otherwise find location data, fall back to station ZIP code
    return geocode(settings.DEFAULT_ZIP_CODE)
