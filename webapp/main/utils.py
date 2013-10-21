import re
import datetime
import functools
import json

from django import http


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)


def json_view(f):
    @functools.wraps(f)
    def wrapper(request, *args, **kw):
        response = f(request, *args, **kw)
        if isinstance(response, http.HttpResponse):
            return response
        else:
            indent = 0
            if request.REQUEST.get('pretty') == 'print':
                indent = 2
            return json_response(response)
    return wrapper


def json_response(data, indent=0):
    return http.HttpResponse(
                _json_clean(json.dumps(
                    data,
                    cls=DateTimeEncoder,
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
