from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',

	url(r'^/?', include('generator.urls')),
    # Examples:
    # url(r'^$', 'uncreative.views.home', name='home'),
    # url(r'^uncreative/', include('uncreative.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

#if not settings.DEBUG:
#	urlpatterns += staticfiles_urlpatterns()