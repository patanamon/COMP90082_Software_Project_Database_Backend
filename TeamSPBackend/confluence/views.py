from django.shortcuts import render

# Create your views here.
from TeamSPBackend.confluence.models import PageHistory
from TeamSPBackend.common import utils
from TeamSPBackend.api.views.confluence import confluence
from datetime import datetime
import time


def update_page_history():
    PageHistory.objects.all().delete()
    # for all coordinators, get their username and password
    # for all space keys imported by the user
    for space_key, atl_username, atl_password in []:
        conf = confluence.log_into_confluence(atl_username, atl_password)
        contents = conf.get_space_content(space_key=space_key, content_type="page", expand="history")
        results = contents["results"]
        while contents["size"] == contents["limit"]:
            contents = conf.get_space_content(space_key=space_key, start=len(results), content_type="page", expand="history")
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
            history.save()


utils.start_schedule(update_page_history, 60 * 60 * 24)