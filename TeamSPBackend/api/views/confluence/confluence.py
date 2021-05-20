from atlassian import Confluence
import json
import requests
from requests.auth import HTTPBasicAuth

from TeamSPBackend.common.choices import RespCode
from django.views.decorators.http import require_http_methods
from django.http.response import HttpResponse
from TeamSPBackend.common.utils import init_http_response, check_login
from TeamSPBackend.confluence.models import UserList
from TeamSPBackend.confluence.models import MeetingMinutes

from TeamSPBackend.project.models import ProjectCoordinatorRelation

from TeamSPBackend.confluence.models import PageHistory
from TeamSPBackend.coordinator.models import Coordinator
from TeamSPBackend.api import config


@require_http_methods(['GET'])
def get_all_groups(request):
    """Get all groups accessable by the logged in user
    Method: GET
    """
    user = request.session.get('user')
    username = user['atl_username']
    password = user['atl_password']
    try:
        confluence = log_into_confluence(username, password)
        conf_resp = confluence.get_all_groups()
        data = []
        for group in conf_resp:
            data.append({
                'type': group['type'],
                'name': group['name']
            })
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_space(request, space_key):
    """Get a Confluence Space
    Method: GET
    Request: space_key
    """
    user = request.session.get('user')
    username = user['atl_username']
    password = user['atl_password']
    try:
        confluence = log_into_confluence(username, password)
        conf_resp = confluence.get_space(
            space_key, expand='homepage')
        conf_homepage = conf_resp['homepage']
        data = {
            'id': conf_resp['id'],
            'key': conf_resp['key'],
            'name': conf_resp['name'],
            'homepage': {
                'id': conf_homepage['id'],
                'type': conf_homepage['type'],
                'title': conf_homepage['title'],

            }
        }
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_pages_of_space(request, space_key):
    """Get all the pages under the Confluence Space
    Method: GET
    Request: space
    """
    user = request.session.get('user')
    username = user['atl_username']
    password = user['atl_password']
    try:
        confluence = log_into_confluence(username, password)
        conf_resp = confluence.get_all_pages_from_space(space_key)
        data = []
        for page in conf_resp:
            data.append({
                'id': page['id'],
                'type': page['type'],
                'title': page['title']
            })
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")

    # Get Page Content by ID (HTML) (lower prio for now)


@require_http_methods(['GET'])
def search_team(request, keyword):
    user = request.session.get('user')
    username = user['atl_username']
    password = user['atl_password']
    try:
        confluence = log_into_confluence(username, password)
        conf_resp = confluence.get_all_groups()
        data = []
        result = []
        for group in conf_resp:
            data.append({
                'type': group['type'],
                'name': group['name']
            })
        for element in data:
            if keyword.lower() in element['name'].lower():
                result.append({
                    'name': element['name']
                })
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = result
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_group_members(request, group):
    """Get all the members under 'group_name' of the Confluence Space
    Method: GET
    Request: group_name
    """
    try:
        user = request.session.get('user')
        username = user['atl_username']
        password = user['atl_password']
        group_name = group
        confluence = log_into_confluence(username, password)
        conf_resp = confluence.get_group_members(group_name)
        data = []
        for user in conf_resp:
            data.append({
                # 'type': user['type'],
                # 'userKey': user['userKey'],
                # 'profilePicture': user['profilePicture'],
                'name': user['displayName'],
                'email': user['username'] + "@student.unimelb.edu.au"
            })
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_user_details(request, member):
    """Get a specific Confluence Space member's details
    Method: POST
    Request: member's username
    """
    user = request.session.get('user')
    username = user['atl_username']
    password = user['atl_password']
    try:
        confluence = log_into_confluence(username, password)
        conf_resp = confluence.get_user_details_by_username(member)
        data = {
            'type': conf_resp['type'],
            'username': conf_resp['username'],
            'userKey': conf_resp['userKey'],
            'profilePicture': conf_resp['profilePicture'],
            'displayName': conf_resp['displayName']
        }
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_subject_supervisors(request, subjectcode, year):
    user = request.session.get('user')
    username = user['atl_username']
    password = user['atl_password']
    try:
        confluence = log_into_confluence(username, password)
        conf_resp = confluence.get_all_groups()
        supervisors = []
        data = []
        for group in conf_resp:
            if "staff" in group['name'] and year in group['name'] and subjectcode in group['name']:
                supervisors = confluence.get_group_members(group['name'])

        for each in supervisors:
            data.append({
                # 'type': user['type'],
                # 'userKey': user['userKey'],
                # 'profilePicture': user['profilePicture'],
                'name': each['displayName'],
                'email': each['username']
            })
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
def get_page_contributors(request, *args, **kwargs):
    """Get a Confluence page's contributors
    Method: Get
    Request: page_id
    """
    user = request.session.get('user')
    username = user['atl_username']
    password = user['atl_password']
    try:
        confluence = log_into_confluence(username, password)
        page_id = kwargs['page_id']
        # Todo: change these to configurable inputs
        domain = "https://confluence.cis.unimelb.edu.au"
        port = "8443"
        url = f"{domain}:{port}/rest/api/content/{page_id}/history"
        parameters = {"expand": "contributors.publishers.users"}
        conf_resp = requests.get(
            url, params=parameters, auth=HTTPBasicAuth(username, password)).json()
        data = {
            "createdBy": conf_resp["createdBy"],
            "createdDate": conf_resp["createdDate"],
            "contributors": conf_resp["contributors"]
        }
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


def log_into_confluence(username, password):
    confluence = Confluence(
        url='https://confluence.cis.unimelb.edu.au:8443/',
        username=username,
        password=password,
        verify_ssl=False
    )
    return confluence


def get_members(request, group):
    try:
        user = request.session.get('user')
        username = user['atl_username']
        password = user['atl_password']
        confluence = log_into_confluence(username, password)
        conf_resp = confluence.get_group_members(group)
        data = []
        for user in conf_resp:
            data.append({
                # 'type': user['type'],
                # 'userKey': user['userKey'],
                # 'profilePicture': user['profilePicture'],
                'name': user['displayName'],
                'email': user['username'] + "@student.unimelb.edu.au"
            })
        return data
    except Exception as e:
        print(e)
        return None


@require_http_methods(['GET'])
@check_login()
def get_spaces_by_key(request, key_word):
    """Get a list of Confluence space keys that contains the key word
    Method: GET
    Request: key_word
    """
    username = config.atl_username
    password = config.atl_password
    try:
        confluence = log_into_confluence(username, password)
        spaces = confluence.get_all_spaces()
        space_keys = [space['key'] for space in spaces if key_word.lower() in space['key'].lower()]
        while len(spaces) > 0:
            spaces = confluence.get_all_spaces(start=len(spaces))
            space_keys.extend([space['key'] for space in spaces if key_word.lower() in space['key'].lower()])

        resp = init_http_response(RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = space_keys
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
@check_login()
def get_user_list(request, space_key):
    """Get the user list in a Confluence space
    Method: Get
    Parameter: space_key
    """
    try:
        user_list = []
        for user_info in UserList.objects.filter(space_key=space_key):
            user_detail = {
                "name": user_info.user_name,
                "id": user_info.user_id,
                "email": user_info.email,
                "picture": user_info.picture
            }
            user_list.append(user_detail)
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = {"total": len(user_list),
                        "user_list": user_list}
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")

      
@require_http_methods(['GET'])
@check_login()
def get_meeting_minutes(request, space_key):
    """
        return all the meeting minutes titles and links from the specific confluence space
        step1: get the space_key
        step2: find all the minutes which have the same space key
        step3: return the titles and links
    """
    # user = request.session.get('user')
    # username = user['atl_username']
    # password = user['atl_password']
    key = space_key
    try:
        # find all the meeting minutes which have the specific space key
        meeting_minutes = MeetingMinutes.objects.filter(space_key=key)
        data = []
        for meeting in meeting_minutes:
            data.append({
                'title': meeting.meeting_title,
                'link': meeting.meeting_link
            })
        resp = init_http_response(
        RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")  
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")

      
@require_http_methods(['GET'])
@check_login()
def get_page_count_by_time(request, space_key):
    """Get a list of time, page count pairs.
    From this space is created, to the date this method is called, one a daily basis.
    Method: GET
    Request: space_key
    """
    try:
        data = []
        for page_history in PageHistory.objects.filter(space_key=space_key):
            history = {
                "time": page_history.date,
                "page_count": page_history.page_count
            }
            data.append(history)

        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['GET'])
@check_login()
def get_imported_project(request):
    """
    get the imported projects
    Method: GET
    Request: coordinator_id
    Return: status code, message, list of project space keys and space names
    """
    # user = request.session.get('user')
    # username = user['atl_username']
    # password = user['atl_password']
    username = config.atl_username
    password = config.atl_password
    coordinator_id = request.session.get('coordinator_id')

    try:
        confluence = log_into_confluence(username, password)
        data = []
        # get all the space keys from DB where coordinator_id = given id
        for project in ProjectCoordinatorRelation.objects.filter(coordinator_id=coordinator_id):
            space_key = project.space_key
            space = confluence.get_space(space_key)
            space_name = space['name']
            data.append({
                'space_key': space_key,
                'space_name': space_name
            })
        resp = init_http_response(
            RespCode.success.value.key, RespCode.success.value.msg)
        resp['data'] = data
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")


@require_http_methods(['POST'])
@check_login()
def delete_project(request, *args, **kwargs):
    try:
        # delete space key that is imported by the coordinator.
        space_key = json.loads(request.body)["space_key"]
        coordinator_id = request.session['coordinator_id']
        ProjectCoordinatorRelation.objects.filter(coordinator_id=coordinator_id, space_key=space_key).delete()
        resp = {'code': RespCode.success.value.key, 'msg': RespCode.success.value.msg}
        return HttpResponse(json.dumps(resp), content_type="application/json")
    except:
        resp = {'code': -1, 'msg': 'error'}
        return HttpResponse(json.dumps(resp), content_type="application/json")