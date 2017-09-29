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
