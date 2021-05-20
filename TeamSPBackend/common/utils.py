# -*- coding: utf-8 -*-

import base64
from threading import Timer
import datetime

from functools import wraps
from Crypto.Cipher import AES

from django.http.response import HttpResponse

from TeamSPBackend.common import *
from TeamSPBackend.common.choices import RespCode, MyEnum
from TeamSPBackend.common.config import SESSION_REFRESH, HOMEPAGE, REGISTER_PAGE, INVITATION_KEY, SALT


logger = logging.getLogger('django')


def make_json_response(func=HttpResponse, resp=None):
    return func(ujson.dumps(resp), content_type='application/json')


def make_redirect_response(func=HttpResponse, resp=None):
    return func(ujson.dumps(resp), content_type='application/json', status=302)


def init_http_response(code, message, data=None):
    return dict(
        code=code,
        message=message,
        data=data,
    )

def init_http_response_withoutdata(code, message):
    return dict(
        code=code,
        message=message
    )

def init_http_response_my_enum(resp: MyEnum, data=None):
    return init_http_response(resp.key, resp.msg, data)


def check_body(func):
    """

    :param func:
    :return:
    """
    def wrapper(request, *args, **kwargs):

        try:
            body = dict(ujson.loads(request.body))
            logger.info(body)
        except ValueError or json.JSONDecodeError as e:
            logger.info(request.body)
            resp = init_http_response(RespCode.incorrect_body.value.key, RespCode.incorrect_body.value.msg)
            return make_json_response(HttpResponse, resp)

        return func(request, body, *args, **kwargs)
    return wrapper


def check_user_login(roles=None):
    """
    Disable for testing
    :param roles:
    :return:
    """
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            user = request.session.get('user', {})
            if not user or 'id' not in user or 'is_login' not in user:
                resp = init_http_response(RespCode.not_logged.value.key, RespCode.not_logged.value.msg)
                return make_json_response(HttpResponse, resp)

            if roles is not None:
                if not isinstance(roles, list):
                    raise ValueError('check_user_login: incorrect roles')
                if user['role'] not in roles:
                    logger.info('permission deny %s', func)
                    resp = init_http_response(RespCode.permission_deny.value.key, RespCode.permission_deny.value.msg)
                    return make_json_response(HttpResponse, resp)

            request.session.set_expiry(SESSION_REFRESH)
            # print('{} {} {}'.format(request, args, kwargs))
            return func(request, *args, **kwargs)
        return inner
    return decorator


def check_login():
    """
    Disable for testing
    :return:
    """
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if 'coordinator_id' not in request.session or 'coordinator_name' not in request.session:
                resp = init_http_response(RespCode.not_logged.value.key, RespCode.not_logged.value.msg)
                return make_json_response(HttpResponse, resp)

            request.session.set_expiry(SESSION_REFRESH)
            return func(request, *args, **kwargs)
        return inner
    return decorator


def check_user_role(func, role):
    """
    Disable for testing
    :param func:
    :return:
    """
    def wrapper(request, *args, **kwargs):
        user = request.session.get('user', {})
        user_role = user['role']
        if user_role is not role:
            resp = init_http_response(RespCode.permission_deny.value.key, RespCode.permission_deny.value.msg)
            return make_json_response(HttpResponse, resp)

        return func(request, args, kwargs)
    return wrapper


def body_extract(body: dict, obj: object):
    """
    Extract parameters from the request body
    :param body:
    :param obj:
    :return:
    """
    for i in obj.__dict__.keys():
        if i in body:
            obj.__setattr__(i, body.get(i))


def mills_timestamp():
    return int(time.time() * 1000)


def email_validate(email):
    return re.match(r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$', email)


def get_invitation_link(key):
    return HOMEPAGE + REGISTER_PAGE + '?' + INVITATION_KEY + '=' + key


def auto_fill(key):
    if not isinstance(key, str):
        return None
    while len(key) % 16 != 0:
        key += '\0'
    return str.encode(key)


def decrypt_aes(key):
    if key is None:
        return None
    aes = AES.new(auto_fill(SALT), AES.MODE_ECB)
    return str(aes.decrypt(base64.decodebytes(key))).rstrip('\0')

def start_schedule(func, interval, *args):
    """
    Run function regularly at the given interval.
    For example, start_schedule(print, 3, "hello world") will print "hello world" every 3 seconds
    :param func: the function/method need to be run on a regular basis
    :param interval: the time interval to run function, in seconds
    :param args: arguments of this function, is optional if no argument is needed.
    """
    Timer(0, func, args).start()
    Timer(interval, start_schedule, args=[func, interval, *args]).start()

def transformTimestamp(timestamp):
    y = time.localtime(timestamp).tm_year
    m = time.localtime(timestamp).tm_mon
    d = time.localtime(timestamp).tm_mday
    s = str(datetime.date(y, m, d))
    timeArray = time.strptime(s, "%Y-%m-%d")
    timeStamp = int(time.mktime(timeArray)) + 24 * 60 * 60 - 1
    # Unified the date to 23:59:59 of the day
    return timeStamp

