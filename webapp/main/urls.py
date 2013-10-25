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
    url(r'^(?P<identifier>[0-9A-Z]{10,15})/$',
        views.wishlist_home,
        name='wishlist'),
    url(r'^(?P<identifier>[0-9A-Z]{10,15})/pick-one/$',
        views.wishlist_admin,
        name='wishlist_admin'),
    url(r'^(?P<identifier>[0-9A-Z]{10,15})/your-name/$',
        views.wishlist_your_name,
        name='wishlist_your_name'),
    url(r'^(?P<identifier>[0-9A-Z]{10,15})/already-set-up/$',
        views.wishlist_taken,
        name='wishlist_taken'),
    url(r'^about-us/$',
        views.about_us,
        name='about_us'),
)
