from typing import Any, Callable
import inspect
import builtins
from dataclasses import dataclass
from docstring_parser import parse as doc_parse
from dearpygui import dearpygui as dpg

from pybnk.util import logger
from pybnk.enums import property_defaults


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


def create_properties_table(
    properties: dict[str, Any],
    on_value_changed: Callable[[dict[str, Any]], None],
    *,
    tag: str | int = 0,
    user_data: Any = None,
) -> None:
    if tag in (None, 0, ""):
        tag = dpg.generate_uuid()
    
    property_keys = list(property_defaults.keys())
    current_properties = dict(properties)

    def get_available_keys(exclude: str | None = None) -> list[str]:
        used = set(current_properties.keys())
        if exclude:
            used.discard(exclude)

        return [k for k in property_keys if k not in used]

    def refresh_table() -> None:
        dpg.delete_item(tag, children_only=True, slot=1)
        for prop, val in current_properties.items():
            add_row(prop, val)

        add_footer()

    def on_prop_type_changed(sender: int, new_key: str) -> None:
        row = dpg.get_item_parent(sender)
        siblings = dpg.get_item_children(row, slot=1)
        value_widget = siblings[1]
        old_key = next(
            k for k, combo in row_widgets.items() if combo[0] == sender
        )

        val = current_properties.pop(old_key)
        current_properties[new_key] = val
        row_widgets[new_key] = row_widgets.pop(old_key)
        dpg.configure_item(value_widget, default_value=val)
        sync_combos()

        on_value_changed(tag, dict(current_properties), user_data)

    def on_prop_value_changed(sender: int, new_val: float) -> None:
        for key, (_, value_id) in row_widgets.items():
            if value_id == sender:
                current_properties[key] = new_val
                break

        on_value_changed(tag, dict(current_properties), user_data)

    def on_add_clicked() -> None:
        available = get_available_keys()
        if not available:
            return

        new_key = available[0]
        current_properties[new_key] = property_defaults[new_key]
        refresh_table()
        on_value_changed(tag, dict(current_properties), user_data)

    def on_remove_clicked(sender: int) -> None:
        key = next(k for k, ids in row_widgets.items() if ids[2] == sender)
        current_properties.pop(key)
        refresh_table()
        on_value_changed(tag, dict(current_properties), user_data)

    def sync_combos() -> None:
        for key, (combo_id, _, __) in row_widgets.items():
            dpg.configure_item(combo_id, items=get_available_keys(exclude=key))

    def add_row(prop: str, val: float) -> None:
        with dpg.table_row(parent=tag):
            combo_id = dpg.add_combo(
                items=get_available_keys(exclude=prop),
                default_value=prop,
                width=150,
                callback=on_prop_type_changed,
            )
            value_id = dpg.add_input_double(
                default_value=val,
                width=150,
                callback=on_prop_value_changed,
            )
            remove_id = dpg.add_button(label="-", callback=on_remove_clicked)
            row_widgets[prop] = (combo_id, value_id, remove_id)

    def add_footer() -> None:
        with dpg.table_row(parent=tag):
            dpg.add_button(label="+ Add Property", callback=on_add_clicked)

    row_widgets: dict[str, tuple[int, int, int]] = {}

    # The actual widgets
    dpg.add_spacer(height=5)
    dpg.add_text("Properties")

    with dpg.table(header_row=False, policy=dpg.mvTable_SizingFixedFit, tag=tag):
        dpg.add_table_column(label="Property", width_stretch=True, init_width_or_weight=100)
        dpg.add_table_column(label="Value", width_stretch=True, init_width_or_weight=100)
        dpg.add_table_column(label="", width_fixed=True)
        for prop, val in current_properties.items():
            add_row(prop, val)
        add_footer()

    dpg.add_spacer(height=5)


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
