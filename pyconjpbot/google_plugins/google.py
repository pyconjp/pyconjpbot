from urllib.request import quote, unquote

import requests
from bs4 import BeautifulSoup
from slackbot.bot import respond_to

from ..botmessage import botsend


@respond_to(r"google\s+(.*)")
def google(message, keywords):
    """
    google で検索した結果を返す
    """

    if keywords == "help":
        return

    # 検索を実行して結果を取得
    query = quote(keywords)
    url = f"https://google.com/search?q={query}"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    answer = soup.find("h3")
    if not answer:
        botsend(message, f"`{keywords}` での検索結果はありませんでした")

    try:
        # 検索結果からURLとテキストを取得して返す
        text = answer.text
        href = answer.parent["href"]
        href = href.replace("/url?q=", "")
        href = href.split("&", 1)[0]
        botsend(message, f"{text} {unquote(href)}")
    except IndexError:
        botsend(message, f"`{keywords}` での検索結果はありませんでした")
    except KeyError:
        botsend(message, f"`{keywords}` での検索結果はありませんでした")


def unescape(url):
    """
    for unclear reasons, google replaces url escapes with \\x escapes
    """
    return url.replace(r"\x", "%")


@respond_to(r"image\s+(.*)")
def google_image(message, keywords):
    """
    google で画像検索した結果を返す

    https://github.com/llimllib/limbo/blob/master/limbo/plugins/image.py
    """

    query = quote(keywords)
    url = f"https://www.google.com/search?q={query}&source=lnms&tbm=isch"

    # this is an old iphone user agent. Seems to make google return good results.
    useragent = (
        "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/43.0.2357.134 Safari/537.36"
    )
    r = requests.get(url, headers={"User-agent": useragent})
    soup = BeautifulSoup(r.text, "html.parser")
    images = soup.find_all("img")[1:]

    if images:
        image = images[0]
        botsend(message, image["src"])
    else:
        botsend(message, f"`{keywords}` での検索結果はありませんでした")


@respond_to(r"google\s+help$")
def google_help(message):
    botsend(
        message,
        """- `$google keywords`: 指定したキーワードでgoogle検索した結果を返す
- `$image keywords`: 指定したキーワードでgoogle画像検索した結果からランダムに返す""",
    )
