from django.shortcuts import render
from .models import MeetingMinutes
from django.http import HttpResponse
import json
import urllib3

from ..api.views.confluence.confluence import log_into_confluence
from ..common.choices import RespCode
from ..common.utils import init_http_response
from TeamSPBackend.common import utils
# Create your views here.


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
    username = ''  # now it is the hard code, needs to changed later
    password = ''   # now it is the hard code, needs to changed later
    space_key = ''   # now it is the hard code, needs to changed later
    # delete all the data in the meeting_minutes table
    MeetingMinutes.objects.all().delete()
    confluence = log_into_confluence(username, password)
    all_pages = confluence.get_all_pages_from_space(space_key, start=0, limit=999999)
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
                                      space_key=space_key)
                meet.save()

utils.start_schedule(update_meeting_minutes, 60 * 60 * 24)  # update user list on a daily basis
