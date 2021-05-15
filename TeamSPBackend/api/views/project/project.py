from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
import json
import operator
import requests

from TeamSPBackend.common.choices import RespCode
from TeamSPBackend.coordinator.models import Coordinator
from TeamSPBackend.project.models import ProjectCoordinatorRelation
from TeamSPBackend.common.utils import init_http_response
from threading import Timer
from TeamSPBackend.confluence.views import insert_space_user_list, insert_space_page_contribution, insert_space_page_history


@require_http_methods(['POST'])
# @check_body
def import_project_in_batch(request, *args, **kwargs):
    # Method: POST
    try:
        query_dict = request.POST
        coordinator = query_dict['coordinator']
        project_list = [x.strip() for x in query_dict['project_list'].split(',')]
        # get coordinator_id based on coordinator_name
        if len(Coordinator.objects.filter(coordinator_name=coordinator)) == 0:
            print('No existing coordinator')
        else:
            coordinator_id = Coordinator.objects.filter(coordinator_name=coordinator)[0].id
            for x in project_list:
                import_project(coordinator_id, x)
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': 0, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


def store_coordinator(username):
    if len(Coordinator.objects.filter(coordinator_name=username)) == 0:
        coordinator = Coordinator(coordinator_name=username, )
        coordinator.save()

@require_http_methods(['POST'])
def login_sso(request, *args, **kwargs):
    try:
        json_body = json.loads(request.body)
        username = json_body.get("username")
        password = json_body.get("password")
        url = 'https://sso.unimelb.edu.au/api/v1/authn'
        data = {"username": username, "password": password}
        res = requests.post(url=url, json=data)
        if operator.eq(res.json().get("status"),"SUCCESS"):
            resp = init_http_response(
                RespCode.success.value.key, RespCode.success.value.msg)
            store_coordinator(username)
            # put username into session
            request.session['coordinator_id'] = Coordinator.objects.filter(coordinator_name=username)[0].id
            request.session['coordinator_name'] = username
        else:
            resp = {'code': -2, 'msg': 'authentication failed'}
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except Exception as e:
        print(e)
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


def import_project(coordinator_id, project):
    # check if this relation has already existed to avoid overwrite
    if len(ProjectCoordinatorRelation.objects.filter(coordinator_id=coordinator_id, space_key=project)) == 0:
        relation = ProjectCoordinatorRelation(coordinator_id=coordinator_id, space_key=project)
        relation.save()
        Timer(0, insert_space_user_list, project).start()
        Timer(0, insert_space_page_history, project).start()
