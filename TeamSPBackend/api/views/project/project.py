from django.views.decorators.http import require_http_methods
from TeamSPBackend.common.utils import check_body, \
    body_extract
from TeamSPBackend.api.dto.dto import ProjectDTO
from TeamSPBackend.project.views import import_projects_into_coordinator


@require_http_methods(['POST'])
@check_body
def import_project_in_batch(request, body, *args, **kwargs):
    # Method: POST
    project_dto = ProjectDTO()
    body_extract(body, project_dto)
    coordinator = project_dto.coordinator
    project_list = project_dto.project_list
    return import_projects_into_coordinator(coordinator, project_list)
