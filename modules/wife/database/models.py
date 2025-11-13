from datetime import datetime, timedelta

from tortoise import fields

from core.database.base import DBModel

table_prefix = "module_wife_"


class TodayWifeInfo(DBModel):
    """
    用户随机到的老婆

    :param sender_id: 用户 ID。
    :param wife_name: 随机的老婆名。
    :param timestamp: 时间戳。
    """

    sender_id = fields.CharField(max_length=512, pk=True)
    wife_name = fields.CharField(max_length=512, null=True)
    timestamp = fields.DatetimeField(auto_now=True)

    class Meta:
        table = f"{table_prefix}newinfo"

    @classmethod
    async def get_wife(cls, sender_id: str, name: str):
        info = (await cls.get_or_create(sender_id=sender_id))[0]
        info.wife_name = name
        await info.save()
        return True
