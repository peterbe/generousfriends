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
    #url(r'^wishlist/$',
    #    views.home,
    #    name='home'),
    url(r'^(?P<identifier>[0-9A-Z]{10,15})/$',
        views.wishlist_home,
        name='wishlist'),
    url(r'^(?P<identifier>[0-9A-Z]{10,15})/configure/$',
        views.wishlist_admin,
        name='wishlist_admin'),
)
