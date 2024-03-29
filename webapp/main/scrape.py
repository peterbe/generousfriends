import time
import codecs
import urlparse
import time
import stat
import os
import hashlib
import decimal
from cStringIO import StringIO

from django.conf import settings
from PIL import Image
from pyquery import PyQuery
import requests

from webapp.main.utils import mkdir


def root_dir():
    _CACHE_DIR = getattr(settings, 'CACHE_DIR', settings.MEDIA_ROOT)
    return os.path.join(_CACHE_DIR, '.scrape-cache')


class NotFoundError(Exception):
    pass


def _download(url, cache_seconds=3600 * 1, binary=False, force_refresh=False):
    key = hashlib.md5(url).hexdigest()

    if '.' in url and len(url.split('.')[-1]) < 5:
        key += '.%s' % url.split('.')[-1]
    else:
        key += '.html'
    cache_file = os.path.join(
        root_dir(),
        key[:2], key[2:4], key[4:]
    )
    if not force_refresh and os.path.isfile(cache_file):
        age = time.time() - os.stat(cache_file)[stat.ST_MTIME]
        if age < cache_seconds:
            if binary:
                opener = lambda x: open(x).read()
            else:
                opener = lambda x: codecs.open(x, 'r', 'utf-8').read()
            try:
                return opener(cache_file)
            except UnicodeDecodeError:
                pass
        os.remove(cache_file)

    print "CACHE MISS", url
    response = requests.get(url)
    if response.status_code < 200 or response.status_code >= 400:
        # treat 500 errors differently?
        raise NotFoundError(response.status_code)
    if binary:
        content = response.content
    else:
        content = response.text
    if not os.path.isdir(root_dir()):
        mkdir(root_dir())
    dirname = os.path.dirname(cache_file)
    mkdir(dirname)
    if binary:
        writer = lambda x: open(x, 'wb')
    else:
        writer = lambda x: codecs.open(x, 'w', 'utf-8')
    with writer(cache_file) as f:
        f.write(content)
    return content


def _parse_price(price):
    try:
        return decimal.Decimal(price.replace('$', ''))
    except decimal.InvalidOperation:
        pass


def scrape(wishlistid, shallow=False, force_refresh=False, cache_seconds=3600 * 1):
    """
    if @shallow don't bother downloading the images
    """
    url = 'http://www.amazon.com/registry/wishlist/%s?layout=compact' % wishlistid
    html = _download(
        url,
        force_refresh=force_refresh,
        cache_seconds=cache_seconds,
    )
    doc = PyQuery(html)
    items = []
    externals = []
    name = None
    ship_to = None

    for profile_elem in doc('.profile-layout-aid-top'):
        _next_is_ship_to = False
        for name_elem in doc('span', profile_elem):
            if _next_is_ship_to:
                ship_to = name_elem.text.strip()
            elif name_elem.text.strip() == 'Ship-to:':
                _next_is_ship_to = True
            #print "\t",repr(name_elem.text.strip())

    for row_elem in doc('table.g-compact-items tr, table.compact-items tr'):
        price = None
        for price_elem in doc('td.g-price span, td .price strong', row_elem):
            price = _parse_price(price_elem.text.strip())
        if price is None:
            continue

        for elem in doc('td.g-title a, .productTitle a', row_elem):

            text = elem.text.strip()
            #print repr(text)

            item_url = urlparse.urljoin('http://www.amazon.com', elem.attrib['href'])
            item = {
                'text': text,
                'url': item_url,
                'price': price
            }
            if not item_url.startswith('http://www.amazon.com'):
                print "\tSKIPPING", item_url
                externals.append(item)
                continue
            item_html = _download(item_url)
            item_doc = PyQuery(item_html)
            item_image_url = None
            _checked = set()
            if not shallow:
                for img in item_doc('#main-image-container img,#main-image-content img'):
                    image_url = img.attrib['src']
                    if image_url in _checked:
                        continue
                    _checked.add(image_url)
                    content = _download(image_url, binary=True)
                    if content:
                        f = StringIO(content)
                        try:
                            img = Image.open(f)
                        except IOError:
                            print "Was unable to open (as image)", image_url
                            continue
                        width, __ = img.size
                        if width <= 40:
                            # thumbnail
                            continue
                        #print "\t", image_url
                        #print "\t", img.size
                        item['picture'] = {
                            'url': image_url,
                            'size': img.size
                        }
            items.append(item)
    return {
        'items': items,
        'name': name,
        'externals': externals,
        'ship_to': ship_to,
    }


def clean_cache(min_days):
    now = time.time()
    min_seconds = min_days * 24  * 3600
    for root, dirs, files in os.walk(root_dir()):
        for f in files:
            fp = os.path.join(root, f)
            mtime = os.stat(fp)[stat.ST_MTIME]
            age = now - mtime
            if age > min_seconds:
                print "DELETE FILE", fp
                os.remove(fp)
        for dir_ in dirs:
            dirp = os.path.join(root, dir_)
            if not os.listdir(dirp):
                print "DELETE DIR", dirp
                os.rmdir(dirp)

if __name__ == '__main__':
    import sys
    if not sys.argv[1:]:
        sys.exit(1)
    else:
        items = scrape(sys.argv[1])
        from pprint import pprint
        pprint(items)
