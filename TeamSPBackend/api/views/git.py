# -*- coding: utf-8 -*-

import logging
import ujson

from django.views.decorators.http import require_http_methods

from TeamSPBackend.common.github_util import get_commits, get_pull_request
from TeamSPBackend.api.dto.dto import GitDTO
from TeamSPBackend.common.choices import RespCode
from TeamSPBackend.common.utils import make_json_response, check_user_login, body_extract, mills_timestamp, check_body, init_http_response_my_enum

logger = logging.getLogger('django')

@require_http_methods(['POST'])
@check_user_login()
@check_body
def get_git_commits(request, body, *args, **kwargs):
    git_dto = GitDTO()
    body_extract(body, git_dto)

    if not git_dto.valid_url:
        resp = init_http_response_my_enum(RespCode.invalid_parameter)
        return make_json_response(resp=resp)
    git_dto.url = git_dto.url.lstrip('$')

    commits = get_commits(git_dto.url, git_dto.author, git_dto.branch, git_dto.second_after, git_dto.second_before)
    total = len(commits)
    author = set()
    file_changed = 0
    insertion = 0
    deletion = 0
    # 感觉这个没必要啊，file_change什么的，有点蠢，因为重复率太高了
    for commit in commits:
        file_changed += commit['file_changed']
        insertion += commit['insertion']
        deletion += commit['deletion']
        author.add(commit['author'])

    data = dict(
        total=total,
        author=list(author),
        file_changed=file_changed,
        insertion=insertion,
        deletion=deletion,
        commits=commits,
    )
    resp = init_http_response_my_enum(RespCode.success, data)
    return make_json_response(resp=resp)

# pull request
@require_http_methods(['POST'])
@check_user_login()
@check_body
def get_git_pr(request, body, *args, **kwargs):
    git_dto = GitDTO()
    body_extract(body, git_dto)

    if not git_dto.valid_url:
        resp = init_http_response_my_enum(RespCode.invalid_parameter)
        return make_json_response(resp=resp)
    git_dto.url = git_dto.url.lstrip('$')

    commits = get_pull_request(git_dto.url, git_dto.author, git_dto.branch, git_dto.second_after, git_dto.second_before)
    total = len(commits)
    author = set()
    for commit in commits:
        author.add(commit['author'])
    # 个人感觉这里做一个合并，变成字典：{author1: [commits...], author2: [cmits...], ...}
    data = dict(
        total=total,
        author=list(author),
        commits=commits,
    )
    resp = init_http_response_my_enum(RespCode.success, data)
    return make_json_response(resp=resp)
