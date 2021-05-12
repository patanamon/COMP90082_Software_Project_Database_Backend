# -*- coding: utf-8 -*-
from collections import defaultdict
import logging
from django.views.decorators.http import require_http_methods
from TeamSPBackend.git.views import update_individual_commits
from TeamSPBackend.common.github_util import get_commits, get_pull_request
from TeamSPBackend.api.dto.dto import GitDTO
from TeamSPBackend.common.choices import RespCode
from TeamSPBackend.common.utils import make_json_response, body_extract, init_http_response_my_enum, transformTimestamp
from TeamSPBackend.git.models import StudentCommitCounts, GitCommitCounts
from TeamSPBackend.project.models import ProjectCoordinatorRelation

logger = logging.getLogger('django')


@require_http_methods(['GET'])
def get_git_individual_commits(request, space_key):
    data = []
    if StudentCommitCounts.objects.filter(space_key=space_key).exists():
        for item in StudentCommitCounts.objects.filter(space_key=space_key):
            temp = {
                "student": str(item.student_name),
                "commit_count": int(item.commit_counts)
            }
            data.append(temp)
    else:
        if ProjectCoordinatorRelation.objects.filter(space_key=space_key).exists():
            update_individual_commits()
            temp={}
            for item in StudentCommitCounts.objects.filter(space_key=space_key):
                temp = {
                    "student": str(item.student_name),
                    "commit_count": int(item.commit_counts)
                }
            data.append(temp)
        else:
            resp = init_http_response_my_enum(RespCode.invalid_parameter)
            return make_json_response(resp=resp)

    resp = init_http_response_my_enum(RespCode.success, data)
    return make_json_response(resp=resp)


@require_http_methods(['GET'])
def get_git_commits(request, space_key):
    # Case 1: if git_commit table contains this space_key, get it directly from db
    data = []
    if GitCommitCounts.objects.filter(space_key=space_key).exists():
        for i in GitCommitCounts.objects.filter(space_key=space_key):
            tmp = {
                "commit_count": str(i.commit_counts),
                "date": str(i.query_date)
            }
            data.append(tmp)
    else:
        # Case 2: if git_commit table doesn't contain while relation table contains, get it from git web (the first crawler)
        if ProjectCoordinatorRelation.objects.filter(space_key=space_key).exists():
            relation_data = ProjectCoordinatorRelation.objects.filter(space_key=space_key)
            commits = get_commits(relation_data[0].git_url, None, None, None, None)
            delta_commit_count = {}  # To store every day commit count
            days = []  # For loop

            for i in commits:
                ts = transformTimestamp(i['date'])
                if ts in delta_commit_count:
                    delta_commit_count[ts] += 1
                else:
                    delta_commit_count[ts] = 1
                    days.append(ts)

            for day in days:
                count = 0
                for k, v in delta_commit_count.items():
                    if k <= day:
                        count += v
                # data which are returned to front end
                tmp = {
                    "commit_count": str(count),
                    "date": str(day)
                }
                data.append(tmp)
                # store data into db by date
                git_data = GitCommitCounts(
                    space_key=space_key,
                    commit_counts=count,
                    query_date=day
                )
                git_data.save()

        # Case 3: Neither contains, invalid space_key, return None
        else:
            resp = init_http_response_my_enum(RespCode.invalid_parameter)
            return make_json_response(resp=resp)

    resp = init_http_response_my_enum(RespCode.success, data)
    return make_json_response(resp=resp)


# pull request
@require_http_methods(['POST'])
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
