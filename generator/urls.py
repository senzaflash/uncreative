from django.conf.urls import patterns, url

from generator import views

urlpatterns = patterns('',
	
	url(r'^$', views.index, name='index'),
	url(r'^index2/$', views.index2, name='index2'),

	url(r'^add/$', views.add, name='add'),
	url(r'^objects/$', views.objects, name='objects'),
	url(r'^objects/urtexts/(?P<username>q?[a-zA-Z0-9_-]{3,20})?/?$', views.userquotes, name='userquotes'),
	url(r'^objects/(?P<text_id>q?\d+)/?$', views.permalink, name='permalink'),
	url(r'^signup/?$', views.signup, name='signup'),
	url(r'^login/?$', views.userlogin, name='login'),
	url(r'^logout/?$', views.userlogout, name='logout'),
	url(r'^about/$', views.about, name='about'),

)
