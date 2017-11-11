from slackbot.bot import respond_to
import requests
import Image

from ..botmessage import botsend, botwebapi

HELP = """
"""


@respond_to('^lgtms+create\s+(\S+)')
def lgtm_create(message, imageurl):
    try:
        requests.get(imageurl)
    except:
        botsend(message, '正しい画像URLを指定してください')
        return
