from typing import Generator, Callable, Any, Optional
from contextlib import contextmanager
from dataclasses import dataclass
import dearpygui.dearpygui as dpg


INDENT_STEP = 14  # actually depends on font size


@dataclass
class RowDescriptor:
    level: int
    node: Optional[str] = None
    selectable: Optional[str] = None
    lazy_callback: Optional[Callable] = None
    lazy_user_data: Any = None


def _get_descriptor(row: str) -> Optional[RowDescriptor]:
    if not dpg.does_item_exist(row):
        return None
    data = dpg.get_item_user_data(row)
    return data if isinstance(data, RowDescriptor) else None


def is_foldable_row(row: str) -> bool:
    return _get_descriptor(row) is not None


def is_foldable_row_leaf(row: str) -> bool:
    desc = _get_descriptor(row)
    return desc is not None and desc.node is None


def is_lazy_foldable(row: str) -> bool:
    desc = _get_descriptor(row)
    return desc is not None and desc.lazy_callback is not None


def is_foldable_row_expanded(row: str) -> bool:
    desc = _get_descriptor(row)
    return desc is not None and desc.node is not None and dpg.get_value(desc.node)


def get_row_level(row: str, default: int = 0) -> int:
    desc = _get_descriptor(row)
    return desc.level if desc else default


def get_row_node_item(row: str) -> Optional[str]:
    desc = _get_descriptor(row)
    return desc.node if desc else None


def get_row_selectable_item(row: str) -> Optional[str]:
    desc = _get_descriptor(row)
    return desc.selectable if desc else None


def is_row_index_visible(table, row_level: int, row_idx: int = -1) -> bool:
    rows = dpg.get_item_children(table, slot=1)
    if row_idx >= 0:
        rows = rows[:row_idx]

    for parent in reversed(rows):
        desc = _get_descriptor(parent)
        if not desc:
            return True
        if desc.node is not None and desc.level < row_level:
            return dpg.get_value(desc.node)

    return True


def is_row_visible(table: str, row: str | int) -> bool:
    desc = _get_descriptor(row)
    if not desc:
        return True

    rows = dpg.get_item_children(table, slot=1)
    row_idx = rows.index(row)
    return is_row_index_visible(table, desc.level, row_idx)


def get_foldable_child_rows(table: str, row: int | str) -> Generator[str, None, None]:
    if row in (None, "", 0):
        return

    if isinstance(row, str):
        row = dpg.get_alias_id(row)

    rows = dpg.get_item_children(table, slot=1)
    row_idx = rows.index(row)

    if row_idx >= 0:
        rows = rows[row_idx + 1 :]

    for child_row in rows:
        if not is_foldable_row(child_row):
            break
        yield child_row


def get_foldable_row_parent(table: str, row: int | str) -> Optional[int]:
    if isinstance(row, str):
        row = dpg.get_alias_id(row)

    rows = dpg.get_item_children(table, slot=1)
    row_idx = rows.index(row)

    if row_idx > 0:
        rows = rows[:row_idx]

    for parent in reversed(list(rows)):
        if is_foldable_row(parent):
            return parent

    return None


def get_next_foldable_row_sibling(table: str, row: str) -> int:
    if isinstance(row, str):
        row = dpg.get_alias_id(row)

    row_level = get_row_level(row)
    rows = dpg.get_item_children(table, slot=1)
    row_idx = rows.index(row)

    if row_idx > 0:
        rows = rows[row_idx + 1 :]

    for child_row in rows:
        if get_row_level(child_row) <= row_level:
            return child_row

    return 0


def get_row_indent(table: str, row: str) -> int:
    parent = get_foldable_row_parent(table, row)
    if not parent:
        return 0
    return get_row_level(parent) * INDENT_STEP


@contextmanager
def apply_row_indent(
    table: str,
    indent_level: int,
    parent_row: str,
    until: int | str = 0,
) -> Generator[str, None, None]:
    try:
        yield
    finally:
        children = get_foldable_child_rows(table, parent_row)

        if isinstance(until, str):
            until = dpg.get_alias_id(until)

        for child_row in children:
            if until != 0 and child_row == until:
                break

            child_row_content = dpg.get_item_children(child_row, slot=1)
            if child_row_content:
                dpg.set_item_indent(child_row_content[0], indent_level * INDENT_STEP)

            desc = _get_descriptor(child_row)
            if desc:
                desc.level = indent_level


def set_foldable_row_status(row: str, expanded: bool) -> None:
    if not is_foldable_row(row) or is_foldable_row_leaf(row):
        return

    if is_foldable_row_expanded(row) == expanded:
        return

    desc = _get_descriptor(row)
    if not desc:
        return

    # We basically simulate a click on the item controlling the row
    if desc.lazy_callback:
        dpg.set_value(desc.node, expanded)
        _on_lazy_node_clicked(row, expanded, desc)
    else:
        # Will be toggled again by the click function
        dpg.set_value(desc.selectable, not expanded)
        _on_row_clicked(desc.selectable, expanded, (row, None, None))


@contextmanager
def table_tree_node(
    label: str,
    *,
    table: str = None,
    folded: bool = True,
    tag: str = 0,
    before: str = 0,
    callback: Callable[[str, bool, Any], None] = None,
    user_data: Any = None,
) -> Generator[str, None, None]:
    if not table:
        table = dpg.top_container_stack()

    if tag in (0, "", None):
        tag = dpg.generate_uuid()

    cur_level = dpg.get_item_user_data(table) or 0
    tree_node = f"{tag}_foldable_row_node"
    selectable = f"{tag}_foldable_row_selectable"
    show = is_row_index_visible(table, cur_level)

    descriptor = RowDescriptor(level=cur_level, node=tree_node, selectable=selectable)

    with dpg.table_row(
        parent=table,
        tag=tag,
        before=before,
        user_data=descriptor,
        show=show,
    ) as row:
        with dpg.group(horizontal=True, horizontal_spacing=0):
            dpg.add_selectable(
                span_columns=True,
                callback=_on_row_clicked,
                user_data=(row, callback, user_data),
                tag=selectable,
            )
            dpg.add_tree_node(
                tag=tree_node,
                label=label,
                indent=cur_level * INDENT_STEP,
                default_open=not folded,
            )

    try:
        dpg.set_item_user_data(table, cur_level + 1)
        yield tree_node
    finally:
        dpg.set_item_user_data(table, cur_level)


@contextmanager
def table_tree_leaf(
    table: str = None,
    tag: str = 0,
    before: str = 0,
) -> Generator[str, None, None]:
    if not table:
        table = dpg.top_container_stack()

    if tag in (0, "", None):
        tag = dpg.generate_uuid()

    cur_level = dpg.get_item_user_data(table) or 0
    show = is_row_index_visible(table, cur_level)

    descriptor = RowDescriptor(level=cur_level)

    try:
        with dpg.table_row(
            parent=table,
            tag=tag,
            before=before,
            user_data=descriptor,
            show=show,
        ) as row:
            yield row
    finally:
        children = dpg.get_item_children(row, slot=1)
        if children:
            dpg.set_item_indent(children[0], cur_level * INDENT_STEP)


def add_lazy_table_tree_node(
    label: str,
    content_callback: Callable,
    *,
    table: str = None,
    tag: str = 0,
    before: str = 0,
    user_data: Any,
) -> str:
    if not table:
        table = dpg.top_container_stack()

    if tag in (0, "", None):
        tag = dpg.generate_uuid()

    cur_level = dpg.get_item_user_data(table) or 0
    tree_node = f"{tag}_foldable_row_node"
    selectable = f"{tag}_foldable_row_selectable"
    show = is_row_index_visible(table, cur_level)

    descriptor = RowDescriptor(
        level=cur_level,
        node=tree_node,
        selectable=selectable,
        lazy_callback=content_callback,
        lazy_user_data=user_data,
    )

    with dpg.table_row(
        parent=table,
        tag=tag,
        before=before,
        user_data=descriptor,
        show=show,
    ) as row:
        with dpg.group(horizontal=True, horizontal_spacing=0):
            dpg.add_selectable(
                span_columns=True,
                callback=_on_row_clicked,
                user_data=(row, _on_lazy_node_clicked, descriptor),
                tag=selectable,
            )
            dpg.add_tree_node(
                tag=tree_node,
                label=label,
                indent=cur_level * INDENT_STEP,
                default_open=False,
            )

    return tree_node


def _on_row_clicked(sender, value, user_data):
    # Make sure it happens quickly and without flickering
    with dpg.mutex():
        # We don't want to highlight the selectable as "selected"
        dpg.set_value(sender, False)

        row, callback, cb_user_data = user_data
        desc = _get_descriptor(row)
        if not desc:
            return

        table = dpg.get_item_parent(row)
        is_leaf = desc.node is None
        is_expanded = not dpg.get_value(desc.node) if not is_leaf else False

        # Toggle the node's "expanded" status
        if not is_leaf:
            dpg.set_value(desc.node, is_expanded)

        if callback:
            callback(row, is_expanded, cb_user_data)

        if is_leaf:
            return

        # All children *beyond* this level (but not on this level) will be hidden
        hide_level = 10000 if is_expanded else desc.level

        for child_row in get_foldable_child_rows(table, row):
            child_desc = _get_descriptor(child_row)
            if not child_desc:
                break

            if child_desc.level <= desc.level:
                break

            if child_desc.level > hide_level:
                dpg.hide_item(child_row)
            else:
                dpg.show_item(child_row)
                if child_desc.node is not None:
                    hide_level = 10000 if dpg.get_value(child_desc.node) else child_desc.level


def _on_lazy_node_clicked(row: str, expanded: bool, user_data: RowDescriptor):
    desc = user_data
    table = dpg.get_item_parent(row)
    
    anchor = get_next_foldable_row_sibling(table, row)
    indent_level = desc.level + 1

    if expanded:
        with apply_row_indent(table, indent_level, row, until=anchor):
            desc.lazy_callback(row, anchor, desc.lazy_user_data)
    else:
        child_rows = list(get_foldable_child_rows(table, row))

        until = anchor
        if isinstance(until, str):
            until = dpg.get_alias_id(anchor)

        for child_row in child_rows:
            if until != 0 and child_row == until:
                break

            dpg.delete_item(child_row)