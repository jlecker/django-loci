from django.conf import settings

from geopy import geocoders

from simplegeo import Client
from simplegeo.util import APIError


def geocode(query):
    client = Client(
        settings.PLACES_SIMPLEGEO_OAUTH_KEY,
        settings.PLACES_SIMPLEGEO_SECRET
    )
    try:
        data = client.context.get_context_by_address(query)
        point = data.get("query", {}).get("latitude"), data.get("query", {}).get("longitude")
        return None, point[0], point[1]
    except APIError:
        return None, None, None
