import re
import decimal

from django import forms

from . import utils

WISHLIST_ID_REGEX = re.compile('^[0-9A-Z]{10,15}$')


class WishlistIDForm(forms.Form):

    amazon_id = forms.CharField()

    def clean_amazon_id(self):
        value = self.cleaned_data['amazon_id']
        if '://' in value:
            value = utils.find_wishlist_amazon_id(value)
            if not value:
                raise forms.ValidationError("Doesn't look like a valid Wish List ID")

        if not WISHLIST_ID_REGEX.match(value):
            raise forms.ValidationError("Doesn't look like a valid Wish List ID")

        return value


class PaymentForm(forms.Form):
    uri = forms.CharField()
    amount = forms.CharField()
    hash = forms.CharField(required=False)
    id = forms.CharField(required=False)
    email = forms.EmailField(required=False)

    def __init__(self, *args, **kwargs):
        self.item = kwargs.pop('item')
        super(PaymentForm, self).__init__(*args, **kwargs)

    def clean_amount(self):
        value = self.cleaned_data['amount']
        value = str(value).replace('$', '').strip()
        try:
            value = decimal.Decimal(value)
        except decimal.InvalidOperation as x:
            raise forms.ValidationError(str(x))
        if value < 0.5:
            raise forms.ValidationError('Minimum is $.50')
        left = self.item.amount_remaining
        if value > left:
            raise forms.ValidationError('Too much. Only $%.2f left to contribute.' % left)
        return value


class YourNameForm(forms.Form):
    your_email = forms.EmailField()
    your_name = forms.CharField()


class TakenForm(forms.Form):
    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        self.wishlist = kwargs.pop('wishlist')
        super(TakenForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        value = self.cleaned_data['email']
        if value.lower().strip() != self.wishlist.email.lower().strip():
            raise forms.ValidationError('Not the same email address')
        return value
