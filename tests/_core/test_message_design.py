import asyncio
from dataclasses import dataclass, field
from types import SimpleNamespace

import pytest
from pyrogram import Client, raw
from pyrogram.enums import MessageEntityType
from pyrogram.types import MessageEntity

from tgpy._core import message_design
from tgpy.api.utils import Utf16CodepointsWrapper


@dataclass
class FakeMessage:
    edited_text: str | None = None
    edited_entities: list | None = None

    async def edit_text(self, *, text, entities, link_preview_options):
        self.edited_text = text
        self.edited_entities = entities
        return self


class UnexpectedParser:
    async def parse(self, *args, **kwargs):
        raise AssertionError('Kurigram discarded explicit message entities')


class RecordingClient:
    edit_message_text = Client.edit_message_text
    link_preview_options = None
    parser = UnexpectedParser()

    def __init__(self):
        self.request = None

    async def resolve_peer(self, chat_id):
        return raw.types.InputPeerSelf()

    async def invoke(self, request, **kwargs):
        self.request = request
        return SimpleNamespace(updates=[])


@dataclass
class IntegratedFakeMessage:
    client: RecordingClient
    chat: object = field(default_factory=lambda: SimpleNamespace(id=1))
    id: int = 1

    async def edit_text(self, **kwargs):
        await self.client.edit_message_text(
            chat_id=self.chat.id,
            message_id=self.id,
            **kwargs,
        )
        return self


@pytest.mark.parametrize(
    ('result', 'output', 'traceback', 'expected'),
    [
        (None, '', '', '1 + 1\n\nTGPy>'),
        (None, 'printed\n', '', '1 + 1\n\nTGPy> printed'),
        (None, '', 'ValueError', '1 + 1\n\nTGPy> ValueError'),
        ('2', 'printed', 'ValueError', '1 + 1\n\nTGPy> 2\n\nprinted\n\nValueError'),
    ],
)
def test_edit_message_formats_nonempty_parts(
    monkeypatch, result, output, traceback, expected
):
    monkeypatch.setattr(
        message_design.reactions_fix, 'update_hash', lambda *a, **k: None
    )
    message = FakeMessage()

    asyncio.run(
        message_design.edit_message(
            message,
            '  1 + 1  ',
            result,
            output=output,
            traceback=traceback,
        )
    )

    assert message.edited_text == expected
    assert 'None' not in message.edited_text


def test_edit_message_uses_utf16_entity_offsets(monkeypatch):
    monkeypatch.setattr(
        message_design.reactions_fix, 'update_hash', lambda *a, **k: None
    )
    message = FakeMessage()

    asyncio.run(message_design.edit_message(message, '"😀"', '😀', output='done'))

    entities = message.edited_entities
    assert [entity.type for entity in entities] == [
        MessageEntityType.PRE,
        MessageEntityType.BOLD,
        MessageEntityType.CODE,
        MessageEntityType.CODE,
    ]
    code_length = len(Utf16CodepointsWrapper('"😀"'))
    title_offset = code_length + 2
    assert (entities[0].offset, entities[0].length) == (0, code_length)
    assert (entities[1].offset, entities[1].length) == (title_offset, len('TGPy>'))
    assert (entities[2].offset, entities[2].length) == (
        title_offset + len('TGPy>') + 1,
        2,
    )
    assert (entities[3].offset, entities[3].length) == (
        title_offset + len('TGPy>') + 1 + 2 + 2,
        len('done'),
    )


def test_edit_message_preserves_monotype_entities_through_kurigram(monkeypatch):
    monkeypatch.setattr(
        message_design.reactions_fix, 'update_hash', lambda *a, **k: None
    )
    client = RecordingClient()
    message = IntegratedFakeMessage(client)

    asyncio.run(message_design.edit_message(message, 'code', '> first\nsecond'))

    request = client.request
    assert request.message == 'code\n\nTGPy> > first\nsecond'
    assert [type(entity) for entity in request.entities] == [
        raw.types.MessageEntityPre,
        raw.types.MessageEntityBold,
        raw.types.MessageEntityCode,
    ]
    assert (request.entities[-1].offset, request.entities[-1].length) == (
        len(Utf16CodepointsWrapper('code\n\nTGPy> ')),
        len(Utf16CodepointsWrapper('> first\nsecond')),
    )


def test_edit_message_does_not_mutate_rewritten_entities(monkeypatch):
    monkeypatch.setattr(
        message_design.reactions_fix, 'update_hash', lambda *a, **k: None
    )
    message = FakeMessage()
    result_entity = MessageEntity(
        type=MessageEntityType.BOLD,
        offset=0,
        length=4,
    )

    asyncio.run(
        message_design.edit_message(
            message,
            'code',
            'text',
            result_entitites_rewrite=[result_entity],
        )
    )

    assert result_entity.offset == 0
    assert message.edited_entities[-1].offset == len('code\n\nTGPy> ')


def test_edit_message_truncates_to_telegram_utf16_limit(monkeypatch):
    monkeypatch.setattr(
        message_design.reactions_fix, 'update_hash', lambda *a, **k: None
    )
    message = FakeMessage()

    asyncio.run(message_design.edit_message(message, 'code', '😀' * 4096))

    assert len(Utf16CodepointsWrapper(message.edited_text)) <= 4096
    assert message.edited_text.endswith('…')
    assert all(
        entity.offset + entity.length <= 4096 for entity in message.edited_entities
    )
