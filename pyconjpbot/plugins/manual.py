from urllib.parse import quote_plus

from slackbot.bot import respond_to

from ..botmessage import botsend

# マニュアルのURL
URL = "http://manual.pycon.jp/"


@respond_to(r"^manual$")
def manual(message):
    """
    マニュアルのURLを返す
    """
    botsend(message, f"PyCon JP 運営マニュアル {URL}")


@respond_to(r"^manual\s+(.*)")
def manual_search(message, query):
    """
    マニュアルをキーワード検索したURLを返す
    """
    if query != "help":
        botsend(message, f"{URL}search.html?q={quote_plus(query)}")


@respond_to(r"^manual\s+help$")
def manual_help(message):
    """
    マニュアルコマンドのヘルプを返す
    """
    botsend(
        message,
        """- `$manual`: マニュアルのURLを返す
- `$manual keywords`: マニュアルを指定キーワード検索する""",
    )
