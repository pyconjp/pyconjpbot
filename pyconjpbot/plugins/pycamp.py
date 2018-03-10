import os
from io import StringIO
from datetime import timedelta, datetime
from dateutil import parser

from jira import JIRA, JIRAError
from slackbot import settings
from slackbot.bot import respond_to
from slackbot.utils import create_tmp_file
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageFont, ImageDraw

from ..google_plugins.google_api import get_service
from ..botmessage import botsend, botwebapi

# Clean JIRA Url to not have trailing / if exists
CLEAN_JIRA_URL = settings.JIRA_URL
if settings.JIRA_URL[-1:] == '/':
    CLEAN_JIRA_URL = CLEAN_JIRA_URL[:-1]

# Login to jira
jira_auth = (settings.JIRA_USER, settings.JIRA_PASS)
jira = JIRA(CLEAN_JIRA_URL, basic_auth=jira_auth)

# Python Boot Camp の issue を作成するJIRAのプロジェクトとコンポーネント名
PROJECT = 'ISSHA'
COMPONENT = 'Python Boot Camp'

# JIRA の issue の種類
ISSUE_TYPE_TASK = 3     # タスク
ISSUE_TYPE_SUBTASK = 5  # サブタスク

# コアスタッフの JIRA username
REPORTER = 'takanory'
CORE_STAFFS = ('makoto-kimura', 'takanory', 'ryu22e')

ASSIGNEE_TYPE = {
    '作成者': 'reporter',
    '現地スタッフ': 'local_staff',
    '講師': 'lecturer',
    }

# テンプレートとなるスプレッドシートのID
# https://docs.google.com/spreadsheets/d/1LEtpNewhAFSf_vtkhTsWi6JGs2p-7XHZE8yOshagz0I/edit#gid=1772747731
SHEET_ID = '1LEtpNewhAFSf_vtkhTsWi6JGs2p-7XHZE8yOshagz0I'

# 参加者枠の短い名前
SHORT_PTYPE_NAMES = ('学生', 'TA', 'スタッフ',
                     '本イベント参加者', '懇親会のみ')

# Settings for the logo generation.
MAIN_COLOR = (90, 200, 233)
TEXT_SIZE = 120
TEXT_HEIGHT = 200
FONT = 'RictyDiminished-Regular.ttf'
IMAGES = (
        ('pycamp_logo.png', (1080, 1080)),
        ('pycamp_logo_horizontal.png', (2827, 1080)),
)

HELP = """
`$pycamp create (地域) (開催日) (現地スタッフJIRA) (講師のJIRA)`: pycamp のイベント用issueを作成する
`$pycamp summary`: 開催予定のpycampイベントの概要を返す
`$pycamp summary -party`: 開催予定のpycamp懇親会の概要を返す
`$pycamp logo (地域)`: pycamp のイベント用ロゴを作成する
"""


def create_issue(template, params, parent=None, area=None):
    """
    テンプレートにパラメーターを適用して、JIRA issueを作成する

    :params template:
    :params params:
    :params parent: 親issueのID(ISSHA-XXX)
    :params area: 地域名(東京、大阪など)
    """

    # 担当者情報を作成
    assignee_type = template.get('assignee_type', 'reporter')
    assignee = params[assignee_type]
    # 期限の日付を作成
    delta = timedelta(days=template.get('delta', -7))
    duedate = params['target_date'] + delta

    issue_dict = {
        'project': {'key': PROJECT},
        'components': [{'name': COMPONENT}],
        'summary': template.get('summary', '').format(**params),
        'description': template.get('description', '').format(**params),
        'assignee': {'name': assignee},  # 担当者
        'reporter': {'name': REPORTER},  # 報告者
        'duedate': '{:%Y-%m-%d}'.format(duedate),  # 期限
    }

    if parent:
        # 親issueのサブタスクとして作成
        issue_dict['parent'] = {'key': parent}
        issue_dict['issuetype'] = {'id': ISSUE_TYPE_SUBTASK}

        # サブタスクはタイトルの先頭に "#pycamp 地域: " とつける
        summary = '#pycamp {area}: ' + template.get('summary', '')
        issue_dict['summary'] = summary.format(**params)
    else:
        issue_dict['issuetype'] = {'id': ISSUE_TYPE_TASK}

    # issue を作成する
    issue = jira.create_issue(fields=issue_dict)
    # JIRA bot を watcher からはずす
    jira.remove_watcher(issue, settings.JIRA_USER)
    # コアスタッフを watcher に追加
    for watcher in CORE_STAFFS:
        jira.add_watcher(issue, watcher)
    return issue


def get_task_template(service):
    """
    Google Spreadsheetから親タスクのテンプレート情報を抜き出す

    :param service: Google Sheets APIの接続サービス
    """
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range='親タスク!A2:D2').execute()
    row = result.get('values', [])[0]
    # 作成するチケットのテンプレート
    template = {
        'assignee_type': ASSIGNEE_TYPE[row[0]],
        'delta': int(row[1]),  # 開催日からの差の日数
        'summary': row[2],  # タイトル
        'description': row[3],  # 本文
    }
    return template


def get_subtask_template(service):
    """
    Google Spreadsheetから親タスクのテンプレート情報を抜き出す

    :param service: Google Sheets APIの接続サービス
    """
    result = service.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range='サブタスク!A2:E').execute()
    subtask_template = {}
    for row in result.get('values', []):
        category = row[0]
        template = {
            'assignee_type': ASSIGNEE_TYPE[row[1]],
            'delta': int(row[2]),  # 開催日からの差の日数
            'summary': row[3],
            'description': row[4],
        }
        if category in subtask_template:
            subtask_template[category].append(template)
        else:
            subtask_template[category] = [template]
    return subtask_template


@respond_to('^pycamp\s+create\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)')
def pycamp_create(message, area, date_str, local_staff, lecturer):
    """
    Python Boot Camp の issue をまとめて作成する

    :params area: 地域名(札幌、大阪など)
    :params date_str: 開催日の日付文字列
    :params jira_id: 現地スタッフの JIRA ID
    """

    # 日付が正しいかチェック
    try:
        target_date = parser.parse(date_str)
    except ValueError:
        botsend(message, 'Python Boot Campの開催日に正しい日付を指定してください')
        return

    # 開催日(target_date)が過去の場合は1年後にする
    if datetime.now() > target_date:
        target_date = target_date.replace(year=target_date.year + 1)

    # 指定されたユーザーの存在チェック
    try:
        jira.user(local_staff)
        jira.user(lecturer)
    except JIRAError as e:
        botsend(message, '`$pycamp` エラー: `{}`'.format(e.text))
        return

    # Google Sheets API でシートから情報を抜き出す
    service = get_service('sheets', 'v4')
    # 親タスクのテンプレートをスプレッドシートから取得
    task_template = get_task_template(service)
    # 親タスクのテンプレートをスプレッドシートから取得
    subtask_template = get_subtask_template(service)

    # issue を作成するための情報
    params = {
        'reporter': REPORTER,
        'local_staff': local_staff,
        'lecturer': lecturer,
        'target_date': target_date,
        'area': area,
    }
    try:
        # テンプレートとパラメーターから JIRA issue を作成する
        issue = create_issue(task_template, params)
        desc = issue.fields.description

        # サブタスクを作成する
        for category in sorted(subtask_template.keys()):
            # カテゴリーを description に追加
            desc += '\r\n\r\nh3. {}\r\n\r\n'.format(category)
            for subtask in subtask_template[category]:
                sub_issue = create_issue(subtask, params, issue.key, area)
                _, summary = sub_issue.fields.summary.split(': ', 1)
                # サブタスクへのリンクを親タスクのdescriptionに追加
                desc += '* {} {}\r\n'.format(sub_issue.key, summary)

        # descriptionを更新する
        issue.update(description=desc)

        botsend(message, 'チケットを作成しました: {}'.format(issue.permalink()))
    except JIRAError as e:
        import pdb
        pdb.set_trace()
        botsend(message, '`$pycamp` エラー:', e.text)


def get_participants(url):
    """
    イベント情報のWebページから参加者情報を取得する

    :url text: イベントページのURL
    :return: 参加者情報の一覧(辞書の配列)
    """
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')
    td = soup.find('td', class_='participation')
    participants = []
    for ptype in td.select('div.ptype'):
        # 参加の種別を取得
        ptype_name = ptype.find('p', class_='ptype_name').text

        # 参加者枠の講師は無視する
        if ptype_name == '講師':
            continue
        # 参加者枠の名前を短くする
        for short_ptype_name in SHORT_PTYPE_NAMES:
            if short_ptype_name in ptype_name:
                ptype_name = short_ptype_name
                break

        # 人数を取得
        p = ptype.find('p', class_='participants')
        amount = p.find('span', class_='amount').text
        participants.append({
            'ptype': ptype_name,
            'amount': amount,
        })
    import time
    time.sleep(1)
    return participants


def generate_pycamp_summary(events):
    """
    イベント情報一覧からレスポンス用のattachementsを生成する
    """
    attachements = []
    # 新しい方が上にあるので、逆順で処理する
    for event in reversed(events):
        # イベント名、URL、日付
        title = '<{url}|{title}> ({started_at:%Y年%m月%d日})\n'.format(**event)
        ptypes = []
        for pinfo in event['participants']:
            ptypes.append('*{ptype}*: {amount}'.format(**pinfo))
        msg = {
            'pretext': title,
            'text': '、 '.join(ptypes),  # 参加者数の文字列を生成
            'mrkdwn_in': ['pretext', 'text'],
        }
        attachements.append(msg)
    return attachements


@respond_to('^pycamp\s+summary$')
@respond_to('^pycamp\s+summary\s+(-party)')
def pycamp_summary(message, party=None):
    """
    開催予定のpycampイベントの情報を返す
    """
    params = {
        'series_id': 137,
        'keyword': 'Python Boot Camp',
        'order': 2,  # 開催日時順
        'count': 20,  # 20件
    }
    r = requests.get('https://connpass.com/api/v1/event/', params=params)
    now = datetime.now()
    events = []
    for event in r.json()['events']:
        if party and '懇親会' not in event['title']:
            # 懇親会のみを対象にする
            continue
        elif not party and '懇親会' in event['title']:
            # 懇親会は無視する
            continue

        # 過去のイベントは対象外にする
        dt = parser.parse(event['started_at']).replace(tzinfo=None)
        if dt < now:
            break

        # イベント情報を追加
        event_info = {
            'title': event['title'],  # タイトル
            'started_at': dt,  # 開催日時
            'url': event['event_url'],  # イベントURL
            'address': event['address'],  # 開催場所
            'place': event['place'],  # 開催会場
        }
        event_info['participants'] = get_participants(event['event_url'])
        events.append(event_info)

    attachements = generate_pycamp_summary(events)
    botwebapi(message, attachements)


@respond_to('^pycamp\s+logo\s+(\S+)')
def pycamp_logo(message, title):
    botsend(message, 'Python Boot Camp ロゴ作成中... :hammer:')

    for name, size in IMAGES:
        logo_image = Image.open(os.path.join('templates', name))
        logo_image = logo_image.convert('RGBA')
        logo_image.thumbnail(size)

        width, height = size

        background = Image.new('RGBA', (width, TEXT_HEIGHT), MAIN_COLOR)
        font = ImageFont.truetype(os.path.join('fonts', FONT), size=TEXT_SIZE)
        draw = ImageDraw.Draw(background)
        text_width, _ = draw.textsize(title, font=font)
        draw.text(((width - text_width) / 2, 0), title, font=font, fill=(0, 0, 0))

        logo_image.paste(background, (0, height - TEXT_HEIGHT))

        with create_tmp_file() as tmpf:
            logo_image.save(tmpf, 'png')
            message.channel.upload_file(name, tmpf)

    botsend(message, '作成完了 :thumbsup:')


@respond_to('^pycamp\s+help')
def pycamp_help(message):
    """
    ヘルプメッセージを返す
    """
    botsend(message, HELP)


