# TODO: space_key is not used in jira, clarification required, currently we use Project in JQL
# TODO: illegal value assignments in legacy code, specifically response only have data field.
# TODO: Re-adapt to fit legacy API documentation, include: variable rename, django app integration
# TODO: Specify except statement to avoid accidental termination
# TODO: django app integration
# TODO: charts output
from django.apps import AppConfig
from atlassian import Jira
import json
import time
import datetime

from django.views.decorators.http import require_http_methods
from django.http.response import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
# for file op
import os
import time
from dateutil import parser

from TeamSPBackend.common.choices import RespCode
from TeamSPBackend.common.utils import init_http_response
from TeamSPBackend.common.utils import start_schedule
from TeamSPBackend.api.views.jira.models import JiraCountByTime
from TeamSPBackend.api.views.jira.models import IndividualContributions
from TeamSPBackend.api.views.jira.models import Urlconfig

# helper functions
def session_interpreter(request):
    """ Extracts credentials from session"""
    user = request.session.get('user')
    username = user['atl_username']
    password = user['atl_password']
    return username, password


def jira_login(request):
    """ Handles Jira login"""
    username, password = session_interpreter(request)
    jira = Jira(
        url='https://jira.cis.unimelb.edu.au:8444',
        username='',
        password='',
        verify_ssl=False
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


def get_member_names(project_key, jira):
    """"Get team members with project key"""
    jira_resp = jira.get_all_assignable_users_for_project(project_key)
    name = []
    display_name = []
    for d in jira_resp:
        name.append(d['name'])
        display_name.append(d['displayName'])

    return name, display_name


def datetime_truncate(t):
    """returns truncated datetime object that only contains date"""
    t = t.replace(hour=0, minute=0, second=0, microsecond=0)
    t = datetime.date(t.year, t.month, t.day)
    return t


def to_unix_time(day):
    """returns unix timestamp from truncated datetime object """
    return time.mktime(datetime.datetime.strptime(str(day), "%Y-%m-%d").timetuple())


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
    except:
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
    except:
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
    except:
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
    except:
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
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


# New APIs
@require_http_methods(['GET'])
def get_ticket_count_team_timestamped(request, team):
     """ Return a HttpResponse, data contains 3 kinds of issues timestamped with unix time of each day"""
     try:
        jira = jira_login(request)

        jquery = jira.jql('project = ' + team + ' ORDER BY created ASC')['issues'][0]['fields']['created']

        # parses to datetime object
        jquery = parser.parse(jquery)

        d0 = datetime_truncate(jquery)
        today = datetime.date.today()

        delta = today - d0

        date_list = [today - datetime.timedelta(days=x) for x in range(delta.days)]

        data = []
        for day in reversed(date_list):
            todo = jira.jql('project = ' + team + ' AND status WAS "To Do" ON ' + str(day))['total']
            in_progress = jira.jql('project = ' + team + ' AND status WAS "In Progress" ON ' + str(day))['total']
            done = jira.jql('project = ' + team + ' AND status WAS "Done" ON ' + str(day))['total']
            #print(day, todo, in_progress, done)
            data.append({
                'time': to_unix_time(day),
                'to_do': todo,
                'in_progress': in_progress,
                'done': done
            })

            jira_obj = JiraCountByTime(space_key=team, count_time=time.strftime('%Y-%m-%d', time.localtime(int((to_unix_time(day))))), todo=todo,
                                       in_progress=in_progress, done=done)
            jira_obj.save()

        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
     except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")

@require_http_methods(['GET'])
def get_contributions(request, team):
    """ Return a HttpResponse, data contains display names and Done Counts
    NOTE:
    jira.get_all_assignable_users_for_project returns assignable users
    jql assignee returns issues assigned to users

    assignable users may have zero records, let alone DONE
    whilst assignees may have been deactivated, thus not gettable with jira methods
    """
    try:
        jira = jira_login(request)

        students, names = get_member_names(get_project_key(team, jira), jira)
        count = []
        for student in students:
            count.append(jira.jql('assignee = ' + student + ' AND project = '
                                  + team + ' AND status = "Done"')['total'])
        result = dict(zip(names, count))

        data = []
        for name, count in result.items():
            data.append({
                'student': name,
                'done_count': count
            })
            jira_obj = IndividualContributions(space_key=team,student=name, done_count=count)
            jira_obj.save()

        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_contributions_from_db(request,team):
    try:

        allExistRecord=list(IndividualContributions.objects.filter(space_key=team).values('student','done_count'))

        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = allExistRecord
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_ticket_count_team_timestamped_afterthefirstrun(request, team):
    """ Return a HttpResponse, data contains 3 kinds of issues timestamped with unix time"""
    try:
        jira = jira_login(request)

        todo = jira.jql('project = ' + team + ' AND status = "To Do"')['total']
        in_progress = jira.jql('project = ' + team + ' AND status = "In Progress"')['total']
        done = jira.jql('project = ' + team + ' AND status = "Done"')['total']
        data = {
            'time': time.strftime('%Y-%m-%d', time.localtime(to_unix_time(datetime.date.today()))),
            'to_do': todo,
            'in_progress': in_progress,
            'done': done,
        }

        jira_obj = JiraCountByTime(space_key=team,count_time=data['time'], todo=data['to_do'], in_progress=data['in_progress'], done=data['done'])
        jira_obj.save()

        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_ticket_count_team_timestamped_from_db(request,team):
    try:
        allExistRecord=list(JiraCountByTime.objects.filter(space_key=team).values('count_time','todo','in_progress','done'))

        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = allExistRecord
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def auto_get_ticket_count_team_timestamped(request):
     jira = jira_login(request)
     allProjects = jira.projects()
     for p in allProjects:
        # first run, fetch all the records from the date the project is created
        get_ticket_count_team_timestamped(request, p['name'])

     time.sleep(60 * 60 * 24)
     for p in allProjects:
        start_schedule(get_ticket_count_team_timestamped_afterthefirstrun, 60 * 60 * 24, request, p['name'])

     resp = 'success!'
     return HttpResponse(resp, content_type="application/json")


@require_http_methods(['POST'])
def setGithubJiraUrl(request,team):
    try:
        data = request.POST
        git_url = data['git_url']
        jira_url = data['jira_url']
        git_username = data['git_username']
        git_password = data['git_password']

        try:
            existRecord = Urlconfig.objects.get(git_username=git_username,space_key=team)
            existRecord.git_url=git_url
            existRecord.jira_url=jira_url
            existRecord.git_username = git_username
            existRecord.git_password = git_password
            existRecord.save()
        except ObjectDoesNotExist:
            # team = 'swen90013-2020-sp'
            jira_obj = Urlconfig(space_key=team,git_url=git_url,jira_url = jira_url,git_username=git_username,git_password=git_password)
            jira_obj.save()


        resp = init_http_response(
             RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = 'success'
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")

@require_http_methods(['POST'])
def get_url_from_db(request,team):
    try:
        data = request.POST
        git_username = data['git_username']
        allExistRecord=list(Urlconfig.objects.filter(git_username=git_username,space_key=team).values('git_url','jira_url'))

        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = allExistRecord
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


# Legacy APIs, not working

def jira_analytics(request, team):
    """ Configures config.yml and executes it with jira-agile-metrics"""
    username, password = session_interpreter(request)
    with open('config.yaml', 'r') as file:
        data = file.read()
        data = data.replace('usernameplace', username)
        data = data.replace('passwordplace', password)
        data = data.replace('projectplace', team)
    with open('config.yaml', 'w') as file:
        file.write(data)
    os.popen("jira-agile-metrics config.yaml --output-directory TeamSPBackend/api/views/jira")


@require_http_methods(['GET'])
def get_jira_cfd(request, team):
    """ Return a HttpResponse, data contains a a png of Cumulative Flow Diagram"""
    jira_analytics(request, team)
    while not os.path.exists('TeamSPBackend/api/views/jira/cfd.png'):
        time.sleep(1)

    if os.path.isfile('TeamSPBackend/api/views/jira/cfd.png'):
        time.sleep(1)
        data = open('TeamSPBackend/api/views/jira/cfd.png', 'rb').read()
        return HttpResponse(data, content_type="image/png")


