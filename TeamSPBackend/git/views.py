from django.shortcuts import render

# Create your views here.
from collections import defaultdict
from TeamSPBackend.git.models import StudentCommitCounts
from TeamSPBackend.common import utils
from TeamSPBackend.common.github_util import get_commits, get_pull_request
from TeamSPBackend.api.dto.dto import GitDTO
from TeamSPBackend.common.choices import RespCode
from TeamSPBackend.common.utils import make_json_response, check_user_login, body_extract, mills_timestamp, check_body, init_http_response_my_enum

def update_individual_commits(request, body, *args, **kwargs):
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
        data.append(temp)

