import urlparse
import time
import stat
import os
import hashlib
import decimal
from cStringIO import StringIO

from PIL import Image
from pyquery import PyQuery
import requests


class NotFoundError(Exception):
    pass

def _download(url, cache_seconds=3600 * 20):
    key = hashlib.md5(url).hexdigest()

    if '.' in url and len(url.split('.')[-1]) < 5:
        key += '.%s' % url.split('.')[-1]
    else:
        key += '.html'
    cache_file = os.path.join('.cache', key[:2], key[2:4], key[4:])
    if os.path.isfile(cache_file):
        age = time.time() - os.stat(cache_file)[stat.ST_MTIME]
        if age < cache_seconds:
            return open(cache_file).read()
        os.remove(cache_file)

    print "CACHE MISS", url
    response = requests.get(url)
    if response.status_code < 200 or response.status_code >= 400:
        # treat 500 errors differently?
        raise NotFoundError(response.status_code)
    html = response.content
    if not os.path.isdir('.cache'):
        os.mkdir('.cache')
    dirname = os.path.dirname(cache_file)
    os.makedirs(dirname)
    with open(cache_file, 'w') as f:
        f.write(html)
    return html


def _parse_price(price):
    try:
        return decimal.Decimal(price.replace('$', ''))
    except decimal.InvalidOperation:
        pass


def scrape(wishlistid):
    url = 'http://www.amazon.com/registry/wishlist/%s?layout=compact' % wishlistid
    html = _download(url)
    #print len(html)
    doc = PyQuery(html)
    items = []
    name = None
    for profile_elem in doc('.profile-layout-aid-top'):
        for name_elem in doc('.stable', profile_elem):
            print repr(name_elem.text.strip())

    for row_elem in doc('table.g-compact-items tr'):
        price = None
        for price_elem in doc('td.g-price span', row_elem):
            price = _parse_price(price_elem.text.strip())
        if price is None:
            continue

        for elem in doc('td.g-title a', row_elem):

            text = elem.text.strip()
            print text

            item_url = urlparse.urljoin('http://www.amazon.com', elem.attrib['href'])
            item = {
                'text': text,
                'url': item_url,
                'price': price
            }
            item_html = _download(item_url)
            item_doc = PyQuery(item_html)
            item_image_url = None
            _checked = set()
            for img in item_doc('#main-image-container img,#main-image-content img'):
                image_url = img.attrib['src']
                if image_url in _checked:
                    continue
                _checked.add(image_url)
                content = _download(image_url)
                if content:
                    f = StringIO(content)
                    img = Image.open(f)
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
    return {'items': items, 'name': name}


if __name__ == '__main__':
    import sys
    if not sys.argv[1:]:
        sys.exit(1)
    else:
        items = scrape(sys.argv[1])
        from pprint import pprint
        pprint(items)