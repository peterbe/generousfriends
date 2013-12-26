import re

from lxml import etree
import amazonproduct


_item_id_regex = re.compile('/dp/(\w{10})')


def url_to_asin(url):
    return _item_id_regex.findall(url)[0]


class ItemNotAccessible(Exception):
    pass


class ItemLookup(object):

    def __init__(self, asins, locale='us'):
        if not isinstance(asins, (tuple, list)):
            asins = [asins]
        self.asins = asins
        self.api = amazonproduct.API(locale=locale)
        self.images = {}
        self.affiliates_urls = {}
        for asins in self._batches():
            #print "ASINS", asins
            res = self._lookup(asins, image=True)
            #print self._debug(res)
            for Items in res.Items:
                for Item in Items.Item:
                    try:
                        self.images[Item.ASIN.text] = Item.LargeImage.URL.text
                    except AttributeError:
                        try:
                            self.images[Item.ASIN.text] = Item.ImageSets.ImageSet.LargeImage.URL.text
                        except AttributeError:
                            print "ASIN", Item.ASIN.text
                            print self._debug(res)
                            raise
                    #print "Y", repr(y), y.tag
            res = self._lookup(asins)
            for Items in res.Items:
                for Item in Items.Item:
                    try:
                        self.affiliates_urls[Item.ASIN.text] = Item.DetailPageURL.text
                    except AttributeError:
                        print self._debug(res)
                        raise
            #print self._debug(res)
            #print
        #from pprint import pprint
        #print "IMAGES"
        #pprint(self.images)
        #print "AFFILIATES_URLS"
        #pprint(self.affiliates_urls)

    def _batches(self):
        for i in range(0, len(self.asins), 10):
            yield self.asins[i : i + 10]

    def _lookup(self, asins, image=False):
        try:
            if image:
                return self.api.item_lookup(*asins, ResponseGroup='Images')
            else:
                return self.api.item_lookup(*asins)
        except amazonproduct.errors.AWSError as err:
            # this is gross but the best I can think of right now
            if 'ItemNotAccessible' in str(err):
                raise ItemNotAccessible(asins)
            raise

    def _debug(self, res):

        return etree.tostring(res, pretty_print=True)
