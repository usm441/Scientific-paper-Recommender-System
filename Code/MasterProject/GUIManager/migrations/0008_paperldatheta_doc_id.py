# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2018-04-29 14:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('GUIManager', '0007_systemalgorithmrecommendationlog'),
    ]

    operations = [
        migrations.AddField(
            model_name='paperldatheta',
            name='doc_id',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]