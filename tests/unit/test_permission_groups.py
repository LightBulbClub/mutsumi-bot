from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import bots.milky.context as milky_context
import bots.onebot.context as onebot_context
from bots.milky.context import MilkyContextManager
from bots.milky.features import features as milky_features
from bots.onebot.context import OneBotContextManager
from bots.onebot.features import features as onebot_features
from bots.qqbot.context import QQBotContextManager
from bots.qqbot.features import features as qqbot_features, guild_features
from core.builtins.bot import Bot
from core.builtins.session.info import SessionInfo
from core.queue.client import JobQueueClient
from core.queue.contracts import PlatformAPI
from core.queue.peer import ServiceRoute
from core.tester import Tester, func_case


async def _test_permission_group_features():
    return (
        guild_features.support_permission_group
        and onebot_features.support_permission_group
        and milky_features.support_permission_group
        and not qqbot_features.support_permission_group
    )


async def _test_server_queue_forwarding():
    with patch("core.builtins.session.info._current_client_peer_id", return_value=None):
        session = await SessionInfo.assign(
            target_id="Discord|Channel|123",
            target_from="Discord|Channel",
            client_name="Discord",
        )
    captured = []

    class Peer:
        @staticmethod
        async def call(target, method, payload, timeout=None):
            captured.append((target, method, payload, True))
            return None

        @staticmethod
        async def submit(target, method, payload, timeout=None):
            captured.append((target, method, payload, False))
            return "task-id"

    grant = await PlatformAPI.grant_permission_group.using(Peer)(
        session, ["Discord|Client|1", "Discord|Client|2"], ["10", "20"], "test"
    )
    revoke = await PlatformAPI.revoke_permission_group.using(Peer).submit(session, "Discord|Client|1", "10")
    grant_args = PlatformAPI.grant_permission_group.decode_arguments(captured[0][2]).arguments
    return (
        grant is None
        and revoke == "task-id"
        and captured[0][0:2]
        == (
            ServiceRoute(service="Discord", routing_key=session.target_id, role="client"),
            PlatformAPI.grant_permission_group.name,
        )
        and captured[0][3] is True
        and grant_args["user_id"] == ["Discord|Client|1", "Discord|Client|2"]
        and grant_args["permission_group_id"] == ["10", "20"]
        and grant_args["reason"] == "test"
        and grant_args["session_info"].support_permission_group is False
        and captured[1][0:2]
        == (
            ServiceRoute(service="Discord", routing_key=session.target_id, role="client"),
            PlatformAPI.revoke_permission_group.name,
        )
        and captured[1][3] is False
    )


async def _test_client_queue_actions():
    session = await SessionInfo.assign(
        target_id="Discord|Channel|123",
        target_from="Discord|Channel",
        client_name="Discord",
    )
    context = SimpleNamespace(
        grant_permission_group=AsyncMock(return_value=None),
        revoke_permission_group=AsyncMock(return_value=None),
    )
    with (
        patch.object(Bot, "ContextSlots", [context]),
        patch.object(SessionInfo, "refresh_info", new=AsyncMock()),
    ):
        grant = await JobQueueClient.handlers[PlatformAPI.grant_permission_group.name](
            PlatformAPI.grant_permission_group.encode_arguments(session, ["Discord|Client|1"], ["10", "20"], "test")
        )
        revoke = await JobQueueClient.handlers[PlatformAPI.revoke_permission_group.name](
            PlatformAPI.revoke_permission_group.encode_arguments(session, ["Discord|Client|1"], ["10", "20"], "test")
        )

    for method in (context.grant_permission_group, context.revoke_permission_group):
        assert method.await_count == 1
        forwarded, *arguments = method.await_args.args
        assert isinstance(forwarded, SessionInfo)
        assert forwarded.target_id == session.target_id
        assert arguments == [["Discord|Client|1"], ["10", "20"], "test"]
    return grant is None and revoke is None


async def _test_qqbot_permission_groups():
    api = SimpleNamespace(
        create_guild_role_member=AsyncMock(),
        delete_guild_role_member=AsyncMock(),
    )
    session = SessionInfo(
        target_id="QQBot|Guild|123|456",
        target_from="QQBot|Guild",
        client_name="QQBot",
    )

    with patch("bots.qqbot.context._get_client", return_value=SimpleNamespace(api=api)):
        await QQBotContextManager.grant_permission_group(session, "QQBot|Tiny|1", ["10", "20"])
        await QQBotContextManager.revoke_permission_group(session, "QQBot|Tiny|1", "10")

    return (
        api.create_guild_role_member.await_args_list[0].args == ("123", "10", "1", "456")
        and api.create_guild_role_member.await_args_list[1].args == ("123", "20", "1", "456")
        and api.delete_guild_role_member.await_args.args == ("123", "10", "1", "456")
    )


async def _test_onebot_permission_groups():
    call_action = AsyncMock(return_value=None)
    session = SessionInfo(
        target_id="QQ|Group|123",
        target_from="QQ|Group",
        sender_id="QQ|1",
        sender_from="QQ",
        client_name="QQ",
        session_id="onebot-permission-groups",
    )

    with patch.object(onebot_context.aiocqhttp_bot, "call_action", new=call_action):
        await OneBotContextManager.grant_permission_group(session, ["QQ|1", "QQ|2"], ["admin"])
        await OneBotContextManager.revoke_permission_group(session, "QQ|1", "admin")
        # OneBot 没有「管理员」以外的原生权限组，此类请求应被跳过而非发出无效调用
        await OneBotContextManager.grant_permission_group(session, "QQ|1", "role|10")

    calls = call_action.await_args_list
    api_calls = [call.args for call in calls]
    api_kwargs = [call.kwargs for call in calls]
    return api_calls == [("set_group_admin",)] * 3 and api_kwargs == [
        {"group_id": 123, "user_id": 1, "enable": True},
        {"group_id": 123, "user_id": 2, "enable": True},
        {"group_id": 123, "user_id": 1, "enable": False},
    ]


async def _test_milky_permission_groups():
    set_admin = AsyncMock(return_value=None)
    session = SessionInfo(
        target_id="QQ|Group|123",
        target_from="QQ|Group",
        sender_id="QQ|1",
        sender_from="QQ",
        client_name="QQ",
        session_id="milky-permission-groups",
    )

    with patch.object(milky_context.milky_bot, "set_group_member_admin", new=set_admin):
        await MilkyContextManager.grant_permission_group(session, ["QQ|1", "QQ|2"], ["admin"])
        await MilkyContextManager.revoke_permission_group(session, "QQ|1", "admin")
        await MilkyContextManager.grant_permission_group(session, "QQ|1", "role|10")

    calls = set_admin.await_args_list
    return [call.kwargs for call in calls] == [
        {"group_id": 123, "user_id": 1, "is_set": True},
        {"group_id": 123, "user_id": 2, "is_set": True},
        {"group_id": 123, "user_id": 1, "is_set": False},
    ]


@func_case
async def test_permission_groups(tester: Tester):
    """平台原生权限组能力、队列转换与 SDK 调用测试。"""
    await tester.test(_test_permission_group_features, "权限组能力标记测试")
    await tester.test(_test_server_queue_forwarding, "权限组服务器队列转发测试")
    await tester.test(_test_client_queue_actions, "权限组客户端队列动作测试")
    await tester.test(_test_qqbot_permission_groups, "QQBot 权限组授予与移除测试")
    await tester.test(_test_onebot_permission_groups, "OneBot 权限组授予与移除测试")
    await tester.test(_test_milky_permission_groups, "Milky 权限组授予与移除测试")
    return tester
