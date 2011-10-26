from django import forms

from loci.models import Location


class LocationForm(forms.ModelForm):
    
    name = forms.CharField()
    phone = forms.CharField(required=False)
    website = forms.CharField(required=False)
    
    class Meta:
        model = Location
        fields = [
            "address",
            "city",
            "state",
            "zip_code"
        ]
