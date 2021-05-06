from django.shortcuts import render
from .models import MeetingMinutes
from django.http import HttpResponse
import json
import urllib3

from ..api.views.confluence.confluence import log_into_confluence
from ..common.choices import RespCode
from ..common.utils import init_http_response
from TeamSPBackend.common import utils
from TeamSPBackend.coordinator.models import Coordinator
from TeamSPBackend.project.models import ProjectCoordinatorRelation
from TeamSPBackend.confluence.models import PageHistory
from TeamSPBackend.common import utils
from TeamSPBackend.api.views.confluence import confluence
from datetime import datetime
import time

from TeamSPBackend.coordinator.models import Coordinator
from TeamSPBackend.project.models import ProjectCoordinatorRelation
from django.db import transaction
# Create your views here.


from TeamSPBackend.confluence.models import UserList
from TeamSPBackend.common import utils
from TeamSPBackend.api.views.confluence import confluence
from TeamSPBackend.coordinator.models import Coordinator
from TeamSPBackend.project.models import ProjectCoordinatorRelation
from django.db import transaction


def update_user_list():
    user_list = []
    for coordinator in Coordinator.objects.all():
        atl_username = coordinator.atl_username
        atl_password = coordinator.atl_password
        for space in ProjectCoordinatorRelation.objects.filter(coordinator_id = coordinator.id):
            space_key = space.space_key
            # assume other than the students, the coordinator is the only one who can read/update this space.
            conf = confluence.log_into_confluence(atl_username, atl_password)
            user_set = {atl_username, }
            group_set = set()
            permissions = conf.get_space_permissions(space_key)
            for permission in permissions:
                for detail in permission["spacePermissions"]:
                    user = detail["userName"]
                    group = detail["groupName"]
                    if user is not None and user not in user_set:
                        user_info = conf.get_user_details_by_username(user)
                        user_list.append(get_user(user_info, space_key))
                        user_set.add(user)
                    if group is not None and group not in group_set:
                        group_set.add(group)
                        # TODO: while there is more to get...
                        members = conf.get_group_members(group)
                        for member in members:
                            if member["username"] not in user_set:
                                user_set.add(member["username"])
                                user_list.append(get_user(member, space_key))

    with transaction.atomic():
        UserList.objects.all().delete()
        UserList.objects.bulk_create(user_list)


def get_user(user, space_key):
    u = UserList(user_id=user["username"],
                 user_name=user["displayName"],
                 email=user["username"] + "@student.unimelb.edu.au",
                 picture="https://confluence.cis.unimelb.edu.au:8443" + user["profilePicture"]["path"],
                 space_key=space_key)
    return u


utils.start_schedule(update_user_list, 60 * 60 * 24)  # update user list on a daily basis
            

def update_meeting_minutes():
    """
    update the meeting_minutes table in DB regularly
    clear all the data in the table first
    then add all the data one by one
    """
    # two for loop still required before running the under codes:
    # one for select all the coodinators and get their username password
    # the other one is for select all the spaces related the the current coodinators and get the space_key
    urllib3.disable_warnings()    # Since ssl is set to False, ignore the warning
    # delete all the data in the meeting_minutes table
    MeetingMinutes.objects.all().delete()
    # select each coordinator data in Coordinator table
    for coordinator in Coordinator.objects.all():
        username = Coordinator.objects.get(id=coordinator.id).atl_username
        password = Coordinator.objects.get(id=coordinator.id).atl_password
        confluence = log_into_confluence(username, password)
        # select each project which coordinator can see
        for project in ProjectCoordinatorRelation.objects.filter(coordinator_id=coordinator.id):
            all_pages = confluence.get_all_pages_from_space(project.space_key, start=0, limit=999999)
            count = 0  # meeting_id
        # for page in all_pages:
        #     page_title = page['title']
        #     page_title_lower = page_title.lower()
        #
        #     page_link_webui = page['_links']['webui']
        #     # each meeting minutes url
        #     page_link = 'https://confluence.cis.unimelb.edu.au:8443/' + page_link_webui
        #
        #     # if the page title contains "meeting", add it into the DB
        #     if "meeting" in page_title_lower:
        #         count += 1
        #         meet = MeetingMinutes(meeting_id=count, meeting_title=page_title, meeting_link=page_link, space_key=space_key)
        #         meet.save()

            # another way to get all the meeting pages exclude the parent page
            for page in all_pages:
                page_id = page['id']
                # get all its child pages
                child = confluence.get_page_child_by_type(page_id)
                # if it does not have any child page, it is the page we want
                if len(child) == 0:
                    page_title = page['title']
                    page_title_lower = page_title.lower()
                    page_link_webui = page['_links']['webui']
                    # each meeting minutes url
                    page_link = 'https://confluence.cis.unimelb.edu.au:8443/' + page_link_webui
                    if 'meeting' in page_title_lower:
                        count += 1
                        meet = MeetingMinutes(meeting_id=count, meeting_title=page_title, meeting_link=page_link,
                                              space_key=project.space_key)
                        meet.save()

utils.start_schedule(update_meeting_minutes, 60 * 60 * 24)  # update user list on a daily basis



def update_page_history():
    history_data = []
    for coordinator in Coordinator.objects.all():
        atl_username = coordinator.atl_username
        atl_password = coordinator.atl_password
        for space in ProjectCoordinatorRelation.objects.filter(coordinator_id = coordinator.id):
            space_key = space.space_key
            conf = confluence.log_into_confluence(atl_username, atl_password)
            contents = conf.get_space_content(space_key=space_key, content_type="page", expand="history")
            results = contents["results"]
            # while there exists incoming results, keep getting space contents
            while contents["size"] == contents["limit"]:
                contents = conf.get_space_content(space_key=space_key, start=len(results),
                                                  content_type="page", expand="history")
                results.extend(contents["results"])

            delta_page_count = {}
            days = []
            for result in results:
                # example: "2021-02-26T10:34:27.631+11:00"
                time_str = result["history"]["createdDate"]
                # from timestamp: take date, ignore time, while keep the time zone
                time_str = time_str[:11]+"00:00:00.001"+time_str[-6:]
                # convert timestamp string to unix timestamp
                page_create_time = int(time.mktime(datetime.fromisoformat(time_str).timetuple()))
                if page_create_time in delta_page_count:
                    delta_page_count[page_create_time] += 1
                else:
                    delta_page_count[page_create_time] = 1
                    days.append(page_create_time)

            days.sort()
            page_count = 0
            cur_time = int(time.mktime(datetime.now().timetuple()))
            for day in range(days[0], cur_time, 60*60*24):
                if day in delta_page_count:
                    page_count += delta_page_count[day]
                history = PageHistory(date=day, page_count=page_count, space_key=space_key)
                history_data.append(history)

    with transaction.atomic():
        PageHistory.objects.all().delete()
        PageHistory.objects.bulk_create(history_data)


utils.start_schedule(update_page_history, 60 * 60 * 24)


