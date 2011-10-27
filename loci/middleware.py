from django.conf import settings
from django.core.cache import cache
from django.utils import simplejson as json

from simplegeo import Client
from simplegeo.util import APIError


class GeoLocationMiddleware(object):
    
    def resolve_ip(self, request):
        return request.META["REMOTE_ADDR"]
    
    def process_request(self, request):
        ip = self.resolve_ip(request)
        if not ip:
            request.user.location = None
            return
        
        cache_key = "geo:%s" % ip
        
        data = cache.get(cache_key)
        if data is None:
            # @@@ not sure if this is doing anything other then just creating
            #     an object, if so might want to cache this
            client = Client(
                settings.LOCI_SIMPLEGEO_OAUTH_KEY,
                settings.LOCI_SIMPLEGEO_SECRET
            )
            try:
                data = client.context.get_context_by_ip(ip)
                cache.set(cache_key, json.dumps(data, use_decimal=True), 86400)
            except APIError:
                data = None
        else:
            data = json.loads(data, use_decimal=True)
        
        request.user.location = data
