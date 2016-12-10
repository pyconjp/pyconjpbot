import pprint

from .googledrive import get_service

import requests
from slackbot.bot import respond_to

SCOPES = 'https://www.googleapis.com/auth/admin.directory.user'
CLIENT_SECRET_FILE = 'gadmin_client_secret.json'
APPLICATION_NAME = 'Directory API Python Quickstart'

# https://developers.google.com/resources/api-libraries/documentation/admin/directory_v1/python/latest/index.html

@respond_to('gadmin (.*)')
def gadmin(message, name):
    service = get_service('admin', 'directory_v1', __file__, SCOPES, CLIENT_SECRET_FILE)
    data = service.users().get(userKey=name + '@pycon.jp').execute()

    pp = pprint.PrettyPrinter(indent=2)
    resp = '```' + pp.pformat(data) + '```'
    message.send(resp)
