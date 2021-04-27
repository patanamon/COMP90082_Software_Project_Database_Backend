# -*- coding: utf-8 -*-
from collections import defaultdict
import logging, time

from django.views.decorators.http import require_http_methods

from TeamSPBackend.common.github_util import get_commits, get_pull_request
from TeamSPBackend.api.dto.dto import GitDTO
from TeamSPBackend.common.choices import RespCode
from TeamSPBackend.common.utils import make_json_response, check_user_login, body_extract, mills_timestamp, check_body, init_http_response_my_enum, transformTimestamp
from TeamSPBackend.git.models import StudentCommitCounts, GitCommitCounts
logger = logging.getLogger('django')

@require_http_methods(['POST'])
@check_user_login()
@check_body
def get_git_individual_commits(request, body, *args, **kwargs):
    # create GitDTO object
    git_dto = GitDTO()
    # extract body information and store them in GitDTO.
    body_extract(body, git_dto)

    if not git_dto.valid_url:
        resp = init_http_response_my_enum(RespCode.invalid_parameter)
        return make_json_response(resp=resp)
    git_dto.url = git_dto.url.lstrip('$')

    # request commits from  github api
    commits = get_commits(git_dto.url, git_dto.author, git_dto.branch, git_dto.second_after, git_dto.second_before)
    CommitCount = defaultdict(lambda: 0)
    for commit in commits:
        CommitCount[commit['author']] += 1
    commit_count = [i for i in CommitCount.values()]
    student = [i for i in CommitCount.keys()]
    data=[]
    # data = {
    #     "student": student,
    #     "commit_count": commit_count
    # }
    for key,value in CommitCount.items():
        temp={
            "student":key,
            "commit_count":value
        }
        if StudentCommitCounts.objects.filter(student_name=key).exists():
            user = StudentCommitCounts.objects.get(student_name=key)
            if value!=user.commit_count:
                StudentCommitCounts.objects.filter(student_name=key).update(commit_counts=value)
        else:
            user=StudentCommitCounts(student_name=key,commit_counts=value)
            user.save()

        data.append(temp)



    resp = init_http_response_my_enum(RespCode.success, data)
    return make_json_response(resp=resp)

@require_http_methods(['POST'])
@check_user_login()
@check_body
def get_git_commits(request, body, *args, **kwargs):
    # body is a dict and use body_extract to construct git_dao which includes url, branch, author, before and after(time)
    git_dto = GitDTO()
    body_extract(body, git_dto)

    if not git_dto.valid_url:
        resp = init_http_response_my_enum(RespCode.invalid_parameter)
        return make_json_response(resp=resp)
    git_dto.url = git_dto.url.lstrip('$')

    before = transformTimestamp(git_dto.second_before)
    after = transformTimestamp(git_dto.second_after)


    if GitCommitCounts.objects.filter(space_key=git_dto.url, query_date=before).exists()\
            and GitCommitCounts.objects.filter(space_key=git_dto.url, query_date=after).exists():
        count_after = GitCommitCounts.objects.get(space_key=git_dto.url, query_date=after).commit_counts
        count_before = GitCommitCounts.objects.get(space_key=git_dto.url, query_date=before).commit_counts
        # res = {'space_key': git_dto.url, 'commit_count': count_after - count_before, 'date_from':before, 'date_to': after}
        data = dict(
            space_key=git_dto.url,
            commit_count=count_after - count_before,
            date_from=before,
            date_to=after
        )
        resp = init_http_response_my_enum(RespCode.success, data)
        return make_json_response(resp=resp)

    commits = get_commits(git_dto.url, git_dto.author, git_dto.branch, time.localtime(), 1)
    total = len(commits)
    relation_id = 1
    info = GitCommitCounts(relation_id=relation_id,
                           space_key=git_dto.url,
                           commit_counts=total,
                           query_date=transformTimestamp(time.localtime()))
    info.save()

    data = dict(
        space_key=git_dto.url,
        commit_count=total,
        date_from=before,
        date_to=after
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
