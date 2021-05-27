import logging

import atlassian
import urllib3
from ..api.views.confluence.confluence import log_into_confluence
from TeamSPBackend.confluence.models import PageHistory, UserList, IndividualConfluenceContribution, MeetingMinutes
from datetime import datetime
import time
from TeamSPBackend.common import utils
from TeamSPBackend.api.views.confluence import confluence
from TeamSPBackend.coordinator.models import Coordinator
from TeamSPBackend.project.models import ProjectCoordinatorRelation
from django.db import transaction
from TeamSPBackend.api import config
from django.conf import settings
import requests


def update_space_user_list(space_key):
    atl_username = config.atl_username
    atl_password = config.atl_password
    conf = confluence.log_into_confluence(atl_username, atl_password)
    user_list = []
    user_set = {atl_username, 'admin'}
    group_set = set()
    GROUP_LIMIT = 30  # this is a limit of user lists, if there is more than 30 users in a space, it is likely to be
    # a public space.
    permissions = conf.get_space_permissions(space_key)
    # notice that if permissions == {}, that means the user don't have the admin permission to the space.
    # simply return the users who have contributed to the space
    for permission in permissions:
        for detail in permission["spacePermissions"]:
            user = detail["userName"]
            group = detail["groupName"]
            if user is not None and user not in user_set:
                try:
                    user_info = conf.get_user_details_by_username(user)
                except atlassian.errors.ApiNotFoundError as e:
                    logger = logging.getLogger('django')
                    logger.error(str(e) + " " + user)
                    continue
                user_list.append(get_user(user_info, space_key))
                user_set.add(user)
            if group is not None and group not in group_set:
                group_set.add(group)
                members = conf.get_group_members(group, limit=GROUP_LIMIT)
                for member in members:
                    if member["username"] not in user_set:
                        user_set.add(member["username"])
                        user_list.append(get_user(member, space_key))
    # if the robot account don't have admin permission, simply return the list of users that made contributions to
    # the space.
    if permissions == {}:
        for contribution in IndividualConfluenceContribution.objects.filter(space_key=space_key):
            if contribution.user_id not in user_set:
                try:
                    user_info = conf.get_user_details_by_username(contribution.user_id)
                except atlassian.errors.ApiNotFoundError as e:
                    logger = logging.getLogger('django')
                    logger.error(str(e) + " " + contribution.user_id)
                    continue
                user_list.append(get_user(user_info, space_key))
                user_set.add(contribution.user_id)
    return user_list


def insert_space_user_list(space_key):
    insert_space_page_contribution(space_key)
    user_list = update_space_user_list(space_key)
    with transaction.atomic():
        UserList.objects.filter(space_key=space_key).delete()
        UserList.objects.bulk_create(user_list)


def update_user_list():
    update_page_contribution()
    user_list = []
    for space_key in get_spaces():
        user_list.extend(update_space_user_list(space_key))

    with transaction.atomic():
        UserList.objects.all().delete()
        UserList.objects.bulk_create(user_list)
        logger = logging.getLogger('django')
        logger.info("Finish update all user list")


def get_user(user, space_key):
    logger = logging.getLogger('django')
    logger.info('insert user ' + user['username'] + ' in the space ' + space_key)
    picture_path = "profile_picture/"
    import re
    url = requests.get("http://txt.go.sohu.com/ip/soip")
    ip = re.findall(r'\d+.\d+.\d+.\d+', url.text)
    host = "http://" + ip[0] + ":18000"
    if user["profilePicture"]["path"].endswith("default.svg"):
        picture_path += "default.svg"
    else:
        picture_path += user["username"]
        download("https://confluence.cis.unimelb.edu.au:8443" + user["profilePicture"]["path"],
                 settings.MEDIA_ROOT + picture_path)
    u = UserList(user_id=user["username"],
                 user_name=user["displayName"],
                 email=user["username"] + "@student.unimelb.edu.au",
                 picture=host + settings.MEDIA_URL + picture_path,
                 space_key=space_key)
    return u


def download(url, file_path):
    r2 = requests.get(url, auth=(config.atl_username, config.atl_password), verify=False)
    with open(file_path, 'wb') as file:
        file.write(r2.content)


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
    atl_username = config.atl_username
    atl_password = config.atl_password
    confluence = log_into_confluence(atl_username, atl_password)
    # select each coordinator data in Coordinator table
    for coordinator in Coordinator.objects.all():
        # select each project which coordinator can see
        for project in ProjectCoordinatorRelation.objects.filter(coordinator_id=coordinator.id):
            all_pages = confluence.get_all_pages_from_space(project.space_key, start=0, limit=999999)
            # get all the meeting pages exclude the parent page
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
                        # it is not in the DB before
                        if len(MeetingMinutes.objects.filter(meeting_title=page_title)) == 0:
                            meet = MeetingMinutes(meeting_title=page_title, meeting_link=page_link,
                                                  space_key=project.space_key)
                            meet.save()


# the meeting minutes will stored in DB as long as project is imported
def insert_space_meeting(space_key):
    conf = log_into_confluence(config.atl_username, config.atl_password)
    all_pages = conf.get_all_pages_from_space(space_key, start=0, limit=999999)
    for page in all_pages:
        page_id = page['id']
        # get all its child pages
        child = conf.get_page_child_by_type(page_id)
        # if it does not have any child page, it is the page we want
        if len(child) == 0:
            page_title = page['title']
            page_title_lower = page_title.lower()
            page_link_webui = page['_links']['webui']
            # each meeting minutes url
            page_link = 'https://confluence.cis.unimelb.edu.au:8443/' + page_link_webui
            if 'meeting' in page_title_lower:
                if len(MeetingMinutes.objects.filter(meeting_title=page_title)) == 0:
                    meet = MeetingMinutes(meeting_title=page_title, meeting_link=page_link,
                                          space_key=space_key)
                    meet.save()

def insert_space_page_history(space_key):
    page_history = update_space_page_history(space_key)
    with transaction.atomic():
        PageHistory.objects.filter(space_key=space_key).delete()
        PageHistory.objects.bulk_create(page_history)


def update_space_page_history(space_key):
    history_data = []
    conf = confluence.log_into_confluence(config.atl_username, config.atl_password)
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

    if len(days) < 1:
        return []

    days.sort()
    page_count = 0
    cur_time = int(time.mktime(datetime.now().timetuple()))
    for day in range(days[0], cur_time, 60*60*24):
        if day in delta_page_count:
            page_count += delta_page_count[day]
        history = PageHistory(date=day, page_count=page_count, space_key=space_key)
        history_data.append(history)
    return history_data


def update_page_history():
    history_data = []
    for space_key in get_spaces():
        history_data.extend(update_space_page_history(space_key))

    with transaction.atomic():
        PageHistory.objects.all().delete()
        PageHistory.objects.bulk_create(history_data)


def update_space_page_contribution(space_key):
    """
    update the individual contributions of confluence pages in a specific space
    """
    atl_username = config.atl_username
    atl_password = config.atl_password
    conf = confluence.log_into_confluence(atl_username, atl_password)
    limit = 100
    contents = conf.get_space_content(space_key=space_key, content_type="page", limit=limit,
                                      expand="history.contributors.publishers.users")
    results = contents["results"]
    # while there exists incoming results, keep getting space contents
    while contents["size"] == contents["limit"]:
        contents = conf.get_space_content(space_key=space_key, start=len(results), limit=limit,
                                          content_type="page", expand="history.contributors.publishers.users")
        results.extend(contents["results"])

    member_contributions = {}
    id_name = {}
    # Loop through every page and store in a dictionary {"page": set of members}
    for page in results:
        page_contributors = page["history"]["contributors"]["publishers"]["users"]
        for user in page_contributors:
            if user['username'] == 'admin':
                continue
            if not user["displayName"] in member_contributions:
                member_contributions[user["displayName"]] = 0
                id_name[user["displayName"]] = user["username"]
            member_contributions[user["displayName"]] += 1

    page_contribution = []
    for user_name in member_contributions:
        page_count = member_contributions[user_name]
        page_contribution.append(IndividualConfluenceContribution(
            space_key=space_key,
            user_id=id_name[user_name],
            user_name=user_name,
            page_count=page_count
        ))

    return page_contribution


def insert_space_page_contribution(space_key):
    page_contribution = update_space_page_contribution(space_key)
    with transaction.atomic():
        IndividualConfluenceContribution.objects.filter(space_key=space_key).delete()
        IndividualConfluenceContribution.objects.bulk_create(page_contribution)


def update_page_contribution():
    page_contribution = []
    for space_key in get_spaces():
        page_contribution.extend(update_space_page_contribution(space_key))

    with transaction.atomic():
        IndividualConfluenceContribution.objects.all().delete()
        IndividualConfluenceContribution.objects.bulk_create(page_contribution)


def get_spaces():
    spaces = set()
    for space in ProjectCoordinatorRelation.objects.all():
        spaces.add(space.space_key)
    return spaces


utils.start_schedule(update_meeting_minutes, 60 * 60 * 24)  # update meeting minutes on a daily basis
utils.start_schedule(update_page_history, 60 * 60 * 24)
utils.start_schedule(update_user_list, 60 * 60 * 24)  # update page contributions and user list on a daily basis

