import re
import json
from urllib.request import quote, unquote
from random import choice

from bs4 import BeautifulSoup
import requests
from slackbot.bot import respond_to

@respond_to('google\s+(.*)')
def google(message, keywords):
    """
    google で検索した結果を返す

    https://github.com/llimllib/limbo/blob/master/limbo/plugins/google.py
    """

    if keywords == 'help':
        return
    
    query = quote(keywords)
    url = "https://encrypted.google.com/search?q={0}".format(query)
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    answer = soup.findAll("h3", attrs={"class": "r"})
    if not answer:
        message.send("`{}` での検索結果はありませんでした".format(keywords))

    try:
        _, url = answer[0].a['href'].split('=', 1)
        url, _ = url.split('&', 1)
        message.send(unquote(url))
    except IndexError:
        # in this case there is a first answer without a link, which is a
        # google response! Let's grab it and display it to the user.
        return ' '.join(answer[0].stripped_strings)

def unescape(url):
    """
    for unclear reasons, google replaces url escapes with \\x escapes
    """
    return url.replace(r"\x", "%")

@respond_to('image\s+(.*)')
def google_image(message, keywords):
    """
    google で画像検索した結果を返す

    https://github.com/llimllib/limbo/blob/master/limbo/plugins/image.py
    """

    query = quote(keywords)
    searchurl = "https://www.google.com/search?tbm=isch&q={0}".format(query)

    # this is an old iphone user agent. Seems to make google return good results.
    useragent = "Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Versio  n/4.0.5 Mobile/8A293 Safari/6531.22.7"

    result = requests.get(searchurl, headers={"User-agent": useragent}).text
    images = list(map(unescape, re.findall(r"var u='(.*?)'", result)))

    if images:
        message.send(choice(images))
    else:
        message.send("`{}` での検索結果はありませんでした".format(keywords))

@respond_to('map\s+(.*)')
def google_map(message, keywords):
    """
    google マップで検索した結果を返す

    https://github.com/llimllib/limbo/blob/master/limbo/plugins/map.py
    """
    query = quote(keywords)

    # Slack seems to ignore the size param
    #
    # To get google to auto-reasonably-zoom its map, you have to use a marker
    # instead of using a "center" parameter. I found that setting it to tiny
    # and grey makes it the least visible.
    url = "https://maps.googleapis.com/maps/api/staticmap?size=800x400&markers={0}&maptype={1}"
    url = url.format(query, 'roadmap')

    message.send(url)
    attachments = [{
        'pretext': '<http://maps.google.com/maps?q={}|大きい地図で見る>'.format(query),
        'mrkdwn_in': ["pretext"],
    }]
    message.send_webapi('', json.dumps(attachments))

@respond_to('google\s+help$')
def google_help(message):
    message.send('''- `$google keywords`: 指定したキーワードでgoogle検索した結果を返す
- `$image keywords`: 指定したキーワードでgoogle画像検索した結果からランダムに返す
- `$map keywords`: 指定したキーワードでgoogleマップの検索結果を返す''')
