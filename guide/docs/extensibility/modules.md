---
description: Modules help you keep functions, classes, or constants when TGPy restarts.
---

# Modules

You may want to define functions, classes, or constants to reuse later. If you want to keep them when TGPy restarts,
save their definitions to modules.

Modules are code snippets that run at every startup.

## Add a module

Say TGPy ran your message. Then you can reply to your message with this method:

```python
modules.add(name)
```

Alternatively, you can add a module from a string with `#!python modules.add(name, source)`.

You can also add a module by replying to a file attachment (e.g., a .py file).

!!! example

    1. Define a square function:

        <div class="tgpy-code-block">
        ```python
        def square(x):
           return x * x
        ```
        <hr>
        ```
        None
        ```
        </div>
    
    2. Save the definition to modules:

        <div class="tgpy-code-block">
        ```python
        # in reply to the previous message
        modules.add('square')
        ```
        <hr>
        ```
        Added module 'square'.
        The module will be executed every time TGPy starts.
        ```
        </div>

!!! Info

    If a module with this name already exists, its code will be replaced.

## Remove a module

Remove a module by name:

```python
modules.remove(name)
```

## Manage modules

Use the string value of `modules` to list all of your modules:

```python
modules
```

The `modules` object provides handy ways to manage your modules. You can iterate over it to get names of your
modules or use `modules[name]` to get info about the module.

### Send a module file and its metadata

You can send a saved module file along with its metadata back to the chat by calling its `send()` method:

```python
modules['square'].send()
```

## Storage

Modules are stored as separate Python files in <code>[tgpy/](/installation/#data-storage)modules</code> directory. You
can safely edit them manually.

Modules run each time TGPy starts. By default, they run in the order they were added.

Each module file contains [module metadata](/reference/module_metadata).

## Features

By default, all variables from a module are saved for future use. You can specify ones the with the `__all__` variable.

You can also specify external packages to install before running the module by adding a `requirements` key to the module metadata. For example:

```python
"""
name: example
requirements:
  - requests
  - numpy>=1.20
priority: 1655584820
"""
# module code here
```

## Standard modules

TGPy has a number of features implemented via standard modules, such as `#!python ping()`
and `#!python restart()` functions.
You may want to disable these features, for example to reimplement them. Use the `#!python core.disabled_modules` config 
key to specify the disabled modules. For example, you can use the following code to disable the `prevent_eval` module which
provides [// and cancel](/reference/code_detection/#cancel-evaluation) features:

```python
tgpy.api.config.set('core.disabled_modules', ['prevent_eval'])
```

[All standard modules in the repo](https://github.com/tm-a-t/TGPy/tree/master/tgpy/std)
