from jira import JIRA, JIRAError
from slackbot import settings
from slackbot.bot import respond_to, listen_to

# Clean JIRA Url to not have trailing / if exists
CLEAN_JIRA_URL = settings.JIRA_URL if not settings.JIRA_URL[-1:] == '/' else settings.JIRA_URL[:-1]

# Login to jira
jira_auth = (settings.JIRA_USER, settings.JIRA_PASS)
jira = JIRA(CLEAN_JIRA_URL, basic_auth=jira_auth)

@listen_to('([A-Za-z]+)-([0-9]+)')
def jira_listener(message, project, number):
    # Only attempt to find tickets in projects defined in slackbot_settings
    if project not in settings.JIRA_PROJECTS:
        return

    # Parse ticket and search JIRA
    issue_id = '{}-{}'.format(project, number)
    try:
        issue = jira.issue(issue_id)
    except JIRAError:
        message.send('%s not found' % issue_id)
        return

    # Create variables to display to user
    summary = issue.fields.summary
    reporter = issue.fields.reporter.displayName if issue.fields.reporter else 'Anonymous'
    assignee = issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned'
    status = issue.fields.status
    ticket_url = CLEAN_JIRA_URL + '/browse/%s' % issue_id

    # Send message to Slack
    message.send('''%s:
    Summary: %s
    Reporter: %s
    Assignee: %s
    Status: %s
    ''' % (
        ticket_url,
        summary,
        reporter,
        assignee,
        status
    )
    )
