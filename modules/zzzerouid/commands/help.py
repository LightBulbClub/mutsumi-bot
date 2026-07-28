from core.builtins.bot import Bot
from core.builtins.message.internal import I18NContext, Image as ImageElement, Plain

from ..utils.name_convert import alias_to_char_name
from ..utils.resource import CAT_GUIDE_PATH, FLOWER_GUIDE_PATH


async def send_guide(msg: Bot.MessageSession, name: str):
    char_name = alias_to_char_name(name)

    # 默认使用花佬攻略
    path1 = FLOWER_GUIDE_PATH / f"{char_name}.jpg"
    path2 = FLOWER_GUIDE_PATH / f"{char_name}.png"
    path = path1 if path1.exists() else path2

    if not path.exists():
        path = CAT_GUIDE_PATH / f"{char_name}.jpg"

    if path.exists():
        await msg.finish(ImageElement.assign(path))
    else:
        await msg.finish(I18NContext("zzzerouid.message.guide.not_found", name=char_name))


async def send_help(msg: Bot.MessageSession):
    await msg.finish(
        Plain(
            "[ZZZ] Command List:\n"
            "~zzz bind uid <uid>\n"
            "~zzz switch uid [uid]\n"
            "~zzz unbind uid <uid>\n"
            "~zzz set cookie <uid> <cookie>\n"
            "~zzz set stoken <uid> <stoken>\n"
            "~zzz info\n"
            "~zzz stamina | note\n"
            "~zzz challenge | abyss\n"
            "~zzz hollow | zero\n"
            "~zzz mem | dangerous\n"
            "~zzz void | critical\n"
            "~zzz monthly | ledger [month]\n"
            "~zzz gacha | refresh gacha\n"
            "~zzz card <character> | refresh card <character>\n"
            "~zzz roster | characters\n"
            "~zzz guide <character>\n"
            "~zzz ann\n"
            "~zzz download | update assets\n"
            "~zzz help"
        )
    )
