import re

from slackbot.bot import respond_to, listen_to
from sympy import sympify, SympifyError

# 単一の数字っぽい文字列を表すパターン
NUM_PATTERN = re.compile('^\s*[-+]?[\d.]+\s*$')

@listen_to('^(([-+*/^%!()\d\s]|pi|e|sqrt|sin|cos|tan)+)$')
def calc(message, expression, dummy_):
    """
    数式っぽい文字列だったら計算して結果を返す
    """

    # 数字っぽいパターンの場合は無視する
    if NUM_PATTERN.match(expression):
        return
    try:
        result = sympify(expression)
    except SympifyError:
        # 数式じゃなかったら無視する
        return
    
    if result.is_Integer:
        message.send(str(result))
    else:
        message.send(str(float(result.evalf())))


