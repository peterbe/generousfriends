# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Payment.receipt_emailed'
        db.add_column(u'main_payment', 'receipt_emailed',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)

        # Adding field 'Payment.notification_emailed'
        db.add_column(u'main_payment', 'notification_emailed',
                      self.gf('django.db.models.fields.DateTimeField')(null=True),
                      keep_default=False)

        for payment in orm['main.Payment'].objects.all():
            payment.receipt_emailed = payment.modified
            payment.notification_emailed = payment.modified
            payment.save()


    def backwards(self, orm):
        # Deleting field 'Payment.receipt_emailed'
        db.delete_column(u'main_payment', 'receipt_emailed')

        # Deleting field 'Payment.notification_emailed'
        db.delete_column(u'main_payment', 'notification_emailed')


    models = {
        u'main.item': {
            'Meta': {'object_name': 'Item'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 8, 0, 0)'}),
            'affiliates_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "'29bcbcba'", 'max_length': '8'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 8, 0, 0)'}),
            'picture': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100'}),
            'preference': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'price': ('django.db.models.fields.DecimalField', [], {'max_digits': '5', 'decimal_places': '2'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200'}),
            'wishlist': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Wishlist']"})
        },
        u'main.payment': {
            'Meta': {'object_name': 'Payment'},
            'actual_amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '5', 'decimal_places': '2'}),
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 8, 0, 0)'}),
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '5', 'decimal_places': '2'}),
            'balanced_hash': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'balanced_id': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True'}),
            'hide_amount': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hide_message': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hide_name': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Item']"}),
            'message': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 8, 0, 0)'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'notification_emailed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'receipt_emailed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'wishlist': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Wishlist']"})
        },
        u'main.verification': {
            'Meta': {'object_name': 'Verification'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 8, 0, 0)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "'83bf5f7b04d2444e'", 'max_length': '16'}),
            'wishlist': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Wishlist']"})
        },
        u'main.wishlist': {
            'Meta': {'object_name': 'Wishlist'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 8, 0, 0)'}),
            'address': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'amazon_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "'8ccc3be1'", 'max_length': '8'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 8, 0, 0)'}),
            'mugshot': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'verified': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        }
    }

    complete_apps = ['main']
