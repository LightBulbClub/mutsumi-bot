from datetime import UTC, datetime
from typing import Sequence

from tortoise import fields
from tortoise.exceptions import IntegrityError

from core.database.base import DBModel
from core.utils.random import Random

table_prefix_wife = "module_wife_"
table_prefix_husband = "module_husband_"


def _is_local_today(timestamp: datetime | None) -> bool:
    """
    判断时间戳是否落在本地时区的今天。

    :param timestamp: 待判断的时间戳。
    """
    if timestamp is None:
        return False
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    return timestamp.astimezone().date() == datetime.now().astimezone().date()


class MarryDeck(DBModel):
    """
    用户牌堆中尚未抽出的牌。

    牌堆按 ``(用户, 性别)`` 区分：每行代表一张还没被抽走的牌。抽牌即随机取走一行并删除，
    行删空后按当前卡池重建。随机取剩余行保证剩余牌被抽出的概率相等，删除保证牌堆抽空前不重复。

    :param sender_id: 用户 ID。
    :param is_husband: 是否为老公牌堆。
    :param card_name: 尚未抽出的牌面（老婆/老公名）。
    """

    id = fields.IntField(pk=True)
    sender_id = fields.CharField(max_length=512, index=True)
    is_husband = fields.BooleanField(default=False)
    card_name = fields.CharField(max_length=512)

    class Meta:
        table = "module_marry_deck"
        unique_together = (("sender_id", "is_husband", "card_name"),)

    @classmethod
    async def _refill(cls, sender_id: str, is_husband: bool, pool: Sequence[str]) -> None:
        """
        按当前卡池重洗一副牌堆。

        :param sender_id: 用户 ID。
        :param is_husband: 是否为老公牌堆。
        :param pool: 当前卡池。
        """
        try:
            await cls.bulk_create([cls(sender_id=sender_id, is_husband=is_husband, card_name=name) for name in pool])
        except IntegrityError:
            # 并发下另一请求可能已重建牌堆，下一轮重新读取即可。
            pass

    @classmethod
    async def draw(cls, sender_id: str, is_husband: bool, names: Sequence[str]) -> str:
        """
        从牌堆随机抽出一张牌。

        每张剩余牌被抽到的概率相等；在牌堆被抽空之前不会抽到重复的牌，抽空后按当前卡池重洗。
        卡池中已下架的牌会从牌堆中剔除，不会抽出。

        :param sender_id: 用户 ID。
        :param is_husband: 是否为老公牌堆。
        :param names: 当前卡池，牌堆抽空或卡池变动时据此重建。
        :return: 抽出的牌面（老婆/老公名）。
        """
        pool = list(dict.fromkeys(names))
        if not pool:
            raise ValueError("marry 牌堆为空，无法抽牌")
        valid = set(pool)

        while True:
            cards = list(await cls.filter(sender_id=sender_id, is_husband=is_husband))
            # 卡池里已下架的牌先剔除，避免抽出没有素材的牌面。
            stale = [card.id for card in cards if card.card_name not in valid]
            if stale:
                await cls.filter(id__in=stale).delete()
                cards = [card for card in cards if card.card_name in valid]
            if not cards:
                # 牌堆抽空（或首次使用）：按当前卡池重洗一副。
                await cls._refill(sender_id, is_husband, pool)
                continue

            picked = cards[Random.randrange(len(cards))]
            # 并发下同一张牌可能已被其它请求抽走，删除成功才算真正抽到。
            if await cls.filter(id=picked.id).delete():
                return picked.card_name


class _TodayCardMixin:
    """今日老婆/老公记录的共用读写逻辑。"""

    _name_field: str

    @classmethod
    async def set_today(cls, sender_id: str, name: str) -> None:
        """
        记录用户今天抽到的牌面。

        :param sender_id: 用户 ID。
        :param name: 抽到的牌面。
        """
        info = (await cls.get_or_create(sender_id=sender_id))[0]
        setattr(info, cls._name_field, name)
        await info.save()

    @classmethod
    async def get_today(cls, sender_id: str) -> str | None:
        """
        读取用户今天抽到的牌面，今天还没抽过则返回 None。

        :param sender_id: 用户 ID。
        """
        info = await cls.get_or_none(sender_id=sender_id)
        if info and _is_local_today(info.timestamp):
            return getattr(info, cls._name_field)
        return None


class TodayWifeInfo(_TodayCardMixin, DBModel):
    """
    用户随机到的老婆

    :param sender_id: 用户 ID。
    :param wife_name: 随机的老婆名。
    :param timestamp: 抽出该老婆的时间。
    """

    _name_field = "wife_name"

    sender_id = fields.CharField(max_length=512, pk=True)
    wife_name = fields.CharField(max_length=512, null=True)
    timestamp = fields.DatetimeField(auto_now=True)

    class Meta:
        table = f"{table_prefix_wife}newinfo"


class TodayHusbandInfo(_TodayCardMixin, DBModel):
    """
    用户随机到的老公

    :param sender_id: 用户 ID。
    :param husband_name: 随机的老公名。
    :param timestamp: 抽出该老公的时间。
    """

    _name_field = "husband_name"

    sender_id = fields.CharField(max_length=512, pk=True)
    husband_name = fields.CharField(max_length=512, null=True)
    timestamp = fields.DatetimeField(auto_now=True)

    class Meta:
        table = f"{table_prefix_husband}info"
