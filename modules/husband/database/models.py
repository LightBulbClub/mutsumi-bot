from datetime import datetime, timedelta

from tortoise import fields

from core.database.base import DBModel

table_prefix = "module_husband_"


class TodayHusbandInfo(DBModel):
    """
    用户随机到的老公

    :param sender_id: 用户 ID。
    :param husband_name: 随机的老公名。
    :param timestamp: 时间戳。
    """

    sender_id = fields.CharField(max_length=512, pk=True)
    husband_name = fields.CharField(max_length=512, null=True)
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = f"{table_prefix}info"

    @classmethod
    async def get_husband(cls, sender_id: str, name: str):
        info = (await cls.get_or_create(sender_id=sender_id))[0]
        info.husband_name = name
        await info.save()
        return True
