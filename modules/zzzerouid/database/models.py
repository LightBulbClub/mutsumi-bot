from tortoise import fields

from core.database.base import DBModel

table_prefix = "module_zzzerouid_"


class ZzzUidBind(DBModel):
    """User -> UID binding, supports multiple UIDs with one main UID."""

    sender_id = fields.CharField(max_length=512)
    bot_id = fields.CharField(max_length=64)
    uid = fields.CharField(max_length=32)
    is_main = fields.BooleanField(default=False)

    class Meta:
        table = f"{table_prefix}uid_bind"
        unique_together = ("sender_id", "bot_id", "uid")

    @classmethod
    async def insert_uid(cls, sender_id: str, bot_id: str, uid: str) -> int:
        if not uid.isdigit() or len(uid) not in (8, 9, 10):
            return -1
        if await cls.filter(sender_id=sender_id, bot_id=bot_id, uid=uid).first():
            return -2
        await cls.create(sender_id=sender_id, bot_id=bot_id, uid=uid, is_main=False)
        await cls._set_main(sender_id, bot_id, uid)
        return 0

    @classmethod
    async def switch_uid(cls, sender_id: str, bot_id: str, uid: str) -> int:
        bind = await cls.filter(sender_id=sender_id, bot_id=bot_id, uid=uid).first()
        if not bind:
            return -1
        await cls.filter(sender_id=sender_id, bot_id=bot_id).update(is_main=False)
        bind.is_main = True
        await bind.save()
        return 0

    @classmethod
    async def delete_uid(cls, sender_id: str, bot_id: str, uid: str) -> int:
        bind = await cls.filter(sender_id=sender_id, bot_id=bot_id, uid=uid).first()
        if not bind:
            return -1
        await bind.delete()
        remaining = await cls.filter(sender_id=sender_id, bot_id=bot_id).first()
        if remaining:
            remaining.is_main = True
            await remaining.save()
        return 0

    @classmethod
    async def get_main_uid(cls, sender_id: str, bot_id: str) -> str | None:
        bind = await cls.filter(sender_id=sender_id, bot_id=bot_id, is_main=True).first()
        return bind.uid if bind else None

    @classmethod
    async def _set_main(cls, sender_id: str, bot_id: str, uid: str):
        await cls.filter(sender_id=sender_id, bot_id=bot_id).update(is_main=False)
        await cls.filter(sender_id=sender_id, bot_id=bot_id, uid=uid).update(is_main=True)


class ZzzCookie(DBModel):
    """UID -> Cookie / SToken / device fingerprint."""

    uid = fields.CharField(max_length=32, primary_key=True)
    cookie = fields.TextField()
    stoken = fields.TextField(null=True)
    mys_id = fields.CharField(max_length=32, null=True)
    device_id = fields.CharField(max_length=64, null=True)
    device_fp = fields.CharField(max_length=64, null=True)

    class Meta:
        table = f"{table_prefix}cookie"


class ZzzPush(DBModel):
    """Push subscriptions."""

    sender_id = fields.CharField(max_length=512)
    target_id = fields.CharField(max_length=512)
    bot_id = fields.CharField(max_length=64)
    uid = fields.CharField(max_length=32)
    energy_push = fields.BooleanField(default=False)
    energy_value = fields.IntField(default=180)
    energy_is_push = fields.BooleanField(default=False)
    ann_push = fields.BooleanField(default=False)

    class Meta:
        table = f"{table_prefix}push"
