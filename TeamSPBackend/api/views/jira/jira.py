from atlassian import Jira
import json
import time


from django.views.decorators.http import require_http_methods
from django.http.response import HttpResponse

# for file op
# TODO: charts output
# TODO: django app integration
import os
import time

from TeamSPBackend.common.choices import RespCode
from TeamSPBackend.common.utils import init_http_response
# import test table
from TeamSPBackend.api.views.jira.models import TestJira

from TeamSPBackend.project.models import ProjectCoordinatorRelation

# helper functions
def session_interpreter(request):
    user = request.session.get('user')
    username = user['atl_username']
    password = user['atl_password']
    return username, password


def jira_login(request):
    username, password = session_interpreter(request)
    jira = Jira(
        url='https://jira.cis.unimelb.edu.au:8444',
        username='',
        password='',
        verify_ssl=False
    )
    return jira


# legacy
@require_http_methods(['GET'])
def get_issues_individual(request, team, student):
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


# new
@require_http_methods(['GET'])
def get_ticket_count_team_timestamped(request, team):
    try:
        # jira = jira_login(request)
        jira = Jira(
            url='https://jira.cis.unimelb.edu.au:8444',
            username='',
            password='',
            verify_ssl=False
        )

        todo = jira.jql('project = ' + team + ' AND status = "To Do"')['total']
        in_progress = jira.jql('project = ' + team + ' AND status = "In Progress"')['total']
        done = jira.jql('project = ' + team + ' AND status = "Done"')['total']
        data = {
            'time': time.time(),
            'to_do': todo,
            'in_progress': in_progress,
            'done': done,
        }
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


# not working

def jira_analytics(request, team):
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
    jira_analytics(request, team)
    while not os.path.exists('TeamSPBackend/api/views/jira/cfd.png'):
        time.sleep(1)

    if os.path.isfile('TeamSPBackend/api/views/jira/cfd.png'):
        time.sleep(1)
        data = open('TeamSPBackend/api/views/jira/cfd.png', 'rb').read()
        return HttpResponse(data, content_type="image/png")

# testing

@require_http_methods(['GET'])
def hey(request):
    # username, password = session_interpreter(request)
    jira = Jira(
        url='https://jira.cis.unimelb.edu.au:8444',
        username='',
        password='',
        verify_ssl=False
    )
    team = 'swen90013-2020-sp'
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


@require_http_methods(['POST'])
def setGithubJiraUrl(request,team):
    jira = Jira(
        url='https://jira.cis.unimelb.edu.au:8444',
        username='',
        password='',
        verify_ssl=False
    )
    # team = 'swen90013-2020-sp'
    jira_obj = ProjectCoordinatorRelation(coordinator_id='1',space_key=team,git_url="123.com",jira_project = "234.com")
    jira_obj.save()
    a = 'success'
    return HttpResponse(json.dumps(a), content_type="application/json")

