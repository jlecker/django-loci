from django.db import models
from django.conf import settings
from django.contrib.localflavor.us.models import USStateField

import geopy.distance

from loci.utils import geocode


class PlaceManager(models.Manager):
    
    def __init__(self):
        super(PlaceManager, self).__init__()
    
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


class Place(models.Model):
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=180, blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = USStateField(blank=True)
    zip_code = models.CharField(max_length=10, blank=True)
    
    latitude = models.FloatField(null=True, blank=True, default=None)
    longitude = models.FloatField(null=True, blank=True, default=None)
    
    objects = PlaceManager()
    
    def __unicode__(self):
        return u'%s (%s, %s)' % (self.name, self.latitude, self.longitude)
    
    def save(self, *args, **kwargs):
        (self.location, address_tuple) = geocode(self.full_address)
        super(Place, self).save(*args, **kwargs)
    
    def distance_to(self, latitude, longitude):
        return geopy.distance.distance(
            (latitude, longitude),
            self.location,
        )
    
    @property
    def full_address(self):
        return '%s, %s %s %s' % (
            self.address,
            self.city,
            self.state,
            self.zip_code,
        )

    @property
    def location(self):
        return (self.latitude, self.longitude)

    @location.setter
    def location(self, point):
        (self.latitude, self.longitude) = point
