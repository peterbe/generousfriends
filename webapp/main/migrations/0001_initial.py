# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Wishlist'
        db.create_table(u'main_wishlist', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identifier', self.gf('django.db.models.fields.CharField')(default='cf791fb4', max_length=8)),
            ('amazon_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=20, db_index=True)),
            ('verified', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('mugshot', self.gf('sorl.thumbnail.fields.ImageField')(max_length=100)),
            ('address', self.gf('django.db.models.fields.TextField')(null=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 11, 8, 0, 0))),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 11, 8, 0, 0))),
        ))
        db.send_create_signal(u'main', ['Wishlist'])

        # Adding model 'Item'
        db.create_table(u'main_item', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('identifier', self.gf('django.db.models.fields.CharField')(default='26c92adf', max_length=8)),
            ('wishlist', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Wishlist'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('url', self.gf('django.db.models.fields.URLField')(max_length=200)),
            ('affiliates_url', self.gf('django.db.models.fields.URLField')(max_length=200, null=True)),
            ('price', self.gf('django.db.models.fields.DecimalField')(max_digits=5, decimal_places=2)),
            ('picture', self.gf('sorl.thumbnail.fields.ImageField')(max_length=100)),
            ('preference', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 11, 8, 0, 0))),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 11, 8, 0, 0))),
        ))
        db.send_create_signal(u'main', ['Item'])

        # Adding model 'Payment'
        db.create_table(u'main_payment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('wishlist', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Wishlist'])),
            ('item', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Item'])),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=5, decimal_places=2)),
            ('actual_amount', self.gf('django.db.models.fields.DecimalField')(max_digits=5, decimal_places=2)),
            ('hide_amount', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, null=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True)),
            ('hide_name', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('message', self.gf('django.db.models.fields.TextField')(null=True)),
            ('hide_message', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('balanced_hash', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
            ('balanced_id', self.gf('django.db.models.fields.CharField')(max_length=200, null=True)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 11, 8, 0, 0))),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 11, 8, 0, 0))),
        ))
        db.send_create_signal(u'main', ['Payment'])

        # Adding model 'Verification'
        db.create_table(u'main_verification', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('wishlist', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['main.Wishlist'])),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75)),
            ('identifier', self.gf('django.db.models.fields.CharField')(default='b573e6caf18f4e57', max_length=16)),
            ('added', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2013, 11, 8, 0, 0))),
        ))
        db.send_create_signal(u'main', ['Verification'])


    def backwards(self, orm):
        # Deleting model 'Wishlist'
        db.delete_table(u'main_wishlist')

        # Deleting model 'Item'
        db.delete_table(u'main_item')

        # Deleting model 'Payment'
        db.delete_table(u'main_payment')

        # Deleting model 'Verification'
        db.delete_table(u'main_verification')


    models = {
        u'main.item': {
            'Meta': {'object_name': 'Item'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 8, 0, 0)'}),
            'affiliates_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "'7cff4b82'", 'max_length': '8'}),
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
            'wishlist': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Wishlist']"})
        },
        u'main.verification': {
            'Meta': {'object_name': 'Verification'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 8, 0, 0)'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "'0849bf0fae85442f'", 'max_length': '16'}),
            'wishlist': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['main.Wishlist']"})
        },
        u'main.wishlist': {
            'Meta': {'object_name': 'Wishlist'},
            'added': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 8, 0, 0)'}),
            'address': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'amazon_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '20', 'db_index': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'identifier': ('django.db.models.fields.CharField', [], {'default': "'37234ebf'", 'max_length': '8'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2013, 11, 8, 0, 0)'}),
            'mugshot': ('sorl.thumbnail.fields.ImageField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'verified': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        }
    }

    complete_apps = ['main']