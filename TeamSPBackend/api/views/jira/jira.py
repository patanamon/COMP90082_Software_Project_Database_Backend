from django.apps import AppConfig
from atlassian import Jira
import json
import time
import datetime
import sys
import re
import csv
import logging

from math import ceil
from django.views.decorators.http import require_http_methods
from django.http.response import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from shutil import copyfile
import fileinput
# for file op
import os
import time
from dateutil import parser

from TeamSPBackend.common import utils
from TeamSPBackend.common.choices import RespCode
from TeamSPBackend.common.utils import init_http_response
from TeamSPBackend.common.utils import init_http_response_withoutdata
from TeamSPBackend.common.utils import start_schedule
from TeamSPBackend.api.views.jira.models import JiraCountByTime
from TeamSPBackend.api.views.jira.models import IndividualContributions
from TeamSPBackend.api.views.jira.models import Urlconfig
from TeamSPBackend.project.models import ProjectCoordinatorRelation
from TeamSPBackend.coordinator.models import Coordinator
from TeamSPBackend.api.config import atl_username, atl_password
from TeamSPBackend.git.views import auto_update_commits


# helper functions
def session_interpreter(request):
    """ Extracts credentials from session"""
    user = request.session.get('user')
    username = user['atl_username']
    password = user['atl_password']
    return username, password


def jira_login(request):
    """ Handles Jira login"""
    # username, password = session_interpreter(request)
    username = atl_username
    password = atl_password
    jira = Jira(
        url='https://jira.cis.unimelb.edu.au:8444',
        username=username,
        password=password,
        # verify_ssl=False # not required with ssl mitigation
    )
    return jira


def get_project_key(project, jira):
    """"Get corresponding project key"""
    jira_resp = jira.projects()
    result = ""
    for d in jira_resp:
        if d['name'].lower() == project:
            result = d['key']

    return result


def get_done_contributor_names(team, jira):
    """Get contributors (name, displayName) list of a project"""
    data = []
    total = jira.jql('project = "' + team + '" AND Status = Done', limit=0)['total']  # get total issue count
    for i in range(ceil(total / 100)):  # recurring query if count > 100
        start = 0 + i * 100
        data.append(jira.jql('project = ' + team + ' AND Status = Done', start=start, limit=100)['issues'])
    data = [issue for data_slice in data for issue in data_slice]  # flatten
    name_lst = []
    display_name_lst = []
    for i in range(len(data)):
        result = data[i]['fields']['assignee']
        if result is not None:
            if result['name'] not in name_lst:
                name_lst.append(result['name'])
            if result['displayName'] not in display_name_lst:
                display_name_lst.append(result['displayName'])
    return name_lst, display_name_lst


def datetime_truncate(t):
    """returns truncated datetime object that only contains date"""
    t = t.replace(hour=0, minute=0, second=0, microsecond=0)
    t = datetime.date(t.year, t.month, t.day)
    return t


def to_unix_time(day):
    """returns unix timestamp from truncated datetime object """
    return time.mktime(datetime.datetime.strptime(str(day), "%Y-%m-%d").timetuple())


def key_extracter(d):
    """Converts dict of jira url to jira key
    Usage: [key_extracter(d) for e in list(djangoresult)]
    """
    def url_to_key(s):
        """Converts possible URLs to jira team key"""
        url_re = re.compile(
            '((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*')
        if re.match(url_re, s):
            if s[-1] == '/':
                s = s.rsplit('/', 3)[1].lower()
                s = s.split('?')[0]
            else:
                s = s.rsplit('/', 2)[1].lower()
                s = s.split('/')[0]
        return s
    return {k: url_to_key(v) for k, v in d.items()}

def key_extracter2(s):
    url_re = re.compile(
        '((http|https)\:\/\/)?[a-zA-Z0-9\.\/\?\:@\-_=#]+\.([a-zA-Z]){2,6}([a-zA-Z0-9\.\&\/\?\:@\-_=#])*')
    if re.match(url_re,s):
        if s[-1] == '/':
            s = s.rsplit('/', 3)[1].lower()
            s = s.split('?')[0]
        else:
            s = s.rsplit('/', 2)[1].lower()
            s = s.split('?')[0]
    return s


# Legacy APIs
@require_http_methods(['GET'])
def get_issues_individual(request, team, student):
    """ Return a HttpResponse, data contains count of all categories of issues (of an individual)"""
    try:
        jira = jira_login(request)

        total = jira.jql('assignee = ' + student + ' AND project = ' + team)['total']
        todo = jira.jql('assignee = ' + student + ' AND project = ' + team + ' AND status = "To Do"')['total']
        in_progress = jira.jql('assignee = ' + student + ' AND project = '
                               + team + ' AND status = "In Progress"')['total']
        done = jira.jql('assignee = ' + student + ' AND project = '
                        + team + ' AND status = "Done"')['total']
        in_review = jira.jql('assignee = ' + student + ' AND project = '
                             + team + ' AND status = "In Review"')['total']
        review = jira.jql('assignee = ' + student + ' AND project = '
                          + team + ' AND status = "Review"')['total']
        data = {
            'student': student,
            'count_issues_total': total,
            'count_issues_to_do': todo,
            'count_issues_progress': in_progress,
            'count_issues_in_review': in_review,
            'count_issues_done': done,
            'count_issues_review': review
        }
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except Exception:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_issues_team(request, team):
    """ Return a HttpResponse, data contains count of all categories of issues (of a team)"""
    try:
        jira = jira_login(request)

        total = jira.jql('project = ' + team)['total']
        todo = jira.jql('project = ' + team + ' AND status = "To Do"')['total']
        in_progress = jira.jql('project = ' + team + ' AND status = "In Progress"')['total']
        done = jira.jql('project = ' + team + ' AND status = "Done"')['total']
        in_review = jira.jql('project = ' + team + ' AND status = "In Review"')['total']
        review = jira.jql('project = ' + team + ' AND status = "Review"')['total']
        data = {
            'count_issues_total': total,
            'count_issues_to_do': todo,
            'count_issues_progress': in_progress,
            'count_issues_in_review': in_review,
            'count_issues_done': done,
            'count_issues_review': review
        }
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except Exception:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_comment_count_individual(request, team, student):
    """ Return a HttpResponse, with username and comment fields"""
    try:
        jira = jira_login(request)

        issues = json.dumps(jira.get_all_project_issues(team, fields='comment'))
        count = issues.count(student)
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['username'] = student
        resp['comments'] = count / 16
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except Exception:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_sprints_dates(request, team):
    try:
        jira = jira_login(request)
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)

        issues = json.dumps(jira.get_all_project_issues(team, fields='*all'))
        split = issues.split("name=Sprint 1,startDate=", 1)
        split2 = split[1].split("endDate=", 1)
        if split[1][:10].startswith('20'):
            resp['sprint_1_start'] = split[1][:10]
        else:
            resp['sprint_1_start'] = "null"
        if split[1][:10].startswith('20'):
            resp['sprint_1_end'] = split2[1][:10]
        else:
            resp['sprint_1_end'] = "null"

        split = issues.split("name=Sprint 2,startDate=", 1)
        split2 = split[1].split("endDate=", 1)
        if split[1][:10].startswith('20'):
            resp['sprint_2_start'] = split[1][:10]
        else:
            resp['sprint_2_start'] = "null"
        if split[1][:10].startswith('20'):
            resp['sprint_2_end'] = split2[1][:10]
        else:
            resp['sprint_2_end'] = "null"

        split = issues.split("name=Sprint 3,startDate=", 1)
        split2 = split[1].split("endDate=", 1)
        if split[1][:10].startswith('20'):
            resp['sprint_3_start'] = split[1][:10]
        else:
            resp['sprint_3_start'] = "null"
        if split[1][:10].startswith('20'):
            resp['sprint_3_end'] = split2[1][:10]
        else:
            resp['sprint_3_end'] = "null"

        split = issues.split("name=Sprint 4,startDate=", 1)
        split2 = split[1].split("endDate=", 1)
        if split[1][:10].startswith('20'):
            resp['sprint_4_start'] = split[1][:10]
        else:
            resp['sprint_4_start'] = "null"
        if split[1][:10].startswith('20'):
            resp['sprint_4_end'] = split2[1][:10]
        else:
            resp['sprint_4_end'] = "null"
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except Exception:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_issues_per_sprint(request, team):
    try:
        jira = jira_login(request)
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        issues = json.dumps(jira.get_all_project_issues(team, fields='*all'))
        split = issues.split("[id=")
        sprint_ids = []
        for str in split[1:]:
            split2 = str.split(",")
            id = split2[0]
            if id not in sprint_ids:
                sprint_ids.append(id)
        sprint_ids.sort()
        i = 1
        for id in sprint_ids:
            jql_request = 'Sprint = id'
            jql_request = jql_request.replace('id', id)
            issues = jira.jql(jql_request)
            count_issues_total = issues['total']
            resp[i] = count_issues_total
            i += 1
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except Exception:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


# New APIs
@require_http_methods(['GET'])
def auto_get_ticket_count_team_timestamped(request):
    """ Return a HttpResponse, data contains 3 kinds of issues timestamped with unix time of each day"""
    try:
        teamList = get_all_url_from_db()
        username = atl_username
        password = atl_password
        for i in range(len(teamList)):
            team = teamList[i]
            jira_analytics(username, password, team)
            data = []
            with open('TeamSPBackend/api/views/jira/cfd_modified.csv', newline='') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    data.append({
                        'time': round(to_unix_time(datetime_truncate(parser.parse(row['Time'])))),
                        'to_do': int(float(row['To Do'])),
                        'in_progress': int(float(row['In Progress'])),
                        'done': int(float(row['Done']))
                    })
                    if not JiraCountByTime.objects.filter(space_key=team, time=round(to_unix_time(datetime_truncate(
                            parser.parse(row['Time']))))).exists():
                        jira_obj = JiraCountByTime(space_key=team,
                                                   time=round(to_unix_time(datetime_truncate(parser.parse(row['Time'])))),
                                                   to_do=int(float(row['To Do'])),
                                                   in_progress=int(float(row['In Progress'])),
                                                   done=int(float(row['Done'])))
                        jira_obj.save()
            os.remove('TeamSPBackend/api/views/jira/cfd_modified.csv')
            os.remove('TeamSPBackend/api/views/jira/cfd.yaml')
            copyfile('TeamSPBackend/api/views/jira/cfd-template.csv',
                     'TeamSPBackend/api/views/jira/cfd.csv')
            copyfile('TeamSPBackend/api/views/jira/cfd-template.png',
                     'TeamSPBackend/api/views/jira/cfd.png')
        return HttpResponse(data, content_type="application/json")
    except Exception:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


def update_ticket_count_team_timestamped(jira_url):
    username = atl_username
    password = atl_password
    team = get_url_from_db(jira_url)

    jira_analytics(username, password, team)

    data = []
    with open('TeamSPBackend/api/views/jira/cfd_modified.csv', newline='') as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            data.append({
                'time': round(to_unix_time(datetime_truncate(parser.parse(row['Time'])))),
                'to_do': int(float(row['To Do'])),
                'in_progress': int(float(row['In Progress'])),
                'done': int(float(row['Done']))
            })
            if not JiraCountByTime.objects.filter(space_key=team, time=round(to_unix_time(datetime_truncate(
                    parser.parse(row['Time']))))).exists():
                jira_obj = JiraCountByTime(space_key=team,
                                           time=round(to_unix_time(datetime_truncate(parser.parse(row['Time'])))),
                                           to_do=int(float(row['To Do'])),
                                           in_progress=int(float(row['In Progress'])),
                                           done=int(float(row['Done'])))
                jira_obj.save()
    os.remove('TeamSPBackend/api/views/jira/cfd_modified.csv')
    os.remove('TeamSPBackend/api/views/jira/cfd.yaml')
    copyfile('TeamSPBackend/api/views/jira/cfd-template.csv',
             'TeamSPBackend/api/views/jira/cfd.csv')
    copyfile('TeamSPBackend/api/views/jira/cfd-template.png',
             'TeamSPBackend/api/views/jira/cfd.png')

    return team


@require_http_methods(['GET'])
def get_contributions(request, team):
    """ Return a HttpResponse, data contains display names and Done Counts"""
    try:
        jira = jira_login(request)

        students, names = get_done_contributor_names(get_project_key(team, jira), jira)
        team = get_project_key(team, jira)
        count = []
        for student in students:
            count.append(jira.jql('assignee = ' + student + ' AND project = "'
                                  + team + '" AND status = "Done"')['total'])
        result = dict(zip(names, count))

        data = []
        for name, count in result.items():
            data.append({
                'student': name,
                'done_count': count
            })
            if IndividualContributions.objects.filter(space_key=team, student=name).exists():
                IndividualContributions.objects.filter(space_key=team, student=name).update(done_count=count)
            else:
                jira_obj = IndividualContributions(space_key=team, student=name, done_count=count)
                jira_obj.save()

        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except Exception:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


def update_contributions(jira_url):
    """Immediately updates jira contribution"""
    jira = jira_login(request)
    team = get_url_from_db(jira_url)

    students, names = get_done_contributor_names(team, jira)
    count = []
    for student in students:
        count.append(jira.jql('assignee = ' + student + ' AND project = "'
                              + team + '" AND status = "Done"')['total'])
    result = dict(zip(names, count))

    data = []
    for name, count in result.items():
        data.append({
            'student': name,
            'done_count': count
        })
        if IndividualContributions.objects.filter(space_key=team, student=name).exists():
            IndividualContributions.objects.filter(space_key=team, student=name).update(done_count=count)
        else:
            jira_obj = IndividualContributions(space_key=team, student=name, done_count=count)
            jira_obj.save()

    resp = init_http_response(
        RespCode.success.value.key, RespCode.success.value.msg)
    resp['data'] = data
    return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def auto_get_contributions(request):
    jira = jira_login(request)
    try:
        allProjects = jira.projects()
        for p in allProjects:
            get_contributions(request, p['name'].lower())
        resp = init_http_response_withoutdata(
            RespCode.success.value.key, RespCode.success.value.msg)
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except Exception:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_contributions_from_db(request, team):
    try:
        coordinator_id = request.session.get('coordinator_id')
        existRecord = list(
            ProjectCoordinatorRelation.objects.filter(coordinator_id=coordinator_id, space_key=team).values(
                'jira_project'))
        url = key_extracter(existRecord[0])
        jira_url = url.get('jira_project')

        allExistRecord = list(IndividualContributions.objects.filter(space_key=jira_url).values('student', 'done_count'))

        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = allExistRecord
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except Exception:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['POST'])
def setGithubJiraUrl(request):
    try:
        coordinator_id = request.session.get('coordinator_id')
        logger = logging.getLogger('django')
        logger.info(coordinator_id)
        data = json.loads(request.body)
        space_key = data.get("space_key")
        logger.info(space_key)
        git_url = data.get("git_url")
        logger.info(git_url)
        jira_url = data.get("jira_url")
        logger.info(jira_url)
        git_username = data.get("git_username")
        logger.info(git_username)
        git_password = data.get("git_password")
        logger.info(git_password)

        existURLRecord = ProjectCoordinatorRelation.objects.get(coordinator_id=coordinator_id, space_key=space_key)
        existURLRecord.git_url = git_url
        existURLRecord.jira_project = jira_url
        existURLRecord.git_username = git_username
        existURLRecord.git_password = git_password
        existURLRecord.save()

        # auto_update_commits(space_key)  # after setting git config, try to update git_commit table at once
        update_ticket_count_team_timestamped(
            jira_url)  # after setting jira config, try to update jira_count_by_time table at once
        update_contributions(jira_url)

        resp = init_http_response_withoutdata(
            RespCode.success.value.key, RespCode.success.value.msg)
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except Exception:
        resp = init_http_response_withoutdata(
            RespCode.success.value.key, RespCode.success.value.msg)
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_ticket_count_from_db(request, team):
    try:
        coordinator_id = request.session.get('coordinator_id')
        existRecord = list(
            ProjectCoordinatorRelation.objects.filter(coordinator_id=coordinator_id, space_key=team).values(
                'jira_project'))
        url = key_extracter(existRecord[0])
        jira_url = url.get('jira_project')

        ticketCountRecord = list(
            JiraCountByTime.objects.filter(space_key=jira_url).values('time', 'to_do', 'in_progress', 'done'))
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = ticketCountRecord
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except Exception:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


def get_all_url_from_db():
    allURL = []
    allExistRecord = list(ProjectCoordinatorRelation.objects.values('jira_project').distinct())
    for record in allExistRecord:
        url = key_extracter(record)
        jira_url = url.get('jira_project')
        allURL.append(jira_url)
    return allURL

def get_url_from_db(jira_url):
    record = key_extracter2(jira_url)
    return record


def jira_analytics(username, password, team):
    """Only queries cfd with jira-agile-metrics"""
    copyfile('TeamSPBackend/api/views/jira/cfd-template.yaml', 'TeamSPBackend/api/views/jira/cfd.yaml')
    with open('TeamSPBackend/api/views/jira/cfd.yaml', 'r') as file:
        data = file.read()
        data = data.replace('jirainstance', 'https://jira.cis.unimelb.edu.au:8444')
        data = data.replace('usernameplace', username)
        data = data.replace('passwordplace', password)
        data = data.replace('projectplace', team)
    with open('TeamSPBackend/api/views/jira/cfd.yaml', 'w') as file:
        file.write(data)
    os.system(
        "jira-agile-metrics TeamSPBackend/api/views/jira/cfd.yaml --output-directory TeamSPBackend/api/views/jira")
    copyfile('TeamSPBackend/api/views/jira/cfd-template.yaml',
             'TeamSPBackend/api/views/jira/cfd.yaml')  # overwrites sensitive info
    # rename csv headers
    inputFileName = 'TeamSPBackend/api/views/jira/cfd.csv'
    outputFileName = os.path.splitext(inputFileName)[0] + "_modified.csv"
    with open(outputFileName, "w") as outfile:
        for line in fileinput.input(
                ['TeamSPBackend/api/views/jira/cfd.csv'],
                inplace=False):
            if fileinput.isfirstline():
                outfile.write('Time,To Do,In Progress,Done\n')
            else:
                outfile.write(line)



if 'runserver' in sys.argv:
    from django.http import HttpRequest

    request = HttpRequest()
    request.method = 'GET'
    request.build_absolute_uri
    request.META['SERVER_NAME'] = request.build_absolute_uri
    utils.start_schedule(auto_get_contributions, 60 * 60 * 24, request)
    utils.start_schedule(auto_get_ticket_count_team_timestamped, 60 * 60 * 24, request)
