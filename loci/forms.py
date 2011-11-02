from django import forms

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
