from django.conf.urls import patterns, url, include

from . import views

urlpatterns = patterns(
    '',
    url(r'^$',
        views.home,
        name='home'),
    url(r'^dashboard/$',
        views.dashboard,
        name='dashboard'),
    url(r'^data/wishlists/$',
        views.wishlists_data,
        name='wishlists_data'),
    url(r'^wishlist/(?P<identifier>[a-f0-9]{8})/$',
        views.wishlist_data,
        name='wishlist_data'),
)
