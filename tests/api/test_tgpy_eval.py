import asyncio
import importlib
from contextvars import Context, ContextVar
from types import SimpleNamespace

from tgpy.api import tgpy_eval as tgpy_eval_func

tgpy_eval_module = importlib.import_module('tgpy.api.tgpy_eval')


def test_tgpy_eval_uses_explicit_empty_context(monkeypatch):
    marker = ContextVar('marker', default='default')
    explicit_context = Context()

    async def fake_tgpy_eval(*args, **kwargs):
        return SimpleNamespace(result=marker.get(), output='')

    monkeypatch.setattr(tgpy_eval_module, '_tgpy_eval', fake_tgpy_eval)
    marker.set('ambient')

    result = asyncio.run(tgpy_eval_func('marker', ctx=explicit_context))

    assert result.result == 'default'


def test_tgpy_eval_copies_ambient_context_by_default(monkeypatch):
    marker = ContextVar('marker', default='default')

    async def fake_tgpy_eval(*args, **kwargs):
        return SimpleNamespace(result=marker.get(), output='')

    monkeypatch.setattr(tgpy_eval_module, '_tgpy_eval', fake_tgpy_eval)
    marker.set('ambient')

    result = asyncio.run(tgpy_eval_func('marker'))

    assert result.result == 'ambient'
