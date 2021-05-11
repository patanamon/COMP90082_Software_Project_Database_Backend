from django.apps import AppConfig

class AutoConfig(AppConfig):
    name = 'jira'
    def ready(self):
        from TeamSPBackend.api.views.jira.jira import auto_get_ticket_count_team_timestamped
        from django.http import HttpRequest
        request = HttpRequest()
        request.method = 'GET'
        request.META['SERVER_NAME'] = '127.0.0.1:8000'
        auto_get_ticket_count_team_timestamped(request)