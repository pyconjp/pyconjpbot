import re

from slackbot.bot import listen_to
from sympy import SympifyError, sympify

from ..botmessage import botsend

# 単一の数字っぽい文字列を表すパターン
NUM_PATTERN = re.compile("^\s*[-+]?[\d.,]+\s*$")


@listen_to("^(([-+*/^%!(),.\d\s]|pi|e|sqrt|sin|cos|tan)+)$")
def calc(message, expression, dummy_):
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
        # 整数だったらそのまま出力
        answer = int(result)
    else:
        try:
            answer = float(result)
        except SympifyError:
            # 答えが数値じゃなかったら無視する
            return

    # カンマをつけて出力する
    botsend(message, "{:,}".format(answer))
