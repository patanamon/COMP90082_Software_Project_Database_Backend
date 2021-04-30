from atlassian import Confluence
import json
import requests
from requests.auth import HTTPBasicAuth

from TeamSPBackend.common.choices import RespCode
from django.views.decorators.http import require_http_methods
from django.http.response import HttpResponse, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseBadRequest
from TeamSPBackend.common.utils import make_json_response, init_http_response, check_user_login, check_body, \
    body_extract, mills_timestamp
from TeamSPBackend.api.dto.dto import ProjectDTO


def import_projects_into_coordinator(coordinator, project_list):
    print()
# try:

# except:
#     resp = {'code': -1, 'msg': 'error'}
#     return HttpResponse(json.dumps(resp), content_type="application/json")
