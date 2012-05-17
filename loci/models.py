"""
Models
======

The :class:`Place` model and its associated :class:`Manager` and
:class:`QuerySet` subclasses.

"""

from django.db import models
from django.db.models.query import QuerySet
from django.conf import settings
from django.contrib.localflavor.us.models import USStateField

from geopy.units import nautical, degrees
import geopy.distance

from loci.utils import geocode


class PlaceManager(models.Manager):
    """
    A :class:`Manager` designed for the :class:`Place` model.

    Returns a :class:`PlaceQuerySet` and proxies the :method:`near` method.

    """

    def get_query_set(self):
        return PlaceQuerySet(self.model, using=self.db)

    def near(self, *args, **kwargs):
        return self.get_query_set().near(*args, **kwargs)


class PlaceQuerySet(QuerySet):
    def near(self, location, distance=None):
        """
        Returns a list of items in the :class:`QuerySet` which are
        within the given distance of the given location. Does NOT return
        a :class:`QuerySet`.

        Accepts either a :class:`Place` instance or a (lat, lon) tuple
        for location. Also accepts a Place instance with a
        ``nearby_distance`` attribute added (as returned from
        :func:`loci.utils.geolocate_request`); in this case, distance
        need not be explicitly passed.
        
        """
        
        # figure out if we received an object or tuple and get the location
        try:
            (latitude, longitude) = location.location
        except AttributeError:
            (latitude, longitude) = location

        # make sure we have a valid location
        if not (latitude and longitude):
            return []
        
        # get the passed distance or attached to Place
        if distance == None:
            try:
                distance = location.nearby_distance
            except AttributeError:
                raise ValueError('Distance must be attached or passed explicitly.')

        # prune down the set of places before checking precisely
        #deg_lat = Decimal(str(degrees(arcminutes=nautical(miles=distance))))
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
                if exact_distance.miles <= distance:
                    locations.append(location)
        return locations


class Place(models.Model):
    """
    A basic place model. Great for subclassing.

    """

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
            geoloc = geocode(self.full_address)
            self.location = geoloc.location
            if not self.city:
                self.city = geoloc.city
            if not self.state:
                self.state = geoloc.state
            if not self.zip_code:
                self.zip_code = geoloc.zip_code
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
