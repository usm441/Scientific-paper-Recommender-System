# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-04-29 18:41
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GUIManager', '0008_paperldatheta_doc_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='ratingmatrix',
            name='doc_id',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='ratingmatrix',
            name='external_user_id',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]
