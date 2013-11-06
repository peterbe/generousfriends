from django.conf.urls import patterns, url, include

from . import views

urlpatterns = patterns(
    '',
    url(r'^$',
        views.start,
        name='start'),
    url(r'^start/$',
        views.wishlist_start,
        name='wishlist_start'),
    url(r'^verify/(?P<identifier>\w{16})$',
        views.wishlist_verify,
        name='wishlist_verify'),
    #url(r'^wishlist/$',
    #    views.home,
    #    name='home'),
    url(r'^about/$',
        views.about,
        name='about'),
    url(r'^help/$',
        views.help,
        name='help'),
    url(r'^inboundemail/$',
        views.inbound_email,
        name='inbound_email'),
   url(r'^(?P<identifier>[a-f0-9]{8})/$',
        views.wishlist_home,
        name='wishlist'),
    url(r'^(?P<identifier>[a-f0-9]{8})/pick-one/$',
        views.wishlist_admin,
        name='wishlist_admin'),
    url(r'^(?P<identifier>[a-f0-9]{8})/your-name/$',
        views.wishlist_your_name,
        name='wishlist_your_name'),
    url(r'^(?P<identifier>[a-f0-9]{8})/your-message/$',
        views.wishlist_your_message,
        name='wishlist_your_message'),
    url(r'^(?P<identifier>[a-f0-9]{8})/already-set-up/$',
        views.wishlist_taken,
        name='wishlist_taken'),
    url(r'^(?P<identifier>[a-f0-9]{3,8})/$',
        views.wishlist_home,
        {'fuzzy': True},
        name='wishlist_fuzzy'),
 )
