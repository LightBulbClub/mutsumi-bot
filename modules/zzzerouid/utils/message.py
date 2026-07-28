from typing import Any, Dict, Union

from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Plain


async def send_diff_msg(
    bot: Bot.MessageSession,
    code: Any,
    data: Dict[Any, Union[str, I18NContext]],
):
    for retcode, text in data.items():
        if code == retcode:
            if isinstance(text, str):
                await bot.send_message(Plain(text))
            else:
                await bot.send_message(text)
            return
