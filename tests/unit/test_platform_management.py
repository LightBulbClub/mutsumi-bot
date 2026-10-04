"""平台成员管理操作的目标身份单元测试。"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import bots.onebot.bot as onebot_bot_module
import bots.onebot.context as onebot_context
from core.builtins.message.chain import MessageChain
from core.builtins.session.info import SessionInfo
from core.tester import Tester, func_case


async def _test_onebot_missing_optional_ids_keep_none():
    assigned = SimpleNamespace()
    assign = AsyncMock(return_value=assigned)
    process = AsyncMock()
    event = SimpleNamespace(
        message="~ping",
        detail_type="group",
        group_id=123,
        user_id=222,
        self_id=999,
        message_id=456,
        sender={"nickname": "member"},
    )
    with (
        patch.object(onebot_bot_module, "qq_account", None),
        patch.object(onebot_bot_module, "mention_required", False),
        patch.object(onebot_bot_module, "to_message_chain", new=AsyncMock(return_value=MessageChain.assign("~ping"))),
        patch.object(onebot_bot_module.SessionInfo, "assign", new=assign),
        patch.object(onebot_bot_module.Bot, "process_message", new=process),
    ):
        await onebot_bot_module.message_handler(event)
    return (
        assign.await_args.kwargs["reply_id"] is None
        and assign.await_args.kwargs["bot_id"] is None
        and process.await_args.args == (assigned, event)
    )


async def _test_onebot_private_list_failure_returns_empty():
    session = SessionInfo(
        target_id="QQ|Group|123",
        target_from="QQ|Group",
        sender_id="QQ|123",
        sender_from="QQ",
        client_name="QQ",
        session_id="onebot-private-list-failure",
    )
    send = AsyncMock()
    with (
        patch.object(
            onebot_context,
            "get_available_private_list",
            new=AsyncMock(side_effect=RuntimeError("friend list failed")),
        ),
        patch.object(onebot_context.OneBotContextManager, "send_message", new=send),
    ):
        try:
            result = await onebot_context.OneBotContextManager.send_private_msg(
                session,
                "QQ|456",
                MessageChain.assign("hello"),
            )
        except Exception:
            return False
    return result == [] and send.await_count == 0


@func_case
async def test_platform_management(tester: Tester):
    """平台管理操作必须作用于显式指定的成员。"""
    await tester.test(_test_onebot_missing_optional_ids_keep_none, "OneBot 缺失引用和机器人 ID 时保留空值")
    await tester.test(_test_onebot_private_list_failure_returns_empty, "OneBot 好友列表查询失败返回空消息 ID")
    return tester
