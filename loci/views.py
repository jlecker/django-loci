from django.shortcuts import render, redirect
from django.template import RequestContext

from loci.forms import PlaceForm
from loci.models import Place


def home(request):
    if request.method == "POST":
        form = PlaceForm(request.POST)
        if form.is_valid():
            place = form.save()
            return redirect("home")
    else:
        form = PlaceForm()
    
    return render(request, "loci/home.html", {
        "form": form,
        "places": Place.objects.all()
    })
