from django.shortcuts import render

# Create your views here.

from TeamSPBackend.confluence.models import UserList
from TeamSPBackend.common import utils
from TeamSPBackend.api.views.confluence import confluence


def update_user_list():
    """
    First remove all user list, then add them one by one.
    """
    UserList.objects.all().delete()
    # TODO: get all space keys, atl usernames and passwords
    # use all_entries = Entry.objects.all()
    # get coordinator-space list for all space_keys and the coordinator imports them
    # get atl_username, atl_password of coordinators
    for space_key, atl_username, atl_password in []:
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
                    insert_user(user_info, space_key)
                    user_set.add(user)
                if group is not None and group not in group_set:
                    group_set.add(group)
                    members = conf.get_group_members(group)
                    for member in members:
                        if member["username"] not in user_set:
                            user_set.add(member["username"])
                            insert_user(member, space_key)


def insert_user(user, space_key):
    u = UserList(user_id=user["username"],
                 user_name=user["displayName"],
                 email=user["username"] + "@student.unimelb.edu.au",
                 picture="https://confluence.cis.unimelb.edu.au:8443" + user["profilePicture"]["path"],
                 space_key=space_key)
    u.save()


utils.start_schedule(update_user_list, 60 * 60 * 24)  # update user list on a daily basis
