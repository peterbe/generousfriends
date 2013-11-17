import re
import decimal

from django import forms
from flanker.addresslib import address

from . import models
from . import utils


WISHLIST_ID_REGEX = re.compile('^[0-9A-Z]{10,15}$')


class _BaseForm(object):
    def clean(self):
        cleaned_data = super(_BaseForm, self).clean()
        for field in cleaned_data:
            if isinstance(cleaned_data[field], basestring):
                cleaned_data[field] = (
                    cleaned_data[field].replace('\r\n', '\n')
                    .replace(u'\u2018', "'").replace(u'\u2019', "'").strip())

        return cleaned_data


class BaseModelForm(_BaseForm, forms.ModelForm):
    pass


class BaseForm(_BaseForm, forms.Form):
    pass


class WishlistIDForm(BaseForm):

    amazon_id = forms.CharField()

    def clean_amazon_id(self):
        value = self.cleaned_data['amazon_id']
        print "VALUE", repr(value)
        if '://' in value:
            value = utils.find_wishlist_amazon_id(value)
            if not value:
                raise forms.ValidationError("Doesn't look like a valid Wish List ID")

        if not WISHLIST_ID_REGEX.match(value):
            raise forms.ValidationError("Doesn't look like a valid Wish List ID")

        return value


class PaymentForm(BaseForm):
    uri = forms.CharField()
    amount = forms.CharField()
    hash = forms.CharField(required=False)
    id = forms.CharField(required=False)
    email = forms.EmailField()

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
            raise forms.ValidationError('Minimum is $0.50')
        left = self.item.amount_remaining
        if value > left:
            raise forms.ValidationError('Too much. Only $%.2f left to contribute.' % left)
        return value


class YourNameForm(BaseForm):
    your_email = forms.EmailField()
    your_name = forms.CharField()


class TakenForm(BaseForm):
    email = forms.EmailField()

    def __init__(self, *args, **kwargs):
        self.wishlist = kwargs.pop('wishlist')
        super(TakenForm, self).__init__(*args, **kwargs)

    def clean_email(self):
        value = self.cleaned_data['email']
        if value.lower().strip() != self.wishlist.email.lower().strip():
            raise forms.ValidationError('Not the same email address')
        return value


class WishlistAdminForm(BaseModelForm):

    class Meta:
        model = models.Wishlist
        fields = ('name', 'public')


class ShareByEmailForm(BaseForm):

    emails = forms.CharField()
    send_copy = forms.BooleanField(required=False)

    def clean_emails(self):
        value = self.cleaned_data['emails']
        value = value.replace('\n', ',').replace(';', ',')
        #print "INPUT"
        #print repr(value)
        emails = address.parse_list(value)
        #print "OUTPUT"
        #print emails
        return emails
