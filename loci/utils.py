import json

from django.conf import settings
from django.core.cache import cache
from django.template.defaultfilters import slugify
from django.db.models.loading import get_model
from django.contrib.sites.models import get_current_site

import requests


MAX_DIST = getattr(settings, 'LOCI_NEARBY_DISTANCE', 80)


def _geo_query(query, query_type=None):
    cache_key = 'geo:' + slugify(str(query))
    location_data = cache.get(cache_key)
    
    if not location_data:
        # data not in cache, do an API query
        api_url = 'http://maps.googleapis.com/maps/api/geocode/json?'
        if query_type == 'address':
            api_url += 'address=%s' % query
        else:
            api_url += 'latlng=%s,%s' % query
        api_url += '&sensor=false'
        try:
            resp = requests.get(api_url)
        except requests.exceptions.RequestException:
            data = {}
        else:
            if resp.status_code == 200:
                data = json.loads(resp.text)
            else:
                data = {}
        
        # for now, we only need coords and address, but more is available
        results = data.get('results', [])
        if results:
            result = results[0]
        else:
            result = {}

        latlon = result.get('geometry', {}).get('location', {})
        location = (latlon.get('lat'), latlon.get('lng'))

        street_address = city = state = zip_code = None
        number = route = ''
        acomps = result.get('address_components', [])
        for comp in acomps:
            if 'street_number' in comp['types']:
                number = comp['long_name']
            if 'route' in comp['types']:
                route = comp['long_name']
            if 'locality' in comp['types']:
                city = comp['long_name']
            if 'administrative_area_level_1' in comp['types']:
                state = comp['short_name']
            if 'postal_code' in comp['types']:
                zip_code = comp['long_name']
        if number or route:
            street_address = number + ' ' + route
        
        if query_type == 'address' and not (city and state and zip_code) and \
                location != (None, None):
            # missing some data, try to get it from coords
            loc_data = get_geo(location)
            if not city:
                city = loc_data.city
            if not state:
                state = loc_data.state
            if not zip_code:
                zip_code = loc_data.zip_code
        
        address_data = (
            street_address,
            city,
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


def get_geo(location):
    return _geo_query(location)


def geolocate_request(request, default_dist=None):
    found = False
    geo_query = request.GET.get('geo')
    try:
        found_dist = int(request.GET.get('dist', ''))
    except ValueError:
        found_dist = request.session.get('geodistance', default_dist or MAX_DIST)
    if geo_query:
        # if the user has submitted an address, attempt to look it up
        geolocation = geocode(geo_query)
        if geolocation.latitude != None:
            # geolocation found from address, save the query only
            # lookup data should be cached, so no need to save it in session
            request.session['geolocation'] = geo_query
            request.session['geodistance'] = found_dist
            found = True
    if not found and request.session.get('geolocation'):
        # there is an existing geo_query in the session
        geolocation = geocode(request.session['geolocation'])
        if geolocation.latitude != None:
            found = True
        else:
            # the query did not find anything, remove it from the session
            del request.session['geodistance']
            del request.session['geolocation']
    if not found:
        # could not otherwise find location data, fall back to station ZIP code
        try:
            zip_code = get_current_site(request).profile.zip_code
        except AttributeError:
            zip_code = settings.DEFAULT_ZIP_CODE
        defloc = geocode(zip_code)
        geolocation = defloc
    if found:
        geolocation.nearby_distance = found_dist
    else:
        geolocation.nearby_distance = MAX_DIST
    return geolocation
