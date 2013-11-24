import re
import os
import datetime
import decimal
import hashlib
import functools
import unicodedata
import json
import uuid
from decimal import Decimal, ROUND_UP

from django import http
from django.utils.timezone import utc
from django.contrib.sites.models import RequestSite


def full_absolute_url(request, url):
    try:
        if url.startswith('//'):
            # just need the protocol
            protocol = 'https' if request.is_secure() else 'http'
            url = '%s:%s' % (protocol, url)
        elif url.startswith('/'):
            # need protocol and domain
            protocol = 'https' if request.is_secure() else 'http'
            domain = RequestSite(request).domain
            url = '%s://%s%s' % (protocol, domain, url)
    except Exception:
        import sys
        print sys.exc_info()
    finally:
        return url


def identifier_maker(length):
    def maker():
        return uuid.uuid4().hex[:length]
    return maker


def now():
    return datetime.datetime.utcnow().replace(tzinfo=utc)


def upload_path(tag):
    def _upload_path_tagged(instance, filename):
        if isinstance(filename, unicode):
            filename = (
                unicodedata
                .normalize('NFD', filename)
                .encode('ascii', 'ignore')
            )
        _now = now()
        path = os.path.join(
            #"%05d" % instance.wishlist,
            _now.strftime('%Y'),
            _now.strftime('%m'),
            _now.strftime('%d')
        )
        hashed_filename = (hashlib.md5(filename +
                           str(now().microsecond)).hexdigest())
        __, extension = os.path.splitext(filename)
        return os.path.join(tag, path, hashed_filename + extension)
    return _upload_path_tagged


class PracticalJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return json.JSONEncoder.default(self, obj)


def json_view(f):
    @functools.wraps(f)
    def wrapper(request, *args, **kw):
        response = f(request, *args, **kw)
        if not isinstance(response, http.HttpResponse):
            response = json_response(response)
        return response
    return wrapper


def json_response(data, indent=0):
    return http.HttpResponse(
                _json_clean(json.dumps(
                    data,
                    cls=PracticalJSONEncoder,
                    indent=indent
                )),
                content_type='application/json; charset=UTF-8'
            )


def _json_clean(value):
    """JSON-encodes the given Python object."""
    # JSON permits but does not require forward slashes to be escaped.
    # This is useful when json data is emitted in a <script> tag
    # in HTML, as it prevents </script> tags from prematurely terminating
    # the javscript.  Some json libraries do this escaping by default,
    # although python's standard library does not, so we do it here.
    # http://stackoverflow.com/questions/1580647/json-why-are-forward-slashe\
    # s-escaped
    return value.replace("</", "<\\/")


def obfuscate_email(email):
    return re.sub('(\w{3})@(\w{3})', '...@...', email)


def mkdir(newdir):
    """works the way a good mkdir should :)
        - already exists, silently complete
        - regular file in the way, raise an exception
        - parent directory(ies) does not exist, make them as well
    """
    if os.path.isdir(newdir):
        return
    if os.path.isfile(newdir):
        raise OSError("a file with the same name as the desired "
                      "dir, '%s', already exists." % newdir)
    head, tail = os.path.split(newdir)
    if head and not os.path.isdir(head):
        mkdir(head)
    if tail:
        os.mkdir(newdir)


# https://github.com/facebook/tornado/blob/master/tornado/escape.py
_URL_RE = re.compile(r"""\b((?:([\w-]+):(/{1,3})|www[.])(?:(?:(?:[^\s&()]|&amp;|&quot;)*(?:[^!"#$%&'()*+,.:;<=>?@\[\]^`{|}~\s]))|(?:\((?:[^\s&()]|&amp;|&quot;)*\)))+)""")

def find_urls(text):
    return list(set([x[0] for x in _URL_RE.findall(text)]))

_WISHLIST_URL_ID_REGEX = re.compile('/([0-9A-Z]{10,15})/?')

def find_wishlist_amazon_id(text):
    for identifier in _WISHLIST_URL_ID_REGEX.findall(text):
        return identifier


def to_decimal(number):
    number = Decimal(number)
    return number.quantize(Decimal('.01'), rounding=ROUND_UP)
