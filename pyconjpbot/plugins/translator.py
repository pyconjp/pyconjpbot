import json

import requests
from langdetect import detect
from slackbot import settings
from slackbot.bot import respond_to
from slackbot.dispatcher import Message

from ..botmessage import botsend

# Microsoft Translator API の BASE URL
API_BASE_URL = "https://api-apc.cognitive.microsofttranslator.com/"


@respond_to(r"^(translate|翻訳)(\s+-[-\w]+)?\s+(.*)")
def translate(message: Message, cmd: str, option: str, text: str) -> None:
    """
    指定した文字列を翻訳する

    https://docs.microsoft.com/en-us/azure/cognitive-services/translator/reference/v3-0-translate
    """
    if text in ("help", "list"):
        return

    lang = "ja"
    if option:
        # 指定した言語に翻訳する
        _, lang = option.split("-", 1)
    elif detect(text) in ("ja", "ko"):
        # 漢字が多いと日本語なのに ko と判定される
        # 日本語の場合は英語に翻訳する
        lang = "en"

    url = API_BASE_URL + "translate"
    headers = {
        "Ocp-Apim-Subscription-Key": settings.TRANSLATOR_API_KEY,
        "Content-Type": "application/json",
    }
    params = {
        "api-version": "3.0",
        "to": lang,
    }
    payload = [{"Text": text}]
    r = requests.post(url, headers=headers, params=params, data=json.dumps(payload))

    if r.status_code == 400:
        # エラーが発生したので内容を表示する
        error_message = r.text
        if "Message: 'to' must be a valid language" in error_message:
            botsend(message, f"`{lang}` は無効な言語です")
        else:
            botsend(message, f"エラーが発生しました\n```\n{r.text}\n```")
        return

    data = r.json()
    translated_text = data[0]["translations"][0]["text"]
    botsend(message, translated_text)


@respond_to(r"^(translate|翻訳)\s+(list|リスト)")
def translate_list(message: Message, cmd: str, option: str) -> None:
    """
    使用できる言語の一覧を返す

    https://docs.microsoft.com/en-us/azure/cognitive-services/translator/reference/v3-0-languages
    """
    url = API_BASE_URL + "languages"
    params = {
        "api-version": "3.0",
        "scope": "translation",
    }
    r = requests.get(url, params=params)
    # 言語の一覧を取得
    data = r.json()
    reply = " ".join((f"`{lang}`" for lang in data["translation"].keys()))
    botsend(message, f"使用できる言語: {reply}")


@respond_to(r"^(translate|翻訳)\s+help")
def translate_help(message: Message, cmd: str) -> None:
    botsend(
        message,
        """`$translate python`, `$翻訳 python`: 指定した文字列を日本語に翻訳
`$translate へび`, `$翻訳 蛇`: 指定した文字列を英語に翻訳
`$translate -ru へび` `$翻訳 -ru へび`: 指定した言語(ru等)に翻訳
`$translate list` `$翻訳 リスト`: 使用できる言語の一覧を返す
""",
    )
