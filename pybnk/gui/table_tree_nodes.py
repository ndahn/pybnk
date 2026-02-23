from typing import Generator, Callable, Any
from contextlib import contextmanager
from dataclasses import dataclass
import dearpygui.dearpygui as dpg


INDENT_STEP = 14  # actually depends on font size


@dataclass
class RowDescriptor:
    level: int
    row: str = None
    table: str = None
    node: str = None
    selectable: str = None
    is_lazy: bool = False
    callback: Callable = None
    user_data: Any = None


def _get_descriptor(row: str) -> RowDescriptor:
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
    return desc is not None and desc.is_lazy


def is_foldable_row_expanded(row: str) -> bool:
    desc = _get_descriptor(row)
    return desc is not None and desc.node is not None and dpg.get_value(desc.node)


def get_row_level(row: str, default: int = 0) -> int:
    desc = _get_descriptor(row)
    return desc.level if desc else default


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
    if not is_foldable_row(row):
        return True

    desc = _get_descriptor(row)
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


def get_foldable_row_parent(table: str, row: int | str) -> int:
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
                desc.level += indent_level


def set_foldable_row_status(row: str, expanded: bool) -> None:
    if not is_foldable_row(row) or is_foldable_row_leaf(row):
        return

    if is_foldable_row_expanded(row) == expanded:
        return

    desc = _get_descriptor(row)
    if not desc:
        return

    if desc.is_lazy:
        dpg.set_value(desc.node, expanded)
        _on_lazy_node_clicked(row, expanded, desc)
    else:
        dpg.set_value(desc.selectable, not expanded)
        _on_row_clicked(desc.selectable, expanded, desc)


@contextmanager
def table_tree_node(
    label: str,
    *,
    table: str = None,
    folded: bool = True,
    tag: str = 0,
    before: str = 0,
    callback: Callable[[str, bool, RowDescriptor], None] = None,
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

    descriptor = RowDescriptor(
        level=cur_level,
        row=tag,
        table=table,
        node=tree_node,
        selectable=selectable,
        callback=callback,
        user_data=user_data,
    )

    with dpg.table_row(
        parent=table,
        tag=tag,
        before=before,
        user_data=descriptor,
        show=show,
    ):
        with dpg.group(horizontal=True, horizontal_spacing=0):
            dpg.add_selectable(
                span_columns=True,
                callback=_on_row_clicked,
                user_data=descriptor,
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
    row = f"{tag}_foldable_row"
    show = is_row_index_visible(table, cur_level)

    descriptor = RowDescriptor(level=cur_level, row=row, table=table)

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

    print("###", user_data, cur_level)

    descriptor = RowDescriptor(
        level=cur_level,
        row=tag,
        table=table,
        node=tree_node,
        selectable=selectable,
        is_lazy=True,
        callback=content_callback,
        user_data=user_data,
    )

    with dpg.table_row(
        parent=table,
        tag=tag,
        before=before,
        user_data=descriptor,
        show=show,
    ):
        with dpg.group(horizontal=True, horizontal_spacing=0):
            dpg.add_selectable(
                span_columns=True,
                callback=_on_lazy_node_clicked,
                user_data=descriptor,
                tag=selectable,
            )
            dpg.add_tree_node(
                tag=tree_node,
                label=label,
                indent=cur_level * INDENT_STEP,
                default_open=False,
            )

    return tree_node


def _on_row_clicked(sender: str, value: Any, desc: RowDescriptor):
    # Make sure it happens quickly and without flickering
    with dpg.mutex():
        dpg.set_value(sender, False)

        row = desc.row
        table = desc.table
        is_leaf = desc.node is None
        is_expanded = not dpg.get_value(desc.node) if not is_leaf else False

        # Toggle the node's "expanded" status
        if not is_leaf:
            dpg.set_value(desc.node, is_expanded)

        # Handle lazy nodes: they manage their own children
        if desc.is_lazy:
            _on_lazy_node_clicked(row, is_expanded, desc)
            return

        # Call user callback for regular nodes
        if desc.callback:
            desc.callback(row, is_leaf or is_expanded, desc.user_data)

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


def _on_lazy_node_clicked(sender: str, expanded: bool, desc: RowDescriptor):
    row = desc.row
    table = desc.table
    anchor = get_next_foldable_row_sibling(table, row)
    indent_level = desc.level + 1

    if expanded:
        with apply_row_indent(table, indent_level, row, until=anchor):
            desc.callback(sender, anchor, desc.user_data)
    else:
        child_rows = list(get_foldable_child_rows(table, row))

        until = anchor
        if isinstance(until, str):
            until = dpg.get_alias_id(anchor)

        for child_row in child_rows:
            if until != 0 and child_row == until:
                break

            dpg.delete_item(child_row)