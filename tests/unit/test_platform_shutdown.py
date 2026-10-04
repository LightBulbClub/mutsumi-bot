"""平台客户端关闭流程单元测试。"""

import asyncio
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import botpy
import bots.onebot.context as onebot_context
import bots.web.client as web_client
from bots.qqbot.context import _MessageSendQueue, _PreparedMessage, _QueuedMessage, _TypingState
from core.tester import Tester, func_case
from core.tester.timing import TIME_SCALE
from bots.onebot.config import AiocqhttpConfig
from bots.qqbot.config import QQBotConfig

# Adapter modules register handlers on import; local enabled credentials must
# never turn an isolated lifecycle test into a live platform connection.
with (
    patch.object(AiocqhttpConfig, "enable", False),
    patch.object(QQBotConfig, "enable", False),
):
    import bots.onebot.bot as onebot_bot_module
    import bots.qqbot.bot as qqbot_bot_module


async def _run_web_lifespan(raise_inside: bool) -> bool:
    if not hasattr(web_client, "client_cleanup"):
        return False

    client_init = AsyncMock()
    client_cleanup = AsyncMock()
    union_info = SimpleNamespace(edit_attr=AsyncMock())
    resolve_union = AsyncMock(return_value=union_info)

    caught = False
    with (
        patch.object(web_client, "client_init", new=client_init),
        patch.object(web_client, "client_cleanup", new=client_cleanup),
        patch.object(web_client.SenderUnionInfo, "resolve_union", new=resolve_union),
        patch.object(web_client, "dist_path", new=Path("__missing_webui__")),
    ):
        try:
            async with web_client.lifespan(web_client.app):
                if raise_inside:
                    raise RuntimeError("lifespan body failed")
        except RuntimeError as exc:
            caught = str(exc) == "lifespan body failed"

    return (
        client_init.await_count == 1
        and resolve_union.await_count == 1
        and union_info.edit_attr.await_count == 1
        and client_cleanup.await_count == 1
        and (caught if raise_inside else not caught)
    )


async def _test_web_lifespan_cleans_up_normally():
    return await _run_web_lifespan(False)


async def _test_web_lifespan_cleans_up_after_application_error():
    return await _run_web_lifespan(True)


async def _test_onebot_shutdown_stops_worker_and_cleans_core():
    if not hasattr(onebot_bot_module, "shutdown") or not hasattr(onebot_bot_module, "client_cleanup"):
        return False
    stop_worker = AsyncMock()
    cleanup = AsyncMock()
    with (
        patch.object(onebot_bot_module.OneBotFetchedContextManager, "stop_task_processor", new=stop_worker),
        patch.object(onebot_bot_module, "client_cleanup", new=cleanup),
    ):
        await onebot_bot_module.shutdown()
    return stop_worker.await_count == 1 and cleanup.await_count == 1


async def _test_onebot_shutdown_releases_typing_tasks_and_cache():
    context_manager = onebot_context.OneBotContextManager
    session_id = "onebot-shutdown-typing"
    cache_key = "QQ|shutdown-user"
    action_started = asyncio.Event()

    async def call_action(*args, **kwargs):
        action_started.set()
        return {}

    session_info = SimpleNamespace(
        session_id=session_id,
        target_from=onebot_context.target_group_prefix,
        sender_id=cache_key,
        message_id="shutdown-message",
    )
    context_manager.context[session_id] = object()
    previous_impl = onebot_context.Temp.data.get("onebot_impl")
    onebot_context.Temp.data["onebot_impl"] = "llonebot"
    onebot_context.last_send_typing_time[cache_key] = 1.0

    stop_worker = AsyncMock()
    cleanup = AsyncMock()
    try:
        with patch.object(onebot_context.aiocqhttp_bot, "call_action", new=call_action):
            await context_manager.start_typing(session_info)
            await asyncio.wait_for(action_started.wait(), timeout=1 * TIME_SCALE)

        typing_flag = context_manager.typing_flags.get(session_id)
        typing_task = context_manager.typing_tasks.get(session_id)
        if typing_flag is None or typing_task is None:
            return False

        with (
            patch.object(onebot_bot_module.OneBotFetchedContextManager, "stop_task_processor", new=stop_worker),
            patch.object(onebot_bot_module, "client_cleanup", new=cleanup),
        ):
            await onebot_bot_module.shutdown()

        return (
            stop_worker.await_count == 1
            and cleanup.await_count == 1
            and typing_flag.is_set()
            and typing_task.done()
            and not context_manager.typing_flags
            and not context_manager.typing_tasks
            and not onebot_context.last_send_typing_time
        )
    finally:
        flag = context_manager.typing_flags.pop(session_id, None)
        if flag:
            flag.set()
        task = context_manager.typing_tasks.pop(session_id, None)
        if task and not task.done():
            task.cancel()
        if task:
            await asyncio.gather(task, return_exceptions=True)
        context_manager.context.pop(session_id, None)
        onebot_context.last_send_typing_time.clear()
        if previous_impl is None:
            onebot_context.Temp.data.pop("onebot_impl", None)
        else:
            onebot_context.Temp.data["onebot_impl"] = previous_impl


async def _test_qqbot_close_stops_worker_and_cleans_core():
    if not hasattr(qqbot_bot_module, "client_cleanup"):
        return False
    cleanup = AsyncMock()
    stop_worker = AsyncMock()
    sdk_close = AsyncMock()
    with (
        patch.object(qqbot_bot_module, "client_cleanup", new=cleanup),
        patch.object(qqbot_bot_module.QQBotFetchedContextManager, "stop_task_processor", new=stop_worker),
        patch.object(botpy.Client, "close", new=sdk_close),
    ):
        await qqbot_bot_module.client.close()
    return cleanup.await_count == 1 and stop_worker.await_count == 1 and sdk_close.await_count == 1


async def _test_qqbot_close_releases_adapter_tasks_and_waiters():
    context_manager = qqbot_bot_module.QQBotContextManager
    session_id = "shutdown-typing"
    queue_key = "group|shutdown-target"
    state = _TypingState()
    send_started = asyncio.Event()
    never_finishes = asyncio.Event()

    async def typing_worker():
        await state.finished.wait()

    async def blocked_send():
        send_started.set()
        await never_finishes.wait()
        return ["unexpected"]

    typing_task = asyncio.create_task(typing_worker())
    queue = _MessageSendQueue()
    loop = asyncio.get_running_loop()
    active_future = loop.create_future()
    pending_future = loop.create_future()
    prepared = _PreparedMessage(
        SimpleNamespace(scope="group", target_id="shutdown-target"),
        blocked_send,
        has_payload=True,
    )
    queue.pending.extend(
        [
            _QueuedMessage(
                active_future,
                prepared,
                1,
                typing_prompt=False,
                typing_state=None,
            ),
            _QueuedMessage(
                pending_future,
                prepared,
                2,
                typing_prompt=False,
                typing_state=None,
            ),
        ]
    )
    context_manager.typing_states[session_id] = state
    context_manager.typing_tasks[session_id] = typing_task
    context_manager.message_send_queues[queue_key] = queue
    queue.worker = asyncio.create_task(context_manager._process_message_send_queue(queue_key, queue))
    await asyncio.wait_for(send_started.wait(), timeout=1 * TIME_SCALE)

    cleanup = AsyncMock()
    stop_worker = AsyncMock()
    sdk_close = AsyncMock()
    try:
        with (
            patch.object(qqbot_bot_module, "client_cleanup", new=cleanup),
            patch.object(qqbot_bot_module.QQBotFetchedContextManager, "stop_task_processor", new=stop_worker),
            patch.object(botpy.Client, "close", new=sdk_close),
        ):
            await qqbot_bot_module.client.close()

        return (
            cleanup.await_count == 1
            and stop_worker.await_count == 1
            and sdk_close.await_count == 1
            and state.finished.is_set()
            and typing_task.done()
            and queue.worker.done()
            and active_future.done()
            and not active_future.cancelled()
            and active_future.result() == []
            and pending_future.done()
            and not pending_future.cancelled()
            and pending_future.result() == []
            and not context_manager.typing_states
            and not context_manager.typing_tasks
            and not context_manager.message_send_queues
        )
    finally:
        state.finished.set()
        never_finishes.set()
        if queue.worker and not queue.worker.done():
            queue.worker.cancel()
        await asyncio.gather(typing_task, queue.worker, return_exceptions=True)
        context_manager.typing_states.pop(session_id, None)
        context_manager.typing_tasks.pop(session_id, None)
        context_manager.message_send_queues.pop(queue_key, None)
        context_manager.prepare_start()


@func_case
async def test_platform_shutdown(tester: Tester):
    """平台退出时必须释放核心客户端与 SDK 资源。"""
    await tester.test(_test_web_lifespan_cleans_up_normally, "Web lifespan 正常退出时清理客户端")
    await tester.test(_test_web_lifespan_cleans_up_after_application_error, "Web lifespan 异常退出时清理客户端")
    await tester.test(_test_onebot_shutdown_stops_worker_and_cleans_core, "OneBot 退出时停止 worker 并清理")
    await tester.test(
        _test_onebot_shutdown_releases_typing_tasks_and_cache,
        "OneBot 退出时释放输入状态任务与缓存",
    )
    await tester.test(_test_qqbot_close_stops_worker_and_cleans_core, "QQBot 关闭时停止 worker 并清理")
    await tester.test(
        _test_qqbot_close_releases_adapter_tasks_and_waiters,
        "QQBot 关闭时释放适配器任务与发送等待者",
    )
    return tester
