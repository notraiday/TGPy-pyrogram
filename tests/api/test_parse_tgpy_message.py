from types import SimpleNamespace

from pyrogram.enums import MessageEntityType
from pyrogram.types import MessageEntity

from tgpy.api.parse_tgpy_message import parse_tgpy_message


def test_parse_tgpy_message_handles_utf16_code_entity():
    message = SimpleNamespace(
        text='print("😀")\n\nTGPy> None',
        caption=None,
        entities=[
            MessageEntity(
                type=MessageEntityType.PRE,
                offset=0,
                length=11,
                language='python',
            )
        ],
    )

    result = parse_tgpy_message(message)

    assert result.is_tgpy_message
    assert result.code == 'print("😀")'
    assert result.result == 'None'


def test_parse_tgpy_message_rejects_plain_text():
    message = SimpleNamespace(text='print(1)', caption=None, entities=[])

    result = parse_tgpy_message(message)

    assert not result.is_tgpy_message
    assert result.code is None
    assert result.result is None
