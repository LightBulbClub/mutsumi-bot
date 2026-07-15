from tortoise import fields

from core.database.base import DBModel

table_prefix_wife = "module_wife_"
table_prefix_husband = "module_husband_"


class TodayWifeInfo(DBModel):
    """
    用户随机到的老婆

    :param sender_id: 用户 ID。
    :param wife_name: 随机的老婆名。
    :param timestamp: 时间戳。
    """

    sender_id = fields.CharField(max_length=512, pk=True)
    wife_name = fields.CharField(max_length=512, null=True)
    timestamp = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = f"{table_prefix_wife}newinfo"

    @classmethod
    async def get_wife(cls, sender_id: str, name: str):
        info = (await cls.get_or_create(sender_id=sender_id))[0]
        info.wife_name = name
        await info.save()
        return True


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
        table = f"{table_prefix_husband}info"

    @classmethod
    async def get_husband(cls, sender_id: str, name: str):
        info = (await cls.get_or_create(sender_id=sender_id))[0]
        info.husband_name = name
        await info.save()
        return True
