from django.shortcuts import render

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
