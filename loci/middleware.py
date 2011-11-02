from loci.utils import geolocate


class GeoLocationMiddleware(object):
    
    def resolve_ip(self, request):
        return request.META['REMOTE_ADDR']
    
    def process_request(self, request):
        ip = self.resolve_ip(request)
        if not ip:
            request.geolocation = None
            return

        request.geolocation = geolocate(ip)
