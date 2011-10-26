from django import template

from loci.models import Location


register = template.Library()


class LocationMapNode(template.Node):
    
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
    
    def __init__(self, locations=None, latitude=None, longitude=None):
        self.locations = locations
        self.latitude = latitude
        self.longitude = longitude
    
    def render(self, context):
        if self.locations and self.latitude and self.longitude:
            locations = self.locations.resolve(context)
            latitude = self.latitude.resolve(context)
            longitude = self.longitude.resolve(context)
        else:
            locations = Location.objects.all()
            latitude = None
            longitude = None
        
        url = "http://maps.google.com/maps/api/staticmap?"
        url += "size=640x360"
        url += "&maptype=roadmap"
        url += "&sensor=false"
        
        for location in locations:
            url += "&markers=color:blue%%7C%s,%s" % (location.latitude, location.longitude)
        if latitude and longitude:
            url += "&markers=color:red%%7C%s,%s" % (latitude, longitude)
        
        return "<img src=\"%s\">" % url


@register.tag
def google_map(parser, token):
    """
    Usage::
        {% google_map for locations and latitude longitude %}
    """
    return LocationMapNode.handle_token(parser, token)


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
    
    def __init__(self, location, latitude, longitude, varname):
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
        self.varname = varname
    
    def render(self, context):
        location = self.location.resolve(context)
        latitude = self.latitude.resolve(context)
        longitude = self.longitude.resolve(context)
        context[self.varname] = location.distance_to(
            latitude=latitude,
            longitude=longitude
        )
        return ""


@register.tag
def distance(parser, token):
    """
    Usage::
        {% distance from location to latitude longitude as var %}
    """
    return DistanceNode.handle_token(parser, token)
