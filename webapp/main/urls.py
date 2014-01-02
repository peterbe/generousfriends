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
    url(r'^about/$',
        views.about,
        name='about'),
    url(r'^terms/$',
        views.terms,
        name='terms'),
    url(r'^help/$',
        views.help_page,
        name='help'),
    url(r'^rules/$',
        views.rules,
        name='rules'),
    url(r'^how-it-works/$',
        views.how_it_works,
        name='how_it_works'),
    url(r'^instructions/shipping-address/$',
        views.instructions_shipping_address,
        name='instructions_shipping_address'),
    url(r'^inboundemail/$',
        views.inbound_email,
        name='inbound_email'),
   url(r'^(?P<identifier>[a-f0-9]{8})/$',
        views.wishlist_home,
        name='wishlist'),
    url(r'^(?P<identifier>[a-f0-9]{8})/pick-one/$',
        views.wishlist_pick_one,
        name='wishlist_pick_one'),
    url(r'^(?P<identifier>[a-f0-9]{8})/pick-another/$',
        views.wishlist_pick_another,
        name='wishlist_pick_another'),
    url(r'^(?P<identifier>[a-f0-9]{8})/settings/$',
        views.wishlist_settings,
        name='wishlist_settings'),
    url(r'^(?P<identifier>[a-f0-9]{8})/close/$',
        views.close_item,
        name='close_item'),
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
    url(r'^(?P<identifier>[a-f0-9]{8})/share-by-email/$',
        views.wishlist_share_by_email,
        name='wishlist_share_by_email'),
    url(r'^find/$',
        views.find_wishlist,
        name='find_wishlist'),
    url(r'^debugger$',
        views.debugger,
        name='debugger'),

 )
