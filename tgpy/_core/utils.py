import sys
import traceback

from pyrogram.types.object import Object as PyrogramObject


def convert_result(result):
    if isinstance(result, PyrogramObject):
        if hasattr(result, 'to_dict'):
            return result.to_dict()
        return str(result)

    return result


def format_traceback() -> tuple[str, str]:
    _, exc_value, exc_traceback = sys.exc_info()
    exc_traceback = exc_traceback.tb_next.tb_next
    te = traceback.TracebackException(
        type(exc_value), exc_value, exc_traceback, compact=True
    )
    return ''.join(te.format_exception_only()), ''.join(te.format())
