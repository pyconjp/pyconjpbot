import re
from urllib.request import quote, unquote
from random import choice

from bs4 import BeautifulSoup
import requests
from slackbot.bot import respond_to

from ..botmessage import botsend, botwebapi


AGENTS = ("Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36",
          "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36",
          "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.0 Safari/537.36",
          )


@respond_to(r'google\s+(.*)')
def google(message, keywords):
    """
    google で検索した結果を返す
    """

    if keywords == 'help':
        return

    # 検索を実行して結果を取得
    query = quote(keywords)
    url = f"https://google.com/search?q={query}"
    headers = {'user-agent': choice(AGENTS)}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    answer = soup.find("h3")
    if not answer:
        botsend(message, f"`{keywords}` での検索結果はありませんでした")

    try:
        # 検索結果からURLとテキストを取得して返す
        text = answer.text
        href = answer.parent['href']
        href = href.replace('/url?q=', '')
        href = href.split('&', 1)[0]
        botsend(message, f"{text} {unquote(href)}")
    except IndexError:
        # in this case there is a first answer without a link, which is a
        # google response! Let's grab it and display it to the user.
        return ' '.join(answer[0].stripped_strings)


def unescape(url):
    """
    for unclear reasons, google replaces url escapes with \\x escapes
    """
    return url.replace(r"\x", "%")


@respond_to(r'image\s+(.*)')
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
        botsend(message, choice(images))
    else:
        botsend(message, "`{}` での検索結果はありませんでした".format(keywords))


@respond_to(r'map\s+(.*)')
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

    botsend(message, url)
    attachments = [{
        'pretext': '<http://maps.google.com/maps?q={}|大きい地図で見る>'.format(query),
        'mrkdwn_in': ["pretext"],
    }]
    botwebapi(message, attachments)


@respond_to(r'google\s+help$')
def google_help(message):
    botsend(message, '''- `$google keywords`: 指定したキーワードでgoogle検索した結果を返す
- `$image keywords`: 指定したキーワードでgoogle画像検索した結果からランダムに返す
- `$map keywords`: 指定したキーワードでgoogleマップの検索結果を返す''')
