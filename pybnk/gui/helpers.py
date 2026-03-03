from typing import Any, Callable, Literal, Type, get_args, get_origin
from enum import Enum, IntFlag
import inspect
import builtins
from pathlib import Path
from dataclasses import dataclass
from docstring_parser import parse as doc_parse
from dearpygui import dearpygui as dpg

from pybnk.node import Node, NodeLike
from pybnk.util import logger
from pybnk.enums import property_defaults
from pybnk.gui.dialogs.file_dialog import open_multiple_dialog
from pybnk.gui.dialogs.select_node_dialog import select_node_dialog


def create_widget(
    value_type: type,
    label: str,
    callback: Callable[[str, Any, Any], None],
    *,
    default: Any = None,
    choices: list[str | tuple[str | Any]] = None,
    readonly: bool = False,
    flags_as_int: bool = False,
    accept_on_enter: bool = False,
    parent: str = 0,
    tag: str = 0,
    user_data: Any = None,
    **kwargs,
) -> str:
    if tag in (None, 0, ""):
        tag = dpg.generate_uuid()

    if isinstance(value_type, type) and issubclass(value_type, IntFlag):
        if flags_as_int:
            value_type = int
        else:
            # We have specific support for flags already
            return create_flag_checkboxes(
                value_type,
                callback,
                readonly=readonly,
                base_tag=tag,
                parent=parent,
                active_flags=default if default is not None else 0,
                user_data=user_data,
            )

    # Support enums by extracting their choices
    if isinstance(value_type, type) and issubclass(value_type, Enum):
        choices = [(v.name, v.value) for v in value_type]
        if default is not None and not isinstance(default, str):
            default = value_type(default).name

    # If choices is provided we treat this as a Literal
    if choices:
        orig_callback = callback
        items = [x[0] if isinstance(x, tuple) else x for x in choices]

        def new_callback(sender: str, data: str, cb_user_data: Any):
            # Find the selected item in the original choices list
            index = items.index(data)
            selected = choices[index]

            # If a tuple was provided the first element is only a label,
            # the actual value is in the second element
            if isinstance(selected, tuple):
                selected = selected[1]

            orig_callback(sender, selected, user_data)

        value_type = Literal[tuple(items)]
        callback = new_callback

    # The simple types
    type_origin = get_origin(value_type)
    if type_origin == Literal:
        choices = get_args(value_type)
        items = [str(c) for c in choices]

        if default in choices:
            default = items[choices.index(default)]

        dpg.add_combo(
            items,
            label=label,
            default_value=default if default is not None else "",
            enabled=not readonly,
            callback=callback,
            parent=parent,
            tag=tag,
            **kwargs,
            user_data=user_data,
        )
    elif value_type is int:
        dpg.add_input_int(
            label=label,
            default_value=int(default) if default is not None else 0,
            readonly=readonly,
            enabled=not readonly,
            callback=callback,
            on_enter=accept_on_enter,
            parent=parent,
            tag=tag,
            user_data=user_data,
            **kwargs,
        )
    elif value_type is float:
        dpg.add_input_float(
            label=label,
            default_value=float(default) if default is not None else 0.0,
            readonly=readonly,
            enabled=not readonly,
            callback=callback,
            on_enter=accept_on_enter,
            parent=parent,
            tag=tag,
            user_data=user_data,
            **kwargs,
        )
    elif value_type is bool:
        dpg.add_checkbox(
            label=label,
            default_value=bool(default) if default is not None else False,
            enabled=not readonly,
            callback=callback,
            parent=parent,
            tag=tag,
            user_data=user_data,
            **kwargs,
        )
    elif not type_origin and value_type in (type(None), str):
        dpg.add_input_text(
            label=label,
            default_value=str(default) if default is not None else "",
            readonly=readonly,
            enabled=not readonly,
            callback=callback,
            on_enter=accept_on_enter,
            parent=parent,
            tag=tag,
            user_data=user_data,
            **kwargs,
        )
    elif value_type is NodeLike or issubclass(value_type, Node):
        if isinstance(default, Node):
            default = default.id
        
        if default is None:
            default = "0"

        default = str(default)

        def select_node() -> None:
            select_node_dialog()  # TODO needs soundbank
            pass

        with dpg.group(horizontal=True, parent=parent):
            dpg.add_input_text(
                default_value=default,
                decimal=True,
                readonly=readonly,
                enabled=not readonly,
                user_data=user_data,
                tag=tag,
            )
            dpg.add_button(
                arrow=True,
                direction=dpg.mvDir_Right,
                callback=select_node,
            )
            dpg.add_text(label)
    else:
        raise ValueError(f"Could not handle type {value_type} for {label}")

    return tag


def create_flag_checkboxes(
    flag_type: Type[IntFlag],
    callback: Callable[[str, int, Any], None],
    *,
    readonly: bool = False,
    base_tag: str = 0,
    parent: str = 0,
    active_flags: int = 0,
    user_data: Any = None,
) -> str:
    if base_tag in (None, 0, ""):
        base_tag = dpg.generate_uuid()

    zero_name = flag_type(0).name or "DISABLED"

    def on_flag_changed(sender: str, checked: bool, flag: IntFlag):
        nonlocal active_flags

        if checked:
            # Checking 0 will disable all other flags
            if flag == 0:
                active_flags = flag_type(0)
            else:
                active_flags |= flag
        else:
            # Prevent disabling 0
            if flag == 0:
                dpg.set_value(f"{base_tag}_{zero_name}", True)
                return

            active_flags &= ~flag

        # Flags are not required to have a 0 mapping
        if dpg.does_item_exist(f"{base_tag}_{zero_name}"):
            # 0 disables all other flags and enables 0
            if active_flags == 0:
                for flag in flag_type:
                    dpg.set_value(f"{base_tag}_{flag.name}", False)
                dpg.set_value(f"{base_tag}_{zero_name}", True)
            # 0 is disabled by any other flag
            else:
                dpg.set_value(f"{base_tag}_{zero_name}", False)

        dpg.set_value(f"{base_tag}_numeric", active_flags)

        if callback:
            callback(base_tag, active_flags, user_data)

    def set_from_int(sender: str, new_value: int, user_data: Any):
        new_flags = flag_type(new_value)
        for flag in flag_type:
            active = flag in new_flags
            if flag.value == 0 and new_flags > 0:
                active = False

            dpg.set_value(f"{base_tag}_{flag.name}", active)
            on_flag_changed(sender, active, flag)

    if not isinstance(active_flags, flag_type):
        try:
            active_flags = flag_type(active_flags)
        except ValueError:
            logger.error(
                f"{active_flags} is not valid for flag type {flag_type.__name__}"
            )
            active_flags = 0

    with dpg.group(parent=parent, tag=base_tag):
        dpg.add_input_int(
            default_value=active_flags,
            callback=set_from_int,
            readonly=readonly,
            enabled=not readonly,
            tag=f"{base_tag}_numeric",
        )

        for flag in flag_type:
            if flag == 0:
                # 0 is in every flag
                active = active_flags == 0
            else:
                active = flag in active_flags

            dpg.add_checkbox(
                default_value=active,
                callback=on_flag_changed,
                enabled=not readonly,
                label=flag.name,
                tag=f"{base_tag}_{flag.name}",
                user_data=flag,
            )

    return base_tag


def create_properties_table(
    initial_properties: dict[str, Any],
    on_value_changed: Callable[[str, dict[str, Any], Any], None],
    *,
    tag: str | int = 0,
    user_data: Any = None,
) -> None:
    if tag in (None, 0, ""):
        tag = dpg.generate_uuid()

    property_keys = list(property_defaults.keys())
    current_properties = dict(initial_properties)

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
        old_key = next(k for k, combo in row_widgets.items() if combo[0] == sender)
        current_properties.pop(old_key)

        val = property_defaults[new_key]
        current_properties[new_key] = val
        row_widgets[new_key] = row_widgets.pop(old_key)
        dpg.configure_item(value_widget, default_value=val)
        sync_combos()

        on_value_changed(tag, dict(current_properties), user_data)

    def on_prop_value_changed(sender: int, new_val: float) -> None:
        for key, (_, value_id, _) in row_widgets.items():
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
                width=-1,
                callback=on_prop_type_changed,
            )
            value_id = dpg.add_input_double(
                default_value=val,
                width=-1,
                callback=on_prop_value_changed,
            )
            remove_id = dpg.add_button(label="-", callback=on_remove_clicked)
            row_widgets[prop] = (combo_id, value_id, remove_id)

    def add_footer() -> None:
        with dpg.table_row(parent=tag):
            dpg.add_button(label="+ Add Property", callback=on_add_clicked)

    row_widgets: dict[str, tuple[int, int, int]] = {}

    # The actual widgets
    dpg.add_text("Properties")

    with dpg.table(
        header_row=False,
        policy=dpg.mvTable_SizingFixedFit,
        borders_outerH=True,
        borders_outerV=True,
        tag=tag,
    ):
        dpg.add_table_column(
            label="Property", width_stretch=True, init_width_or_weight=100
        )
        dpg.add_table_column(
            label="Value", width_stretch=True, init_width_or_weight=100
        )
        dpg.add_table_column(label="", width_fixed=True)
        for prop, val in current_properties.items():
            add_row(prop, val)
        add_footer()


def create_filepaths_table(
    initial_paths: list[Path],
    on_value_changed: Callable[[str, list[Path], Any], None],
    *,
    title: str = "Files",
    filetypes: dict[str, str] = None,
    tag: str | int = 0,
    user_data: Any = None,
) -> None:
    if tag in (None, 0, ""):
        tag = dpg.generate_uuid()

    current_paths: list[Path] = list(initial_paths)

    def refresh_table() -> None:
        dpg.delete_item(tag, children_only=True, slot=1)
        for path in current_paths:
            add_row(path)
        add_footer()

    def on_remove_clicked(sender: int) -> None:
        idx = next(i for i, ids in enumerate(row_widgets) if ids[1] == sender)
        current_paths.pop(idx)
        row_widgets.pop(idx)
        refresh_table()
        on_value_changed(tag, list(current_paths), user_data)

    def on_add_clicked() -> None:
        result = open_multiple_dialog(title=title, filetypes=filetypes)
        if not result:
            return

        current_paths.extend(Path(p) for p in result)
        refresh_table()
        on_value_changed(tag, list(current_paths), user_data)

    def add_row(path: Path) -> None:
        with dpg.table_row(parent=tag):
            text_id = dpg.add_input_text(
                default_value=f"{path.parent.name}/{path.name}",
                enabled=False,
                readonly=True,
                width=-1,
            )
            remove_id = dpg.add_button(label="-", callback=on_remove_clicked)
            row_widgets.append((text_id, remove_id))

    def add_footer() -> None:
        with dpg.table_row(parent=tag):
            dpg.add_button(label="+ Add Files", callback=on_add_clicked)

    row_widgets: list[tuple[int, int]] = []

    # The actual widgets
    dpg.add_text(title)

    with dpg.table(
        header_row=False,
        policy=dpg.mvTable_SizingFixedFit,
        borders_outerH=True,
        borders_outerV=True,
        tag=tag,
    ):
        dpg.add_table_column(label="File", width_stretch=True, init_width_or_weight=100)
        dpg.add_table_column(label="")

        for path in current_paths:
            add_row(path)
        add_footer()


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
