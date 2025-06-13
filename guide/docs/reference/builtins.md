---
description: Reference on built-in functions and objects.
---

# Builtins

## Control functions

| Function             | Description                                                                           |
|----------------------|---------------------------------------------------------------------------------------|
| `#!python ping()`    | Return basic info about your TGPy instance. Use `ping()` to check if TGPy is running. |
| `#!python restart()` | Restart TGPy.                                                                         |
| `#!python update()`  | Download the latest version of TGPy, update, and restart the instance.                |

## Pyrogram objects

| Object            | Description                                                                                                                                                         |
|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `#!python client` | The Pyrogram client. [See Pyrogram Client reference](https://docs.pyrogram.org/api/client)                                    |
| `#!python msg`    | The current message. [See Pyrogram Message reference](https://docs.pyrogram.org/api/types/message)                          |
| `#!python orig`   | Original message: the message you replied to. [See Pyrogram Message reference](https://docs.pyrogram.org/api/types/message) |

!!! note

    TGPy fetches `orig` message only if your code uses the `orig` variable. That’s because it requires an additional
    request to Telegram API.

## Modules

[Read on modules](/extensibility/modules/)

| Object                                       | Description                                                                                                |
|----------------------------------------------|------------------------------------------------------------------------------------------------------------|
| `#!python modules`                           | Object for [module management](/extensibility/modules/#manage-modules).                                                 |
| `#!python modules.add(name: str, code: str)` | Add the given code as a module. If `code` isn’t specified, the code from the `orig` message will be added. |
| `#!python modules.remove(name: str)`         | Remove the module named `name`.                                                                            |

## Context

[Read on the `ctx` object](../extensibility/context.md)

| Object                          | Description                                                                              |
|---------------------------------|------------------------------------------------------------------------------------------|
| `#!python ctx.msg`              | The message where the code is running.                                                   |
| `#!python ctx.is_module`        | `True` if the code is running from a module.                                             |
| `#!python ctx.is_manual_output` | Can be set to True to prevent the last message edit by TGPy so you can edit it yourself. |
