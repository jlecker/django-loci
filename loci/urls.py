from django.conf.urls import patterns, url


urlpatterns = patterns('loci.views',
    url(r'^$', 'home', name='loci_home'),
)
