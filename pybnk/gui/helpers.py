from typing import Any, Callable
import inspect
import builtins
from dataclasses import dataclass
from docstring_parser import parse as doc_parse
from dearpygui import dearpygui as dpg


def create_widget(
    vtype: type,
    label: str,
    callback: Callable[[str, Any, Any], Any],
    default: Any = None,
    *,
    readonly: bool = False,
    user_data: Any = None,
    parent: str = 0,
    tag: str = 0,
) -> None:
    if vtype is bool:
        return dpg.add_checkbox(
            label=label,
            default_value=default or vtype(),
            callback=callback,
            enabled=not readonly,
            user_data=user_data,
            parent=parent,
            tag=tag,
        )
    elif vtype is int:
        return dpg.add_input_int(
            label=label,
            default_value=default or vtype(),
            callback=callback,
            readonly=readonly,
            enabled=not readonly,
            user_data=user_data,
            parent=parent,
            tag=tag,
        )
    elif vtype is float:
        return dpg.add_input_float(
            label=label,
            default_value=default or vtype(),
            callback=callback,
            readonly=readonly,
            enabled=not readonly,
            user_data=user_data,
            parent=parent,
            tag=tag,
        )
    elif vtype is str:
        return dpg.add_input_text(
            label=label,
            default_value=default or vtype(),
            callback=callback,
            readonly=readonly,
            enabled=not readonly,
            user_data=user_data,
            parent=parent,
            tag=tag,
        )
    # TODO literals and enums
    # TODO lists
    # TODO dicts


@dataclass
class FuncArg:
    undefined = object()

    name: str
    type: type
    default: Any = None
    doc: str = None


def get_function_spec(
    func: Callable, undefined: Any = FuncArg.undefined
) -> dict[str, FuncArg]:
    func_args = {}
    sig = inspect.signature(func)

    param_doc = {}
    if func.__doc__:
        parsed_doc = doc_parse(func.__doc__)
        param_doc = {p.arg_name: p.description for p in parsed_doc.params}

    # Create CLI options for click
    for param in sig.parameters.values():
        ptype = None
        default = undefined

        if param.annotation is not param.empty:
            ptype = param.annotation
            if ptype and isinstance(ptype, str):
                # If it's a primitive type we can parse it, otherwise ignore it
                # NOTE use the proper builtins module here, __builtins__ is unreliable
                ptype = getattr(builtins, ptype, None)

        if param.default is not inspect.Parameter.empty:
            default = param.default

            if ptype is None and default is not None:
                ptype = type(default)

        func_args[param.name] = FuncArg(
            param.name, ptype, default, param_doc.get(param.name)
        )

    return func_args


def center_window(window: str, parent: str = None) -> None:
    if parent:
        dpos = dpg.get_item_pos(parent)
        dsize = dpg.get_item_rect_size(parent)
    else:
        dpos = (0.0, 0.0)
        dsize = (dpg.get_viewport_width(), dpg.get_viewport_height())

    psize = dpg.get_item_rect_size(window)

    dpg.set_item_pos(
        window,
        (
            dpos[0] + (dsize[0] - psize[0]) / 2,
            dpos[1] + (dsize[1] - psize[1]) / 2,
        ),
    )
