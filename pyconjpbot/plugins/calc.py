import re

from slackbot.bot import listen_to
from slackbot.dispatcher import Message
from sympy import SympifyError, sympify

from ..botmessage import botsend

# 単一の数字っぽい文字列を表すパターン
NUM_PATTERN = re.compile(r"^\s*[-+]?[\d.,]+\s*$")


@listen_to(r"^(([-+*/^%!(),.\d\s]|pi|e|sqrt|sin|cos|tan)+)$")
def calc(message: Message, expression: str, dummy_: str) -> None:
    """
    数式っぽい文字列だったら計算して結果を返す
    """
    # 単一の数字っぽいパターンは無視する
    if NUM_PATTERN.match(expression):
        return
    try:
        # カンマを削除
        expression = expression.replace(",", "")
        result = sympify(expression)
    except SympifyError:
        # 数式じゃなかったら無視する
        return

    if result.is_Integer:
        # カンマをつけて出力する
        answer = f"{int(result):,}"
    else:
        try:
            # カンマをつけて出力する
            answer = f"{float(result):,}"
        except SympifyError:
            # 答えが数値じゃなかったら無視する
            return

    botsend(message, answer)
