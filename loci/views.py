from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

from loci.forms import LocationForm
from loci.models import Location, Place


def homepage(request):
    
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
    
    return render_to_response("homepage.html", {
        "form": form,
        "locations": Location.objects.all()
    }, context_instance=RequestContext(request))
