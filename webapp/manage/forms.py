from django import forms

from webapp.main.forms import BaseModelForm
from webapp.main import models


class PaymentEditForm(BaseModelForm):

    class Meta:
        model = models.Payment
        fields = ('name', 'message', 'refund_amount', 'declined')

    #def __init__(self, *args, **kwargs):
