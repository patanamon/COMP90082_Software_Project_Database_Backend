from django.shortcuts import render

# Create your views here.

from TeamSPBackend.confluence.models import UserList
from TeamSPBackend.common import utils
from TeamSPBackend.api.views.confluence import confluence


def update_user_list():
    """
    First remove all user list, then add them one by one.
    """
    # TODO: first delete all, then add; get all space keys, atl usernames and passwords
    # all_entries = Entry.objects.all()
    # get coordinator-space list for all space_keys and the coordinator imports them
    # get atl_username, atl_password of coordinators
    for space_key, atl_username, atl_password in []:
        # assume other than the students, the coordinator is the only one who can read/update this space.
        conf = confluence.log_into_confluence(atl_username, atl_password)
        user_set = {atl_username, }
        # by user
        response = conf.get_space_content(space_key, limit=1,
                                          expand='restrictions.update.restrictions.user,'
                                                 'restrictions.update.restrictions.group')
        users = response["page"]["results"][0]["restrictions"]["update"]["restrictions"]["user"]["results"]
        for user in users:
            if user["username"] not in user_set:
                update_user(get_user_detail(user), space_key)
                user_set.add(user["username"])
        # by group
        groups = response["page"]["results"][0]["restrictions"]["update"]["restrictions"]["group"]["results"]
        for group in groups:
            members = conf.get_group_members(group["name"])
            for member in members:
                if member["username"] not in user_set:
                    update_user(get_user_detail(member), space_key)
                    user_set.add(member["username"])


def get_user_detail(user):
    user_info = {
        "name": user["displayName"],
        "id": user["username"],
        "email": user["username"] + "@student.unimelb.edu.au",
        "picture": "https://confluence.cis.unimelb.edu.au:8443" + user["profilePicture"]["path"]
    }
    return user_info


def update_user(user_info, space_key):
    if UserList.objects.filter(user_id=user_info["id"], space_key=space_key).exists():
        user = UserList.objects.get(user_id=user_info["id"], space_key=space_key)
        if user_info["picture"] != user.picture:
            UserList.objects.filter(user_id=user_info["id"], space_key=space_key).update(picture=user_info["picture"])
    else:
        user = UserList(user_id=user_info["id"],
                        user_name=user_info["name"],
                        email=user_info["email"],
                        picture=user_info["picture"],
                        space_key=space_key)
        user.save()


utils.start_schedule(update_user_list, 60 * 60 * 24)  # update user list on a daily basis
