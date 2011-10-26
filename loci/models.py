from decimal import Decimal

from django.db import models
from django.conf import settings

from django.contrib.localflavor.us.models import USStateField, PhoneNumberField

import geopy.distance

# from simplegeo import Client
# from simplegeo.util import APIError


class LocationManager(models.Manager):
    
    def __init__(self):
        super(LocationManager, self).__init__()
    
    def near(self, latitude=None, longitude=None, distance=None):
        if not (latitude and longitude and distance):
            return []
        
        queryset = super(LocationManager, self).get_query_set()
        
        # prune down the set of all locations to something we can quickly check
        # precisely
        minutes = Decimal(str(geopy.distance.nm(miles=distance)))
        rough_distance = Decimal(str(geopy.distance.arc_degrees(arcminutes=minutes) * 2))
        lat_range = (latitude - rough_distance, latitude + rough_distance)
        long_range = (longitude - rough_distance, longitude + rough_distance)
        
        queryset = queryset.filter(
            latitude__range=lat_range,
            longitude__range=long_range
        )
        
        locations = []
        for location in queryset:
            if location.latitude and location.longitude:
                exact_distance = geopy.distance.distance(
                    (latitude, longitude),
                    (location.latitude, location.longitude)
                )
                exact_distance.calculate()
                
                if exact_distance.miles <= distance:
                    locations.append(location)
        
        queryset = queryset.filter(id__in=[l.id for l in locations])
        
        return queryset


class Location(models.Model):

    latitude = models.FloatField(null=True, blank=True, editable=False)
    longitude = models.FloatField(null=True, blank=True, editable=False)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = USStateField(blank=True)
    zip_code = models.CharField(max_length=10, blank=True, db_column="zip")

    objects = LocationManager()
    
    def __unicode__(self):
        return u"%s %s, %s %s at (%s, %s)" % (
            self.address,
            self.city,
            self.state,
            self.zip_code,
            self.latitude,
            self.longitude
        )
    
    def distance_to(self, latitude, longitude):
        exact_distance = geopy.distance.distance(
            (latitude, longitude),
            (self.latitude, self.longitude)
        )
        return exact_distance
    
    @property
    def full_address(self):
        return "%s %s, %s %s" % (
            self.address,
            self.city,
            self.state,
            self.zip_code
        )
    
    def geo_code(self):
        from simplegeo import Client
        from simplegeo.util import APIError
        
        client = Client(
            settings.PLACES_SIMPLEGEO_OAUTH_KEY,
            settings.PLACES_SIMPLEGEO_SECRET
        )
        
        try:
            data = client.context.get_context_by_address(self.full_address)
            # There is a ton of useful data in this dict: might be worth
            # storing the rest of it somewhere
            # {..., 'query': {'address': '54403',
            #           'latitude': Decimal('44.952863'),
            #           'longitude': Decimal('-89.531804')},
            # ...}
            point = data.get("query", {}).get("latitude"), data.get("query", {}).get("longitude")
            self.latitude, self.longitude = point
        except APIError:
            self.latitude = None
            self.longitude = None
    
    def save(self, *args, **kwargs):
        self.geo_code()
        super(Location, self).save(*args, **kwargs)


class Place(models.Model):
    
    location = models.ForeignKey(Location)
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    phone = PhoneNumberField(blank=True)
    website = models.URLField(blank=True)
    
    def __unicode__(self):
        return unicode(self.name)
