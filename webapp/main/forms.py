import re
import decimal

from django import forms


WISHLIST_URL_ID_REGEX = re.compile('/([0-9A-Z]{10,15})/')
WISHLIST_ID_REGEX = re.compile('^[0-9A-Z]{10,15}$')


class WishlistIDForm(forms.Form):

    identifier = forms.CharField()

    def clean_identifier(self):
        value = self.cleaned_data['identifier']
        if '://' in value:
            value = WISHLIST_URL_ID_REGEX.findall(value)[0]

        if not WISHLIST_ID_REGEX.match(value):
            raise forms.ValidationError("Doesn't look like a valid Wish List ID")

        return value


class PaymentForm(forms.Form):
    uri = forms.CharField()
    amount = forms.CharField()
    hash = forms.CharField(required=False)
    id = forms.CharField(required=False)
    email = forms.EmailField(required=False)

    def clean_amount(self):
        value = self.cleaned_data['amount']
        value = str(value).replace('$', '').strip()
        try:
            value = decimal.Decimal(value)
        except decimal.InvalidOperation as x:
            raise forms.ValidationError(str(x))
        if value < 0.5:
            raise forms.ValidationError('Minimum is $.50')
        return value


class YourNameForm(forms.Form):
    your_email = forms.EmailField()
    your_name = forms.CharField()
