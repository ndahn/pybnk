from typing import Any, Callable
from dearpygui import dearpygui as dpg


def create_widget(
    value: Any,
    label: str,
    callback: Callable[[str, Any, Any], Any],
    readonly: bool = False,
    user_data: Any = None,
    tag: str = 0,
) -> None:
    if isinstance(value, bool):
        return dpg.add_checkbox(
            label=label,
            default_value=value,
            callback=callback,
            enabled=not readonly,
            user_data=user_data,
            tag=tag,
        )
    elif isinstance(value, int):
        return dpg.add_input_int(
            label=label,
            default_value=value,
            callback=callback,
            readonly=readonly,
            enabled=not readonly,
            user_data=user_data,
            tag=tag,
        )
    elif isinstance(value, float):
        return dpg.add_input_float(
            label=label,
            default_value=value,
            callback=callback,
            readonly=readonly,
            enabled=not readonly,
            user_data=user_data,
            tag=tag,
        )
    elif isinstance(value, str):
        return dpg.add_input_text(
            label=label,
            default_value=value,
            callback=callback,
            readonly=readonly,
            enabled=not readonly,
            user_data=user_data,
            tag=tag,
        )
    # TODO literals and enums
    # TODO lists
    # TODO dicts
