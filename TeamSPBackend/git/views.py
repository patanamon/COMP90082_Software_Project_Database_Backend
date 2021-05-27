from django.shortcuts import render

# Create your views here.
from collections import defaultdict
from TeamSPBackend.git.models import StudentCommitCounts, GitCommitCounts, GitMetrics
from TeamSPBackend.common import utils
from TeamSPBackend.common.github_util import get_commits, get_und_metrics
from TeamSPBackend.api.dto.dto import GitDTO
from TeamSPBackend.common.choices import RespCode
from TeamSPBackend.common.utils import make_json_response, check_user_login, body_extract, check_body, \
    init_http_response_my_enum
from TeamSPBackend.project.models import ProjectCoordinatorRelation
import time, datetime
from TeamSPBackend.common.utils import transformTimestamp


def update_individual_commits():
    for relation in ProjectCoordinatorRelation.objects.all():
        data = {
            "url": relation.git_url
        }
        # create GitDTO object
        git_dto = GitDTO()
        # extract body information and store them in GitDTO.
        body_extract(data, git_dto)

        if not git_dto.valid_url:
            resp = init_http_response_my_enum(RespCode.invalid_parameter)
            return make_json_response(resp=resp)
        git_dto.url = git_dto.url.lstrip('$')

        # request commits from  github api
        commits = get_commits(git_dto.url, relation.space_key, git_dto.author, git_dto.branch, git_dto.second_after,
                              git_dto.second_before)
        # commits = get_commits(git_dto.url, git_dto.author, git_dto.branch, git_dto.second_after, git_dto.second_before)
        if commits is None:
            resp = init_http_response_my_enum(RespCode.invalid_authentication)
            return make_json_response(resp=resp)
        if commits == -1:
            resp = init_http_response_my_enum(RespCode.user_not_found)
            return make_json_response(resp=resp)
        if commits == -2:
            resp = init_http_response_my_enum(RespCode.git_config_not_found)
            return make_json_response(resp=resp)
        CommitCount = defaultdict(lambda: 0)
        for commit in commits:
            CommitCount[commit['author']] += 1

        for key, value in CommitCount.items():

            if StudentCommitCounts.objects.filter(student_name=str(key)).exists():
                user = StudentCommitCounts.objects.get(student_name=str(key))
                if str(value) != user.commit_counts:
                    StudentCommitCounts.objects.filter(student_name=str(key)).update(commit_counts=str(value))
            else:
                user = StudentCommitCounts(student_name=str(key), commit_counts=str(value),
                                           space_key=relation.space_key)
                user.save()


"""
Auto update git commits per day. 
And it's necessary to consider 3 cases:
1. Git_commit db has this space_key, so just update a new day data
2. It doesn't have, crawler data and sorted by date
3. Server crash, and in order to avoid duplication, don't do commit_query
"""


def auto_update_commits(space_key):
    today = transformTimestamp(time.time())
    # print("space_key is: "+str(space_key))
    # if space_key not None means user update their configuration, and it will update database at once
    if space_key is not None:
        if not GitCommitCounts.objects.filter(space_key=space_key).exists():
            if ProjectCoordinatorRelation.objects.filter(space_key=space_key).exclude(git_url__isnull=True).exists():
                relation = ProjectCoordinatorRelation.objects.filter(space_key=space_key).exclude(git_url__isnull=True)[0]
                git_dto = construct_url(relation)
                if not git_dto.valid_url:
                    return
                commits = get_commits(git_dto.url, space_key, git_dto.author, git_dto.branch, git_dto.second_after,
                                      git_dto.second_before)
                first_crawler(commits, space_key)

    for relation in ProjectCoordinatorRelation.objects.all():
        space_key = relation.space_key
        # Case 3: avoid duplications
        if GitCommitCounts.objects.filter(space_key=space_key, query_date=today).exists():
            continue
        # construct dto
        git_dto = construct_url(relation)
        # not a valid url, continue
        if not git_dto.valid_url:
            continue
        commits = get_commits(git_dto.url, space_key, git_dto.author, git_dto.branch, git_dto.second_after,
                              git_dto.second_before)
        # exception handler
        if commits is None or commits == -1 or commits == -2:
            continue

        # Case 1: has space_key
        if GitCommitCounts.objects.filter(space_key=space_key).exists():
            count = len(commits)

            git_data = GitCommitCounts(
                space_key=space_key,
                commit_counts=count,
                query_date=today
            )
            git_data.save()

        # Case 2: the first crawler
        else:
            first_crawler(commits, space_key)


def construct_url(relation):
    data = {
        "url": relation.git_url
    }
    git_dto = GitDTO()
    body_extract(data, git_dto)
    git_dto.url = git_dto.url.lstrip('$')
    return git_dto


def first_crawler(commits, space_key):
    delta_commit_count = {}  # To store every day commit count
    days = []  # For a month loop
    today = transformTimestamp(time.time())
    for i in range(30):
        days.append(today - i * 24 * 60 * 60)

    for commit in commits:
        ts = commit['date']
        for i in days:
            if ts > i:
                break
            else:
                if i in delta_commit_count:
                    delta_commit_count[i] += 1
                else:
                    delta_commit_count[i] = 1

    days = [i for i in reversed(days)]  # sort low to high
    for day in days:
        count = 0
        if day in delta_commit_count:
            count = delta_commit_count[day]
        # data which are returned to front end
        tmp = {
            "time": int(day),
            "commit_count": int(count)
        }
        # store data into db by date
        git_data = GitCommitCounts(
            space_key=space_key,
            commit_counts=count,
            query_date=day
        )
        git_data.save()


def get_metrics(relation):
    data = {
        "url": relation.git_url
    }
    # create GitDTO object
    git_dto = GitDTO()
    # extract body information and store them in GitDTO.
    body_extract(data, git_dto)
    if not git_dto.valid_url:
        resp = init_http_response_my_enum(RespCode.no_repository)
        return make_json_response(resp=resp)
    git_dto.url = git_dto.url.lstrip('$')

    metrics = get_und_metrics(git_dto.url, relation.space_key)
    if metrics is None:
        resp = init_http_response_my_enum(RespCode.invalid_authentication)
        return make_json_response(resp=resp)
    elif metrics == -1:
        resp = init_http_response_my_enum(RespCode.user_not_found)
        return make_json_response(resp=resp)
    elif metrics == -2:
        resp = init_http_response_my_enum(RespCode.git_config_not_found)
        return make_json_response(resp=resp)

    if GitMetrics.objects.filter(space_key=relation.space_key).exists():
        GitMetrics.objects.filter(space_key=relation.space_key).update(
            file_count=metrics['CountDeclFile'],
            class_count=metrics['CountDeclClass'],
            function_count=metrics['CountDeclFunction'],
            code_lines_count=metrics['CountLineCode'],
            declarative_lines_count=metrics['CountLineCodeDecl'],
            executable_lines_count=metrics['CountLineCodeExe'],
            comment_lines_count=metrics['CountLineComment'],
            comment_to_code_ratio=metrics['RatioCommentToCode'],
        )
    else:
        metrics_dto = GitMetrics(
            space_key=relation.space_key,
            file_count=metrics['CountDeclFile'],
            class_count=metrics['CountDeclClass'],
            function_count=metrics['CountDeclFunction'],
            code_lines_count=metrics['CountLineCode'],
            declarative_lines_count=metrics['CountLineCodeDecl'],
            executable_lines_count=metrics['CountLineCodeExe'],
            comment_lines_count=metrics['CountLineComment'],
            comment_to_code_ratio=metrics['RatioCommentToCode'],
        )
        metrics_dto.save()


def auto_update_metrics():
    for relation in ProjectCoordinatorRelation.objects.all():
        get_metrics(relation)


utils.start_schedule(auto_update_commits, 60 * 60 * 24, None)
utils.start_schedule(update_individual_commits, 60 * 60 * 24)
# utils.start_schedule(auto_update_metrics, 60 * 60 * 24)
