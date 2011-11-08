from django.db import models
from django.db.models.query import QuerySet
from django.conf import settings
from django.contrib.localflavor.us.models import USStateField

from geopy.units import nautical, degrees
import geopy.distance

from loci.utils import geocode


class PlaceManager(models.Manager):
    def get_query_set(self):
        return PlaceQuerySet(self.model, using=self.db)

    def near(self, *args, **kwargs):
        return self.get_query_set().near(*args, **kwargs)


class PlaceQuerySet(QuerySet):
    def near(self, location, distance):
        """
        Returns a list of items in the QuerySet which are within the given
        distance of the given location. Does NOT return a QuerySet.
        
        """

        # prune down the set of all locations to something we can quickly check
        # precisely
        (latitude, longitude) = location
        deg_lat = degrees(arcminutes=nautical(miles=distance))
        lat_range = (latitude - deg_lat, latitude + deg_lat)
        long_range = (longitude - deg_lat * 2, longitude + deg_lat * 2)
        queryset = self.filter(
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
        return locations


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
        if self.full_address and self.location == (None, None):
            (self.location, address_tuple) = geocode(self.full_address)
        super(Place, self).save(*args, **kwargs)
    
    def distance_to(self, latitude, longitude):
        return geopy.distance.distance(
            (latitude, longitude),
            self.location,
        )
    
    @property
    def full_address(self):
        parts = []
        if self.address:
            parts.append(self.address + ',')
        if self.city:
            parts.append(self.city)
        if self.state:
            parts.append(self.state)
        if self.zip_code:
            parts.append(self.zip_code)
        return ' '.join(parts)

    @property
    def location(self):
        return (self.latitude, self.longitude)

    @location.setter
    def location(self, point):
        (self.latitude, self.longitude) = point
