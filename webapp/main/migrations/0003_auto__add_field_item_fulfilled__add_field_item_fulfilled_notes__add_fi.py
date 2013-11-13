# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'Item.fulfilled'
        db.add_column(u'main_item', 'fulfilled',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'Item.fulfilled_notes'
        db.add_column(u'main_item', 'fulfilled_notes',
                      self.gf('django.db.models.fields.TextField')(null=True),
                      keep_default=False)

        # Adding field 'Wishlist.public'
        db.add_column(u'main_wishlist', 'public',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'Item.fulfilled'
        db.delete_column(u'main_item', 'fulfilled')

        # Deleting field 'Item.fulfilled_notes'
        db.delete_column(u'main_item', 'fulfilled_notes')

        # Deleting field 'Wishlist.public'
        db.delete_column(u'main_wishlist', 'public')


    models = {
        u'main.item': {
            'Meta': {'object_name': 'Item'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 11, 0, 0)'}),
            'affiliates_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            'fulfilled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'fulfilled_notes': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "'1c192c9c'", 'max_length': '8'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 11, 0, 0)'}),
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
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 11, 0, 0)'}),
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
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 11, 0, 0)'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True'}),
            'notification_emailed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'receipt_emailed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'wishlist': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Wishlist']"})
        },
        u'main.verification': {
            'Meta': {'object_name': 'Verification'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 11, 0, 0)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "'d54b5e381f8f40c1'", 'max_length': '16'}),
            'wishlist': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Wishlist']"})
        },
        u'main.wishlist': {
            'Meta': {'object_name': 'Wishlist'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 11, 0, 0)'}),
            'address': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'amazon_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "'4fc02d44'", 'max_length': '8'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 11, 0, 0)'}),
            'mugshot': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'public': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'verified': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        }
    }

    complete_apps = ['main']