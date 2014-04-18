from django import forms
from django.conf import settings

from loci.models import Place


class PlaceForm(forms.ModelForm):
    class Meta:
        model = Place
        fields = [
            "name",
            "address",
            "city",
            "state",
            "zip_code"
        ]


class GeolocationForm(forms.Form):
    geo = forms.CharField(label='Location')


DISTANCE_CHOICES = getattr(
    settings,
    'LOCI_DISTANCE_CHOICES',
    [5, 10, 20, 40, 80, 160]
)

class GeolocationDistanceForm(GeolocationForm):
    dist = forms.ChoiceField(
        choices=[(m, '%s miles' % m) for m in DISTANCE_CHOICES],
        initial=160,
        label='Distance'
    )


def geo_form_for_place(place):
    return GeolocationForm(initial={'geo': place.zip_code})


def geodist_form_for_place(request_place):
    return GeolocationDistanceForm(initial={
        'geo': request_place.zip_code, 'dist': request_place.nearby_distance})
