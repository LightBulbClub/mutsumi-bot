from dataclasses import dataclass

from core.builtins.bot import Bot


@dataclass
class EventAdapter:
    user_id: str
    bot_id: str
    bot_self_id: str
    sender: dict
    text: str
    command: str
    at: str | None
    session: Bot.MessageSession

    @classmethod
    def from_session(
        cls,
        msg: Bot.MessageSession,
        text: str = "",
        command: str = "",
    ) -> "EventAdapter":
        info = msg.session_info
        return cls(
            user_id=info.sender_id or "",
            bot_id=info.client_name,
            bot_self_id=info.bot_name or "",
            sender={"nickname": info.sender_name or "Proxy"},
            text=text,
            command=command,
            at=None,
            session=msg,
        )
