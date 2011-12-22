from django.test import TestCase

from loci.models import Place
from loci.utils import geocode, geolocate_request


class _Mock(object):
    pass


class ModelTests(TestCase):
    
    def test_place_creation(self):
        # make sure geocode is working
        assert(geocode('54403').latitude)

        # create a Place from address; location should be added automatically
        place1 = Place.objects.create(
            name='MWC Wausau',
            address='557 Scott St',
            city='Wausau',
            state='WI',
            zip_code='54403'
        )
        self.assertTrue(place1.latitude)
        self.assertTrue(place1.longitude)

        # create a Place with no address but location; should not be changed
        place2 = Place.objects.create(
            name='nowhere in particular',
            location=(45, 45)
        )
        self.assertFalse(place2.address)
        self.assertEqual(place2.location, (45, 45))

        # create a Place with address and location, should not be changed
        place3 = Place.objects.create(
            name='MWC Wausau with wrong location',
            address='557 Scott St',
            city='Wausau',
            state='WI',
            zip_code='54403',
            location=(-45, -45)
        )
        self.assertEqual(place3.address, '557 Scott St')
        self.assertEqual(place3.location, (-45, -45))
    
    def test_near_query(self):
        test_place = Place.objects.create(
            name='Wausau',
            city='Wausau',
            state='WI'
        )
        location = geocode('54401')
        
        # lookup using the location tuple and explicit distance
        nearby = Place.objects.near(location.location, 20)
        self.assertEqual(len(nearby), 1)
        self.assertTrue(test_place in nearby)
        
        # lookup with location object and explicit distance
        nearby = Place.objects.near(location, 20)
        self.assertEqual(len(nearby), 1)
        self.assertTrue(test_place in nearby)
        
        # lookup with no distance info should fail
        self.assertRaises(ValueError, Place.objects.near, location)
        
        # lookup with distance attached but not passed explicitly
        location.nearby_distance = 20
        nearby = Place.objects.near(location)
        self.assertEqual(len(nearby), 1)
        self.assertTrue(test_place in nearby)


class LookupTests(TestCase):
    def test_request_geolocation(self):
        # make a "request" to pass to geolocate_request
        mock_request = _Mock()
        mock_request.GET = {}
        mock_request.session = {}
        mock_request.META = {'REMOTE_ADDR': '127.0.0.1'}

        # should fall back to DEFAULT_ZIP_CODE
        l1 = geolocate_request(mock_request, 100)
        self.assertTrue(l1.location)
        self.assertEqual(l1.nearby_distance, 160)
        
        # should find the new ZIP, with a different location than default
        mock_request.GET['geo'] = '54481'
        l2 = geolocate_request(mock_request, 50)
        self.assertTrue(l2.location)
        self.assertEqual(l2.nearby_distance, 50)
        self.assertNotEqual(l2.location, l1.location)
        
        # geolocation should be saved in the session now
        del mock_request.GET['geo']
        l3 = geolocate_request(mock_request)
        self.assertEqual(l3.location, l2.location)
