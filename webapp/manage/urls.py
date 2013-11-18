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
        views.wishlists,
        name='wishlists'),
    url(r'^data/wishlists/data/$',
        views.wishlists_data,
        name='wishlists_data'),
    url(r'^wishlist/(?P<identifier>[a-f0-9]{8})/$',
        views.wishlist_data,
        name='wishlist_data'),
    url(r'^data/payments/$',
        views.payments,
        name='payments'),
    url(r'^data/payments/data/$',
        views.payments_data,
        name='payments_data'),
    url(r'^data/payments/(?P<id>\d+)/$',
        views.payment_edit,
        name='payment_edit'),
    #url(r'^item/(?P<identifier>[a-f0-9]{8})/$',
    #    views.item_data,
    #    name='item_data'),
)
