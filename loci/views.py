from django.shortcuts import render, redirect
from django.template import RequestContext

from loci.utils import geolocate_request
from loci.forms import PlaceForm, GeolocationForm
from loci.models import Place


def home(request):
    request_location = geolocate_request(request)
    geo_form = GeolocationForm(initial={'geo': request_location.zip_code})
    if request.method == "POST":
        form = PlaceForm(request.POST)
        if form.is_valid():
            place = form.save()
            return redirect("home")
    else:
        form = PlaceForm()
    
    return render(request, "loci/home.html", {
        "request_location": request_location,
        "geo_form": geo_form,
        "form": form,
        "places": Place.objects.all()
    })
