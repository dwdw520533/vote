# -*- coding=utf-8 -*-
from vote.models import VoteTheme

vote_theme = [
    {
        "code": "1",
        "title": "投票主题1",
        "content": "投票内容1"
    },
    {
        "code": "2",
        "title": "投票主题2",
        "content": "投票内容2"
    },
    {
        "code": "3",
        "title": "投票主题3",
        "content": "投票内容3"
    }
]


for vote in vote_theme:
    VoteTheme.objects.create(**vote)
