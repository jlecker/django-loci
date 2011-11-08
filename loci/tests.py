from django.test import TestCase

from loci.models import Place
from loci.utils import geocode


class ModelTests(TestCase):
    def test_place_creation(self):

        # make sure geocode is working
        assert(geocode('54403')[0][0])

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
