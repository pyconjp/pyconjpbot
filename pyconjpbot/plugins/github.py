from github import Github
from slackbot import settings
from slackbot.bot import respond_to

from ..botmessage import botsend, botwebapi

github = Github(settings.GITHUB_TOKEN)
org = github.get_organization(settings.GITHUB_ORGANIZATION)


@respond_to(r"^github\s+repos")
def github_repos(message):
    """
    リポジトリの一覧を返す
    """
    text = ""
    for repo in org.get_repos():
        text += f"- <{repo.html_url}|{repo.name}> {repo.description}\n"

    attachments = [
        {
            "pretext": f"{settings.GITHUB_ORGANIZATION} のリポジトリ一覧",
            "text": text,
            "mrkdwn_in": ["text"],
        }
    ]
    botwebapi(message, attachments)


@respond_to(r"^github\s+search\s+(.*)")
def github_search(message, keywords):
    """
    指定されたキーワードでissueを検索する
    """

    text = ""
    for repo in org.get_repos():
        # リポジトリを指定して検索
        issues = list(github.search_issues(keywords, repo=repo.full_name))
        if issues:
            text += f"リポジトリ: <{repo.html_url}|{repo.name}>\n"
            for issue in issues:
                text += f"- <{issue.html_url}|{issue.title}>\n"

    if text:
        attachments = [
            {
                "pretext": f"`{keywords}` の検索結果",
                "text": text,
                "mrkdwn_in": ["pretext", "text"],
            }
        ]
        botwebapi(message, attachments)

    # 結果が一つもない場合
    else:
        botsend(message, f"`{keywords}` にマッチするissueはありません")


@respond_to(r"^github\s+code\s+(.*)")
def github_code(message, keywords):
    """
    指定されたキーワードでコードを検索する
    """

    text = ""
    for repo in org.get_repos():
        # リポジトリを指定して検索
        files = list(github.search_code(keywords, repo=repo.full_name))
        if files:
            text += f"リポジトリ: <{repo.html_url}|{repo.name}>\n"
            for f in files:
                text += "- <{f.html_url}|{f.name}>\n"

    if text:
        attachments = [
            {
                "pretext": "`{keywords}` の検索結果",
                "text": text,
                "mrkdwn_in": ["pretext", "text"],
            }
        ]
        botwebapi(message, attachments)

    # 結果が一つもない場合
    else:
        botsend(message, "`{keywords}` にマッチするコードはありません")


@respond_to(r"^github\s+help$")
def github_help(message):
    """
    githubコマンドのヘルプを返す
    """
    botsend(
        message,
        """- `$github repos`: pyconjp organization のリポジトリ一覧を返す
- `$github search keywords`: 指定されたキーワードにマッチするissueを返す
- `$github code keywords`: 指定されたキーワードにマッチするコードを返す
""",
    )
