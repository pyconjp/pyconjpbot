import json

from github import Github
from slackbot import settings
from slackbot.bot import respond_to

github = Github(settings.GITHUB_TOKEN)
org = github.get_organization(settings.GITHUB_ORGANIZATION)

@respond_to('^github\s+repos')
def github_repos(message):
    """
    リポジトリの一覧を返す
    """
    text = ""
    for repo in org.get_repos():
        text += "- <{}|{}> {}\n".format(repo.url, repo.name, repo.description)

    attachments = [{
        'pretext': '{} のリポジトリ一覧'.format(settings.GITHUB_ORGANIZATION),
        'text': text,
        'mrkdwn_in': ['text'],
    }]
    message.send_webapi('', json.dumps(attachments))

