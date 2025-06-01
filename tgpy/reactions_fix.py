"""
This module tries to fix Telegram bug/undocumented feature where
setting/removing reaction sometimes triggers message edit event.
This bug/feature introduces a security vulnerability in TGPy,
because message reevaluation can be triggered by other users.
"""

import base64
import json
from enum import Enum
from hashlib import sha256

from pyrogram.types import Message

import tgpy.api

CONFIG_BASE_KEY = 'core.reactions_fix.messages'

in_memory_hashes = {}


def get_content_hash(message: Message) -> str:
    entities = []
    if message.entities:
        for e in message.entities:
            entity_dict = {
                "type": e.type.name if hasattr(e.type, 'name') else str(e.type),
                "offset": e.offset,
                "length": e.length
            }
            if hasattr(e, 'url') and e.url:
                entity_dict["url"] = e.url
            if hasattr(e, 'language') and e.language:
                entity_dict["language"] = e.language
            entities.append(json.dumps(entity_dict))
    data = str(len(entities)) + '\n' + '\n'.join(entities) + (message.text or "")
    return base64.b64encode(sha256(data.encode('utf-8')).digest()).decode('utf-8')


class ReactionsFixResult(Enum):
    ignore = 1
    evaluate = 2
    show_warning = 3


def check_hash(message: Message) -> ReactionsFixResult:
    content_hash = get_content_hash(message)
    saved_hash = in_memory_hashes.get((
        message.chat.id,
        message.id
    )) or tgpy.api.config.get(CONFIG_BASE_KEY + f'.{message.chat.id}.{message.id}')
    if not saved_hash:
        return ReactionsFixResult.show_warning
    if saved_hash == content_hash:
        return ReactionsFixResult.ignore
    return ReactionsFixResult.evaluate


def update_hash(message: Message | None, *, in_memory: bool = False) -> None:
    if not message:
        return
    if in_memory:
        in_memory_hashes[message.chat.id, message.id] = get_content_hash(message)
    else:
        in_memory_hashes.pop((message.chat.id, message.id), None)
        tgpy.api.config.set(
            CONFIG_BASE_KEY + f'.{message.chat.id}.{message.id}',
            get_content_hash(message),
        )


__all__ = ['ReactionsFixResult', 'check_hash', 'update_hash']
