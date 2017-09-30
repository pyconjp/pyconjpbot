import json

def botsend(message, text):
    """
    スレッドの親かどうかで応答先を切り替える message.send() の変わりの関数

    :param messsage: slackbotのmessageオブジェクト
    :param text: 送信するテキストメッセージ
    """
    if message.thread_ts == message.body['ts']:
        # 親メッセージの場合
        message.send(text, thread_ts=None)
    else:
        # スレッド内のメッセージの場合
        message.send(text, thread_ts=message.thread_ts)


def botwebapi(message, attachments):
    """
    スレッドの親かどうかで応答先を切り替える message.send_webapi() の変わりの関数

    :param messsage: slackbotのmessageオブジェクト
    :param attachments: 送信するAttachments(JSON)
    """
    # 文字列じゃないときはJSON文字列にする
    if not isinstance(attachments, str):
        attachments = json.dumps(attachments)

    if message.thread_ts == message.body['ts']:
        # 親メッセージの場合
        message.send_webapi('', attachments)
    else:
        # スレッド内のメッセージの場合
        message.send_webapi('', attachments, thread_ts=message.thread_ts)
