# -*- coding: utf-8 -*-

import os
import logging
import re

from TeamSPBackend.settings.base_setting import BASE_DIR
from TeamSPBackend.project.models import ProjectCoordinatorRelation

logger = logging.getLogger('django')

GITHUB = 'https://github.com/'
REPO_PATH = BASE_DIR + '/resource/repo/'
COMMIT_DIR = BASE_DIR + '/resource/commit_log'

GIT_CLONE_COMMAND = 'git clone {} {}'
GIT_CHECKOUT_COMMAND = 'git -C {} checkout {}'
GIT_UPDATE_COMMAND = 'git -C {} pull origin HEAD'
GIT_LOG_COMMAND = 'git -C {} log --pretty=format:%H%n%an%n%at%n%s --shortstat --no-merges'
GIT_LOG_PR_COMMAND = 'git -C {} log --pretty=format:%H%n%an%n%at%n%s --shortstat --merges'
GIT_LOG_AUTHOR = ' --author={}'
GIT_LOG_AFTER = ' --after={}'
GIT_LOG_BEFORE = ' --before={}'
GIT_LOG_PATH = ' --> {}'


def construct_certification(repo, space_key):
    user_info = ProjectCoordinatorRelation.objects.filter(space_key=space_key)
    if len(user_info) == 0:
        return -1  # -1 means there is no user data
    username = user_info[0].git_username  # 'chengzsh3'
    password = user_info[0].git_password  # 'Czs0707+'
    if len(username) == 0 or len(password) == 0:
        return -2  # -2 means there doesn't exist git username and pwd
    return repo[0:8] + username + ':' + password + '@' + repo[8:]


def init_git():
    if not os.path.exists(REPO_PATH):
        os.mkdir(REPO_PATH)
    if not os.path.exists(COMMIT_DIR):
        os.mkdir(COMMIT_DIR)


def convert(repo: str):
    return '-'.join(repo.replace(GITHUB, '').split('/'))


def check_path_exist(path):
    return os.path.exists(path)


def process_changed(changed):
    file_pattern = re.findall('\d+ file', changed)
    insert_pattern = re.findall('\d+ insert', changed)
    delete_pattern = re.findall('\d+ delet', changed)

    file = 0 if not file_pattern else int(file_pattern[0].strip(' file'))
    insert = 0 if not insert_pattern else int(insert_pattern[0].strip(' insert'))
    delete = 0 if not delete_pattern else int(delete_pattern[0].strip(' delet'))
    return file, insert, delete


def pull_repo(repo, space_key):
    repo = construct_certification(repo, space_key)
    if repo == -1 or repo == -2:
        return repo
    path = REPO_PATH + convert(repo)

    if check_path_exist(path):
        git_update = GIT_UPDATE_COMMAND.format(path)
        logger.info('[GIT] Path: {} Executing: {}'.format(path, git_update))

        os.system(git_update)
        return 1  # 1 means valid

    git_clone = GIT_CLONE_COMMAND.format(repo, path)
    logger.info('[GIT] Path: {} Executing: {}'.format(path, git_clone))
    os.system(git_clone)
    return 1


def get_commits(repo, space_key, author=None, branch=None, after=None, before=None):
    state = pull_repo(repo, space_key)
    if state == -1 or state == -2:
        return state
    repo = construct_certification(repo, space_key)
    repo_path = REPO_PATH + convert(repo)
    path = COMMIT_DIR + '/' + convert(repo) + '.log'

    git_log = GIT_LOG_COMMAND.format(repo_path)
    if author:
        git_log += GIT_LOG_AUTHOR.format(author)
    if after:
        git_log += GIT_LOG_AFTER.format(after)
    if before:
        git_log += GIT_LOG_BEFORE.format(before)
    git_log += GIT_LOG_PATH.format(path)

    if not branch:
        branch = 'master'

    os.system(GIT_CHECKOUT_COMMAND.format(repo_path, branch))

    logger.info('[GIT] Path: {} Executing: {}'.format(path, git_log))
    os.system(git_log)

    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        return None

    commits = list()
    for i in range(0, len(lines), 6):
        # hash_code = lines[i].strip()
        author = lines[i + 1].strip()
        date = int(lines[i + 2].strip())

        commit = dict(
            # hash=hash_code,
            author=author,
            date=date,
        )
        commits.append(commit)
    return commits


def get_pull_request(repo, author=None, branch=None, after=None, before=None):
    pull_repo(repo)

    repo_path = REPO_PATH + convert(repo)
    path = COMMIT_DIR + '/' + convert(repo) + '.log'

    git_log = GIT_LOG_PR_COMMAND.format(repo_path)
    if author:
        git_log += GIT_LOG_AUTHOR.format(author)
    if after:
        git_log += GIT_LOG_AFTER.format(after)
    if before:
        git_log += GIT_LOG_BEFORE.format(before)
    git_log += GIT_LOG_PATH.format(path)

    if not branch:
        branch = 'master'

    os.system(GIT_CHECKOUT_COMMAND.format(repo_path, branch))

    logger.info('[GIT] Path: {} Executing: {}'.format(path, git_log))
    os.system(git_log)

    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    if not lines:
        raise Exception('git log error')

    commits = list()
    for i in range(0, len(lines), 4):
        hash_code = lines[i].strip()
        author = lines[i + 1].strip()
        date = int(lines[i + 2].strip()) * 1000
        description = lines[i + 3].strip()

        commit = dict(
            hash=hash_code,
            author=author,
            date=date,
            description=description,
        )
        commits.append(commit)
    return commits
# if __name__ == '__main__':
#     init_git()
#     pull_repo('https://github.com/LikwunCheung/TeamSPBackend')
#     get_commits('https://github.com/LikwunCheung/TeamSPBackend')

