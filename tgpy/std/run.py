"""
name: run
origin: tgpy://builtin_module/run
priority: 550
"""

from pathlib import Path

from pyrogram.types import Message

from tgpy import Context
from tgpy._core.utils import convert_result, format_traceback
from tgpy.api import constants, tgpy_eval
from tgpy.api.parse_tgpy_message import parse_tgpy_message

ctx: Context


async def run() -> str | None:
    original: Message = ctx.msg.reply_to_message
    if original is None:
        return 'Use this function in reply to a message'
    message_data = parse_tgpy_message(original)
    if message_data.is_tgpy_message:
        code = message_data.code
    elif original.document:
        file_path = await original.download()
        try:
            code = Path(file_path).read_text(encoding='utf-8')
        except Exception:
            return 'Failed to read file attachment'
    else:
        return 'No code found in reply message'
    # Execute the code in background and return the result
    try:
        eval_result = await tgpy_eval(code, message=None, filename=None)
        result = convert_result(eval_result.result)
        output = eval_result.output

        # Format the result for return
        if result is not None and output:
            return f"{result}\n\n{output}"
        elif result is not None:
            return str(result)
        elif output:
            return output
        else:
            return "Code executed successfully (no output)"

    except Exception:
        exc, constants['exc'] = format_traceback()
        return f"Error executing code:\n{exc}"


__all__ = ['run']