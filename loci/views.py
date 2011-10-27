from django.shortcuts import render, redirect
from django.template import RequestContext

from loci.forms import LocationForm
from loci.models import Location, Place


def home(request):
    
    if request.method == "POST":
        form = LocationForm(request.POST)
        if form.is_valid():
            location = form.save()
            Place.objects.create(
                location=location,
                name=form.cleaned_data["name"],
                phone=form.cleaned_data["phone"],
                website=form.cleaned_data["website"]
            )
            return redirect("home")
    else:
        form = LocationForm()
    
    return render(request, "loci/home.html", {
        "form": form,
        "locations": Location.objects.all()
    })
