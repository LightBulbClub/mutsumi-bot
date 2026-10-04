"""统一机器人场景状态接口测试。"""

import inspect
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from core.builtins.session.bot_state import BotState
from core.builtins.session.context import ContextManager
from core.builtins.session.info import SessionInfo
from core.queue import codec
from core.queue.contracts import PlatformAPI
from core.tester import Tester, func_case


def _test_bot_state_is_serializable_and_preserves_unknown_permissions() -> bool:
    state = BotState(
        available=True,
        joined=True,
        permissions={"role": "admin", "bitset": 4, "custom": None},
        raw={"platform_field": ["value"]},
    )
    restored = codec.decode(codec.encode(state, BotState), BotState)
    return (
        restored == state
        and restored.has_permission("custom") is None
        and restored.has_permission("missing") is None
        and restored.has_permission("role") is None
    )


def _test_bot_state_rpc_contract_matches_context() -> bool:
    return PlatformAPI.check_bot_state.signature == inspect.signature(ContextManager.check_bot_state)


async def _test_webui_reports_full_state() -> bool:
    from bots.web.context import WebContextManager

    session = SessionInfo(
        target_id="Web|Group|state",
        target_from="Web|Group",
        client_name="Web",
        session_id="bot-state-web",
    )
    state = await WebContextManager.check_bot_state(session)
    return all(
        getattr(state, name) is True
        for name in (
            "available",
            "joined",
            "is_owner",
            "is_admin",
            "can_read_messages",
            "can_read_all_messages",
            "can_send_messages",
            "can_send_proactive_messages",
            "can_manage_messages",
            "can_manage_members",
            "can_restrict_members",
            "can_react",
            "can_send_private_messages",
        )
    )


async def _test_mock_session_provides_local_bot_state() -> bool:
    from core.tester.mock.session import MockMessageSession

    session = MockMessageSession()
    session.session_info = SessionInfo(
        target_id="TEST|Console|0",
        target_from="TEST",
        client_name="TEST",
        support_manage=True,
        support_reaction=True,
        support_private_msg=True,
    )
    state = await session.check_bot_state()
    return state.raw == {"platform": "test"} and state.can_manage_members and state.can_react


async def _test_qqbot_group_state_maps_official_bot_state() -> bool:
    import bots.qqbot.context as qqbot_context
    from bots.qqbot.info import target_group_prefix

    session = SessionInfo(
        target_id=f"{target_group_prefix}|group-openid",
        target_from=target_group_prefix,
        client_name="QQBot",
        session_id="bot-state-qqbot-group",
    )
    state_api = SimpleNamespace(
        get_group_bot_state=AsyncMock(
            return_value={
                "member_openid": "bot-openid",
                "joined_at": "2025-06-15T14:30:00+08:00",
                "allow_proactive_msg": False,
                "recv_msg_setting": "only_mention",
                "member_role": "admin",
            }
        )
    )
    with patch.object(qqbot_context, "_get_client", return_value=SimpleNamespace(api=state_api)):
        state = await qqbot_context.QQBotContextManager.check_bot_state(session)
    return (
        state.joined is True
        and state.is_admin is True
        and state.can_read_messages is True
        and state.can_read_all_messages is False
        and state.can_send_proactive_messages is False
        and state.permissions["allow_proactive_msg"] is False
        and state.raw["member_openid"] == "bot-openid"
    )


async def _test_non_web_private_context_does_not_claim_management_permissions() -> bool:
    import bots.qqbot.context as qqbot_context
    from bots.qqbot.info import target_c2c_prefix

    session = SessionInfo(
        target_id=f"{target_c2c_prefix}|user-openid",
        target_from=target_c2c_prefix,
        client_name="QQBot",
        session_id="bot-state-qqbot-private",
    )
    state = await qqbot_context.QQBotContextManager.check_bot_state(session)
    return (
        state.joined is True
        and state.can_send_messages is True
        and state.can_send_private_messages is True
        and state.is_owner is None
        and state.is_admin is None
        and state.can_manage_messages is None
        and state.can_manage_members is None
        and state.can_restrict_members is None
    )


async def _test_onebot_group_state_maps_bot_role() -> bool:
    import bots.onebot.context as onebot_context
    from bots.onebot.info import target_group_prefix

    session = SessionInfo(
        target_id=f"{target_group_prefix}|123",
        target_from=target_group_prefix,
        client_name="QQ",
        bot_id="456",
        session_id="bot-state-onebot-group",
    )
    call_action = AsyncMock(return_value={"user_id": 456, "role": "admin", "nickname": "Akari"})
    with patch.object(onebot_context.aiocqhttp_bot, "call_action", new=call_action):
        state = await onebot_context.OneBotContextManager.check_bot_state(session)
    return (
        state.joined is True
        and state.is_admin is True
        and state.is_owner is False
        and state.can_restrict_members is True
        and state.permissions["role"] == "admin"
        and call_action.await_args.kwargs == {"group_id": 123, "user_id": 456}
    )


@func_case
async def test_bot_state(tester: Tester):
    await tester.test(_test_bot_state_is_serializable_and_preserves_unknown_permissions, "BotState 序列化与未知权限")
    await tester.test(_test_bot_state_rpc_contract_matches_context, "BotState RPC 契约")
    await tester.test(_test_webui_reports_full_state, "WebUI 返回完整机器人权限")
    await tester.test(_test_mock_session_provides_local_bot_state, "测试会话提供本地机器人状态")
    await tester.test(_test_qqbot_group_state_maps_official_bot_state, "QQBot 映射官方群机器人状态")
    await tester.test(_test_non_web_private_context_does_not_claim_management_permissions, "非 Web 私聊不宣称管理权限")
    await tester.test(_test_onebot_group_state_maps_bot_role, "OneBot 映射机器人群角色")
    return tester
