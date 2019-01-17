# -*- coding:utf-8 -*-
"""
Models for users related apis.
"""
import datetime
from django.db import models


class VoteTheme(models.Model):
    class Meta:
        db_table = 'vote_theme'

    code = models.CharField(max_length=8, unique=True)
    title = models.CharField(max_length=128)
    content = models.CharField(max_length=512)
    count = models.IntegerField(default=0)
    icon = models.CharField(max_length=512)
    created = models.DateTimeField(default=datetime.datetime.now)
    lut = models.DateTimeField(default=datetime.datetime.now)

    @property
    def to_dict(self):
        return {
            "code": self.code,
            "title": self.title,
            "content": self.content,
            "count": self.count,
            "icon": self.icon
        }


class VoteRecord(models.Model):
    class Meta:
        db_table = 'vote_record'

    user_id = models.CharField(max_length=8)
    code = models.CharField(max_length=128)
    created = models.DateTimeField(default=datetime.datetime.now)
    lut = models.DateTimeField(default=datetime.datetime.now)
