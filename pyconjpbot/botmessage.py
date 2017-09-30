import json


def botsend(message, text):
    """
    スレッドの親かどうかで応答先を切り替える message.send() の代わりの関数

    :param messsage: slackbotのmessageオブジェクト
    :param text: 送信するテキストメッセージ
    """
    if 'thread_ts' in message.body:
        # スレッド内のメッセージの場合
        message.send(text, thread_ts=message.thread_ts)
    else:
        # 親メッセージの場合
        message.send(text, thread_ts=None)


def botreply(message, text):
    """
    スレッドの親かどうかで応答先を切り替える message.reply() の代わりの関数

    :param messsage: slackbotのmessageオブジェクト
    :param text: 送信するテキストメッセージ
    """
    if 'thread_ts' in message.body:
        # スレッド内のメッセージの場合
        message.reply(text, in_thread=True)
    else:
        # 親メッセージの場合
        message.reply(text)


def botwebapi(message, attachments):
    """
    スレッドの親かどうかで応答先を切り替える message.send_webapi() の代わりの関数

    :param messsage: slackbotのmessageオブジェクト
    :param attachments: 送信するAttachments(JSON)
    """
    # 文字列じゃないときはJSON文字列にする
    if not isinstance(attachments, str):
        attachments = json.dumps(attachments)

    if 'thread_ts' in message.body:
        # スレッド内のメッセージの場合
        message.send_webapi('', attachments, thread_ts=message.thread_ts)
    else:
        # 親メッセージの場合
        message.send_webapi('', attachments)
