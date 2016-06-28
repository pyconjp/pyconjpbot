import argparse
import json
from urllib.parse import quote

from jira import JIRA, JIRAError
from slackbot import settings
from slackbot.bot import respond_to, listen_to

# Clean JIRA Url to not have trailing / if exists
CLEAN_JIRA_URL = settings.JIRA_URL if not settings.JIRA_URL[-1:] == '/' else settings.JIRA_URL[:-1]

# Login to jira
jira_auth = (settings.JIRA_USER, settings.JIRA_PASS)
jira = JIRA(CLEAN_JIRA_URL, basic_auth=jira_auth)

# デフォルトの検索対象プロジェクト
DEFAULT_PROJECT = 'SAR'

# コンポーネントの一覧
COMPONENT = {
    '全体': '0.全体',
    '事務局': '1.事務局',
    '会場': '2.会場',
    'プログラム': '3.プログラム',
    'メディア': '4.メディア',
    '環境': '5.環境',
    'その他': '9.その他',
}

# $jira コマンドの引数処理用 argparse
HELP = """
```
$jira {} [-p PROJECT] [-c COMPONENT] [-l LABEL] [-s] [keywords ...]
$jira {} [-p PROJECT] [-c COMPONENT] [-l LABEL] [-s] [keywords ...]

オプション引数:
  -p PROJECT, --project PROJECT
                        検索対象のプロジェクトを指定する(default: {})
  -c COMPONENT, --component COMPONENT
                        検索対象のコンポーネントを指定する
  -l LABEL, --label LABEL
                        検索対象のラベルを指定する
  -s, --summary         要約(タイトル)のみを検索対象にする(未指定時は全文検索)
```
"""

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('-p', '--project', default=DEFAULT_PROJECT, type=str,
                    help='検索対象のプロジェクトを指定する(default: {})'.format(DEFAULT_PROJECT))
parser.add_argument('-c', '--component', type=str,
                    help='検索対象のコンポーネントを指定する')
parser.add_argument('-l', '--label', type=str,
                    help='検索対象のラベルを指定する')
parser.add_argument('-s', '--summary', default=False, action='store_true',
                    help='要約(タイトル)のみを検索対象にする(未指定時は全文検索)')
parser.add_argument('keywords', nargs='*', type=str,
                    help='検索対象のキーワードを指定する')

@listen_to(r'(^|[^/])\b([A-Za-z]+)-([0-9]+)\b')
def jira_listener(message, pre, project, number):
    """
    JIRAのissue idっぽいものを取得したら、そのissueの情報を返す
    """
    # botメッセージの場合は無視する
    if message.body.get('subtype', '') == 'bot_message':
        return

    # Only attempt to find tickets in projects defined in slackbot_settings
    if project not in settings.JIRA_PROJECTS:
        return

    # Parse ticket and search JIRA
    issue_id = '{}-{}'.format(project, number)
    try:
        issue = jira.issue(issue_id)
    except JIRAError:
        message.send('%s は存在しません' % issue_id)
        return

    # Create variables to display to user
    summary = issue.fields.summary
    assignee = '未割り当て'
    if issue.fields.assignee:
        assignee = issue.fields.assignee.displayName 
    status = issue.fields.status.name
    issue_url = issue.permalink()

    attachments = [{
        'fallback': '{} {}'.format(issue_id, summary),
        'pretext': '<{}|{}> {}'.format(issue_url, issue_id, summary),
        'fields': [
            {
                'title': '担当者',
                'value': assignee,
                'short': True,
            },
            {
                'title': 'ステータス',
                'value': status,
                'short': True,
            },
        ],
    }]
    message.send_webapi('', json.dumps(attachments))

def _drive_help(message, cmd1, cmd2):
    """
    jira 検索コマンドのヘルプを返す
    """
    message.send(HELP.format(cmd1, cmd2, DEFAULT_PROJECT))

def _build_jql(args, jql_base=''):
    """
    引数から JIRA を検索するための JQL を生成する
    """
    jql = jql_base
    jql += 'project = {}'.format(args.project)
    if args.component:
        component = COMPONENT.get(args.component, args.component)
        jql += ' AND component = {}'.format(component)
    if args.label:
        jql += ' AND labels = {}'.format(args.label)
    if args.keywords:
        target = 'text'
        if args.summary:
            # 要約を検索対象にする
            target = 'summary'
        jql += ' AND {} ~ "{}"'.format(target, ' '.join(args.keywords))

    return jql
    
@respond_to('jira search (.*)')
@respond_to('jira 検索 (.*)')
def jira_search(message, keywords):
    """
    JIRAをキーワード検索した結果を返す(オープン状態のみ)
    """

    # 引数を処理する
    try:
        args, argv = parser.parse_known_args(keywords.split())
    except SystemExit:
        message.send('引数の形式が正しくありません')
        _drive_help(message, 'search', '検索')
        return

    # 引数から query を生成
    jql = _build_jql(args, 'status in (Open, "In Progress", Reopened) AND ')
    
    title = '「{}」の検索結果(オープンのみ)'.format(keywords)
    _send_jira_search_responce(message, jql, title)

@respond_to('jira allsearch (.*)')
@respond_to('jira 全検索 (.*)')
def jira_allsearch(message, keywords):
    """
    JIRAをキーワード検索した結果を返す(全ステータス対象)
    """
    # 引数を処理する
    try:
        args, argv = parser.parse_known_args(keywords.split())
    except SystemExit:
        message.send('引数の形式が正しくありません')
        _drive_help(message, 'search', '検索')
        return

    # 引数から query を生成
    jql = _build_jql(args)
    
    title = '「{}」の検索結果(全ステータス)'.format(keywords)
    _send_jira_search_responce(message, jql, title)

@respond_to('jira assignee (.*)')
@respond_to('jira 担当者? (.*)')
def jira_assignee(message, user):
    """
    指定されたユーザーにアサインされた課題の一覧を返す
    """
    jql = 'status in (Open, "In Progress", Reopened) AND assignee in ({})'
    title = '「{}」の担当課題'.format(user)
    _send_jira_search_responce(message, jql.format(user), title)

def _send_jira_search_responce(message, query, title):
    """
    JIRAをqueryで検索した結果を返すメソッド
    """
    pretext = title
    pretext += '(<{}/issues/?jql={}|JIRAで見る>)'.format(CLEAN_JIRA_URL, quote(query))
    text = ''

    try:
        issues = jira.search_issues(query)
    except JIRAError as err:
        # なんらかのエラーが発生
        message.send('JIRAError: `{}`'.format(err.text))
        return
    
    if issues:
        for issue in issues:
            summary = issue.fields.summary
            key = issue.key
            url = issue.permalink()
            status = issue.fields.status.name
            text += '- <{}|{}> {}({})\n'.format(url, key, summary, status)
    else:
        text += '該当するJIRA issueは見つかりませんでした'

    attachments = [{
        'fallback': title,
        'pretext': pretext,
        'text': text,
    }]
    message.send_webapi('', json.dumps(attachments))

@respond_to('jira filters?')
@respond_to('jira フィルター?')
def jira_filter(message):
    """
    フィルターの一覧を返す
    """
    pretext = 'フィルター一覧'
    filters = [
        ('1.事務局チーム', '10301'),
        ('2.会場チーム', '10302'),
        ('3.プログラムチーム', '10300'),
        ('4.メディアチーム ', '10303'),
        ('一般社団法人PyCon JP', '11500'),
        ]
    flist = []
    for label, key in filters:
        flist.append('<{}/issues/?filter={}|{}>'.format(CLEAN_JIRA_URL, key, label))
        
    attachments = [{
        'fallback': pretext,
        'pretext': pretext,
        'text': ' / '.join(flist),
    }]
    message.send_webapi('', json.dumps(attachments))

@respond_to('jira help$')
def jira_search(message):
    """
    jiraコマンドのヘルプを返す
    """
    message.send('''- `SAR-123`: 指定されたチケットの詳細情報を返す
- `$jira search keywords` `$jira 検索 keywords`: 指定されたキーワードで検索(オープンのみ)
- `$jira allsearch keywords` `$jira 全検索 keywords`: 指定されたキーワードで検索(全ステータス)
- `$jira assignee user` `$jira 担当 user`: 指定されたユーザーが担当しているissueを返す
- `$jira filter` `$jira フィルター`: フィルターの一覧を返す

検索/全検索時に使用できるオプション''' + HELP.format('検索', '全検索', DEFAULT_PROJECT))
