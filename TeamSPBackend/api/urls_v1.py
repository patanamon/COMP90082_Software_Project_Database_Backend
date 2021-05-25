# -*- coding: utf-8 -*-

from django.urls import path

from TeamSPBackend.api.views.confluence import confluence
from TeamSPBackend.api.views.confluence import page_contributions
from TeamSPBackend.api.views.jira import jira
from .views.invitation import invitation_router, invite_accept
from .views.account import account_router, login, logout, update_account, delete, atl_login, supervisor_router
from .views.subject import subject_router, update_subject, delete_subject
from .views.team import team_router, get_team_members, team_member_configure, team_configure
from .views.slack import get_team_data, get_all_member_data, get_member_data
from TeamSPBackend.api.views.project.project import import_project,login_sso
from .views.git import get_git_commits, get_git_pr, get_git_individual_commits, get_git_metrics


urlpatterns = [
    # Project Related API
    path('project/import',import_project),
    path('project/delete', confluence.delete_project),

    # Invitation Related API
    path('invite', invitation_router),
    path('invite/accept', invite_accept),

    # Account Related API
    path('account/login', login),
    path('account/atlassian/login', atl_login),
    path('account/logout', logout),
    path('account/update', update_account),
    path('account/delete', delete),
    path('account', account_router),

    # Supervisor Related API
    path('supervisor/<int:id>', supervisor_router),
    path('supervisor', supervisor_router),

    # Subject Related API
    path('subject/<int:id>/update', update_subject),
    path('subject/<int:id>/delete', delete_subject),
    path('subject/<int:id>', subject_router),
    path('subject', subject_router),

    # Team Related API
    path('team', team_router),
    # path('team/<int:id>', team_router),
    path('team/<int:id>/members', get_team_members),
    path('team/<int:team_id>/members/<int:team_member_id>', team_member_configure),
    path('team/<int:team_id>/configuration', team_configure),
    path('team/<space_key>', confluence.get_user_list),

    # Git Related API
    path('git/<space_key>/commit_count', get_git_commits),
    path('git/individual_commits/<space_key>', get_git_individual_commits),
    path('git/metrics/<space_key>', get_git_metrics),
    path('git/pullrequest', get_git_pr),

    # Confluence Related API
    # path('confluence/spaces/<space_key>', confluence.get_space),
    path('confluence/spaces/<space_key>/pages', confluence.get_pages_of_space),
    path('confluence/spaces/<space_key>/pages/contributions',
         page_contributions.get_all_page_contributions),
    path('confluence/spaces/<space_key>/pages/<int:page_id>',
         confluence.get_page_contributors),
    path('confluence/groups', confluence.get_all_groups),
    path('confluence/groups/searchteam/<keyword>', confluence.search_team),
    path('confluence/groups/<group>/members', confluence.get_group_members),
    path('confluence/users/<member>', confluence.get_user_details),
    path('subject/<subjectcode>/<year>/supervisors',
         confluence.get_subject_supervisors),
    # COMP90082 21 S1 sprint1
    path('confluence/spaces/<key_word>', confluence.get_spaces_by_key),
    path('confluence/<space_key>/meeting_minutes', confluence.get_meeting_minutes),

    path('confluence/imported_projects', confluence.get_imported_project),

    path('confluence/spaces/<space_key>/page_count', confluence.get_page_count_by_time),

    path('sso/login', login_sso),

    # Jira Related API
    # legacy
    path('jira/<team>/tickets/<student>', jira.get_issues_individual),
    path('jira/<team>/tickets', jira.get_issues_team),
    path('jira/<team>/comments/<student>', jira.get_comment_count_individual),
    path('jira/<team>/sprint_dates', jira.get_sprints_dates),
    path('jira/<team>/issues_per_sprint', jira.get_issues_per_sprint),

    # new
    path('jira/<team>/ticket_count', jira.get_ticket_count_from_db),
    path('jira/<team>/contributions', jira.get_contributions_from_db),
    path('git/config', jira.setGithubJiraUrl),


    # legacy but not working
    #path('jira/<team>/jira_cfd', jira.get_jira_cfd),
    #path('jira/<team>/jiraburn', helpJira.get_jira_burn),
    #path('jira/<team>/jiraburnforecast', helpJira.get_jira_burn_forecast),

    # Slack Related API
    # path('slack', slack_router),
    path('slack/<int:id>', get_team_data),
    path('slack/<int:id>/member', get_all_member_data),
    path('slack/<int:team_id>/member/<int:student_id>', get_member_data),
]


