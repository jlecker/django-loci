from django import template

from loci.models import Place


register = template.Library()


class PlaceMapNode(template.Node):
    
    @classmethod
    def handle_token(cls, parser, token):
        bits = token.split_contents()
        
        if len(bits) not in (1, 6):
            raise template.TemplateSyntaxError
        if len(bits) == 6:
            if bits[1] != "for" and bits[3] != "and":
                raise template.TemplateSyntaxError
            
            return cls(
                parser.compile_filter(bits[2]),
                parser.compile_filter(bits[4]),
                parser.compile_filter(bits[5])
            )
        return cls()
    
    def __init__(self, places=None, latitude=None, longitude=None):
        self.places = places
        self.latitude = latitude
        self.longitude = longitude
    
    def render(self, context):
        if self.places and self.latitude and self.longitude:
            places = self.places.resolve(context)
            latitude = self.latitude.resolve(context)
            longitude = self.longitude.resolve(context)
        else:
            places = Place.objects.all()
            latitude = None
            longitude = None
        
        url = "http://maps.google.com/maps/api/staticmap?"
        url += "size=640x360"
        url += "&maptype=roadmap"
        url += "&sensor=false"
        
        for place in places:
            url += "&markers=color:blue%%7C%s,%s" % (place.latitude, place.longitude)
        if latitude and longitude:
            url += "&markers=color:red%%7C%s,%s" % (latitude, longitude)
        
        return "<img src=\"%s\">" % url


@register.tag
def google_map(parser, token):
    """
    Usage::
        {% google_map for places and latitude longitude %}
    """
    return PlaceMapNode.handle_token(parser, token)


class DistanceNode(template.Node):
    
    @classmethod
    def handle_token(cls, parser, token):
        bits = token.split_contents()
        if len(bits) != 8:
            raise template.TemplateSyntaxError
        if bits[1] != "from" and bits[3] != "to" and bits[6] != "as":
            raise template.TemplateSyntaxError
        return cls(
            parser.compile_filter(bits[2]),
            parser.compile_filter(bits[4]),
            parser.compile_filter(bits[5]),
            bits[7]
        )
    
    def __init__(self, place, latitude, longitude, varname):
        self.place = place
        self.latitude = latitude
        self.longitude = longitude
        self.varname = varname
    
    def render(self, context):
        place = self.place.resolve(context)
        latitude = self.latitude.resolve(context)
        longitude = self.longitude.resolve(context)
        context[self.varname] = place.distance_to(
            latitude=latitude,
            longitude=longitude
        )
        return ""


@register.tag
def distance(parser, token):
    """
    Usage::
        {% distance from place to latitude longitude as var %}
    """
    return DistanceNode.handle_token(parser, token)
