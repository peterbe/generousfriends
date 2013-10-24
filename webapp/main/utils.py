import re
import os
import datetime
import decimal
import hashlib
import functools
import unicodedata
import json

from django import http
from django.utils.timezone import utc


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
