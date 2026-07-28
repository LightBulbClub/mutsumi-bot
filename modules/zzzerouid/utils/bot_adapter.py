from io import BytesIO
from pathlib import Path
from typing import Union

from PIL import Image as PILImage
from core.builtins.bot import Bot
from core.builtins.message.internal import Image, Plain


async def send_image(bot: Bot.MessageSession, img: Union[PILImage.Image, bytes, str, Path]):
    if isinstance(img, PILImage.Image):
        await bot.send_message(Image(img))
    elif isinstance(img, bytes):
        pil_img = PILImage.open(BytesIO(img))
        await bot.send_message(Image(pil_img))
    elif isinstance(img, (str, Path)):
        await bot.send_message(Image(Path(img)))
    else:
        await bot.send_message(Plain(str(img)))


async def send_text(bot: Bot.MessageSession, text: str):
    await bot.send_message(Plain(text))
