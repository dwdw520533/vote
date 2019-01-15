# -*- coding=utf-8 -*-
import util.status_code as sc
from vote.models import VoteTheme, VoteRecord


def get_user_vote_record(user_id):
    try:
        return VoteRecord.objects.get(user_id=user_id)
    except:
        return None


def get_user_vote_theme(code):
    try:
        return VoteTheme.objects.get(code=code)
    except:
        return None


def query_vote_themes():
    result, records = [], list(VoteTheme.objects.all())
    total_count = sum([i.count for i in records])
    for record in records:
        data = record.to_dict
        try:
            data["rate"] = round(record.count / total_count, 2) * 100
        except ZeroDivisionError:
            data["rate"] = 0
        result.append(data)
    return result


def user_vote(user_id, code):
    record = get_user_vote_record(user_id)
    if record:
        return sc.E_PARAM, '已投票'
    vote_theme = get_user_vote_theme(code)
    if not vote_theme:
        return sc.E_PARAM, '投票主题不存在'
    VoteRecord.objects.create(user_id=user_id, code=code)
    vote_theme.count += 1
    vote_theme.save()
    return sc.E_SUCC, None
