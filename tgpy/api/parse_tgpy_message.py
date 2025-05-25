from dataclasses import dataclass

from pyrogram.types import Message

from tgpy._core.message_design import Utf16CodepointsWrapper, get_title_entity


@dataclass
class MessageParseResult:
    is_tgpy_message: bool
    code: str | None
    result: str | None


def parse_tgpy_message(message: Message) -> MessageParseResult:
    e = get_title_entity(message) 
    if (
        not e
        # Likely a `TGPy error>` message
        or e.offset == 0
    ):
        return MessageParseResult(False, None, None)
    msg_text_str = message.text if message.text else "" 
    msg_text = Utf16CodepointsWrapper(msg_text_str)
    code = msg_text[: e.offset].strip()
    result = msg_text[e.offset + e.length :].strip()
    return MessageParseResult(True, code, result)


__all__ = ['MessageParseResult', 'parse_tgpy_message']
