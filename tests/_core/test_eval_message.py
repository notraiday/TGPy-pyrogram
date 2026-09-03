import asyncio
import importlib
from types import SimpleNamespace

import pytest

eval_message_module = importlib.import_module('tgpy._core.eval_message')


@pytest.fixture(autouse=True)
def clear_running_messages():
    eval_message_module.running_messages.clear()
    yield
    eval_message_module.running_messages.clear()


def test_older_evaluation_does_not_remove_newer_task(monkeypatch):
    started = {name: asyncio.Event() for name in ('first', 'second')}
    finish = {name: asyncio.Event() for name in ('first', 'second')}

    async def fake_tgpy_eval(code, *args, **kwargs):
        started[code].set()
        await finish[code].wait()
        return SimpleNamespace(result=code, output='')

    async def fake_edit_message(message, code, result, **kwargs):
        return message

    monkeypatch.setattr(eval_message_module, 'tgpy_eval', fake_tgpy_eval)
    monkeypatch.setattr(
        eval_message_module.message_design, 'edit_message', fake_edit_message
    )
    message = SimpleNamespace(chat=SimpleNamespace(id=1), id=2)
    key = (message.chat.id, message.id)

    async def exercise_race():
        first = asyncio.create_task(eval_message_module.eval_message('first', message))
        await started['first'].wait()
        first_inner_task = eval_message_module.running_messages[key]

        second = asyncio.create_task(
            eval_message_module.eval_message('second', message)
        )
        await started['second'].wait()
        second_inner_task = eval_message_module.running_messages[key]
        assert second_inner_task is not first_inner_task

        finish['first'].set()
        await first
        assert eval_message_module.running_messages[key] is second_inner_task

        finish['second'].set()
        await second
        assert key not in eval_message_module.running_messages

    asyncio.run(exercise_race())
