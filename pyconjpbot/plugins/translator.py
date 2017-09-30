import xml.etree.ElementTree as ET

from slackbot import settings
from slackbot.bot import respond_to

import requests
from langdetect import detect

from ..botmessage import botsend

# Microsoft Translator API の BASE URL
API_BASE_URL = 'https://api.microsofttranslator.com/V2/Http.svc/'


@respond_to('^(translate|翻訳)(\s+-[-\w]+)?\s+(.*)')
def translate(message, cmd, option, text):
    """
    指定した文字列を翻訳する

    http://docs.microsofttranslator.com/text-translate.html#!/default/get_Translate
    """
    if text in ('help', 'list'):
        return

    lang = 'ja'
    if option:
        # 指定した言語に翻訳する
        _, lang = option.split('-', 1)
    elif detect(text) in ('ja', 'ko'):
        # 漢字が多いと日本語なのに ko と判定される
        # 日本語の場合は英語に翻訳する
        lang = 'en'

    url = API_BASE_URL + 'Translate'
    headers = {
        'Ocp-Apim-Subscription-Key': settings.TRANSLATOR_API_KEY,
    }
    query = {
        'to': lang,
        'text': text,
    }
    r = requests.get(url, headers=headers, params=query)

    if r.status_code == 400:
        # エラーが発生したので内容を表示する
        error_message = r.text
        if "Message: 'to' must be a valid language" in error_message:
            botsend(message, '`{}` は無効な言語です'.format(lang))
        else:
            botsend(message, 'エラーが発生しました\n```\n{}\n```'.format(r.text))
        return

    tree = ET.fromstring(r.text)
    botsend(message, tree.text)


@respond_to('^(translate|翻訳)\s+(list|リスト)')
def translate_list(message, cmd, option):
    """
    使用できる言語の一覧を返す

    http://docs.microsofttranslator.com/text-translate.html#!/default/post_GetLanguageNames
    """
    url = API_BASE_URL + 'GetLanguagesForTranslate'
    headers = {
        'Ocp-Apim-Subscription-Key': settings.TRANSLATOR_API_KEY,
    }
    r = requests.get(url, headers=headers)
    # 言語の一覧を取得
    tree = ET.fromstring(r.text)
    langs = sorted(child.text for child in tree)
    reply = ' '.join(('`{}`'.format(l) for l in langs))
    botsend(message, '使用できる言語: {}'.format(reply))


@respond_to('^(translate|翻訳)\s+help')
def translate_help(message, cmd):
    botsend(message, '''`$translate python`, `$翻訳 python`: 指定した文字列を日本語に翻訳
`$translate へび`, `$翻訳 蛇`: 指定した文字列を英語に翻訳
`$translate -ru へび` `$翻訳 -ru へび`: 指定した言語(ru等)に翻訳
`$translate list` `$翻訳 リスト`: 使用できる言語の一覧を返す
''')

