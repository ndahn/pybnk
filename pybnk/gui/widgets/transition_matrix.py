from typing import Any, Callable, TypeAlias
from copy import deepcopy
from dearpygui import dearpygui as dpg

from pybnk import Soundbank
from pybnk.node_types import MusicSwitchContainer, MusicRandomSequenceContainer
from pybnk.gui.dialogs.edit_transition_dialog import edit_transition_dialog


TransitionNode: TypeAlias = MusicSwitchContainer | MusicRandomSequenceContainer

_base_transition_rule = {
    "source_transition_rule_count": 1,
    "source_ids": [-1],
    "destination_transition_rule_count": 1,
    "destination_ids": [-1],
    "source_transition_rule": {
        "transition_time": 500,
        "fade_curve": "Linear",
        "fade_offet": 500,
        "sync_type": "Immediate",
        "clue_filter_hash": 0,
        "play_post_exit": 0,
    },
    "destination_transition_rule": {
        "transition_time": 500,
        "fade_curve": "Linear",
        "fade_offet": 0,
        "clue_filter_hash": 0,
        "jump_to_id": 0,
        "jump_to_type": 0,
        "entry_type": 0,
        "play_pre_entry": 0,
        "destination_match_source_cue_name": 0,
    },
    "alloc_trans_object_flag": 0,
    "transition_object": {
        "segment_id": 0,
        "fade_out": {"transition_time": 0, "curve": "Log3", "offset": 0},
        "fade_in": {"transition_time": 0, "curve": "Log3", "offset": 0},
        "play_pre_entry": 0,
        "play_post_exit": 0,
    },
}


def add_transition_matrix(
    bnk: Soundbank,
    node: TransitionNode,
    on_transition_rules_changed: Callable[[str, TransitionNode, Any], None] = None,
    *,
    short_transition: int = 0,
    long_transition: int = 3000,
    parent: str | int = 0,
    tag: str | int = 0,
    user_data: Any = None,
) -> str | int:
    if not tag:
        tag = dpg.generate_uuid()

    cell_size = 30
    table_h = min(400, cell_size * 1.8 + len(node.children) * (cell_size + 5))

    def get_transition_time_color(transition_time: int) -> tuple[int, int, int, int]:
        # Interpolate from red (low time) to blue (high time)
        if long_transition == short_transition:
            t = 0.5
        else:
            t = (transition_time - short_transition) / (
                long_transition - short_transition
            )

        r = int(200 * (1 - t))
        g = int(60 * (1 - abs(t - 0.5) * 2))
        b = int(200 * t)

        return (r, g, b, 200)

    def find_best_rule(
        rules: list[dict],
        src_id: int,
        dst_id: int,
    ) -> tuple[int, dict]:
        # Return the most specific rule for a (src, dst) pair.
        # Specificity:
        #  - exact src + exact dst >
        #  - exact src + wildcard >
        #  - wildcard + exact dst >
        #  - wildcard + wildcard
        # Among equal specificity, first encountered wins.
        best_rule_idx = -1
        best_rule = None
        best_score = -1

        for i, rule in enumerate(rules):
            src_ids = rule.get("source_ids", [-1])
            dst_ids = rule.get("destination_ids", [-1])

            src_match = src_id in src_ids
            dst_match = dst_id in dst_ids
            src_wild = -1 in src_ids
            dst_wild = -1 in dst_ids

            if src_match and dst_match:
                score = 3
            elif src_match and dst_wild:
                score = 2
            elif src_wild and dst_match:
                score = 1
            elif src_wild and dst_wild:
                score = 0
            else:
                continue

            if score > best_score:
                best_score = score
                best_rule_idx = i
                best_rule = rule

        return (best_rule_idx, best_rule)

    def id_label(id: int) -> str:
        if id == "-1":
            return "*"

        return str(id)

    def get_cell_label(rule: dict) -> str:
        return "x" if rule.get("transition_object", {}).get("segment_id", 0) > 0 else ""

    def make_cell_theme(color: tuple[int, int, int, int]) -> int:
        theme_tag = dpg.generate_uuid()

        with dpg.theme(tag=theme_tag):
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, color)
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonHovered,
                    (
                        min(color[0] + 40, 255),
                        min(color[1] + 40, 255),
                        min(color[2] + 40, 255),
                        230,
                    ),
                )
                dpg.add_theme_color(
                    dpg.mvThemeCol_ButtonActive,
                    (
                        min(color[0] + 60, 255),
                        min(color[1] + 60, 255),
                        min(color[2] + 60, 255),
                        255,
                    ),
                )
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255, 255, 255, 255))

        return theme_tag

    def open_edit_transition_dialog(sender: str, app_data: Any, rule: dict) -> None:
        is_new = not rule
        if is_new:
            rule = deepcopy(_base_transition_rule)
            
        edit_transition_dialog(node, rule, on_rule_changed, user_data=is_new)

    def on_rule_changed(sender: str, rule: dict, is_new: bool) -> None:
        if is_new:
            node.transition_rules.append(rule)
        
        if on_transition_rules_changed:
            on_transition_rules_changed(tag, node, user_data)

        regenerate()

    def regenerate() -> None:
        dpg.delete_item(tag, children_only=True, slot=1)
        dpg.delete_item(tag, children_only=True, slot=2)

        dpg.push_container_stack(tag)

        # Row-label column (no header text — the header row shows destination IDs)
        dpg.add_table_column(width_fixed=True, init_width_or_weight=cell_size)

        children = [-1] + list(node.children)

        # One column per destination ID
        for dst in children:
            dpg.add_table_column(
                label=id_label(dst),
                angled_header=True,
                width_fixed=True,
                init_width_or_weight=cell_size,
            )

        # Non-selectable column header
        with dpg.table_row():
            dpg.add_text(label="S\\D")
            for dst in children:
                dpg.add_text(id_label(dst))

        # One row per source ID
        for src in children:
            with dpg.table_row():
                # Row header cell
                dpg.add_text(id_label(src))

                for dst in children:
                    rule_idx, rule = find_best_rule(node.transition_rules, src, dst)

                    if rule:
                        src_trans_time = rule["source_transition_rule"][
                            "transition_time"
                        ]
                        dst_trans_time = rule["destination_transition_rule"][
                            "transition_time"
                        ]
                        total_time = src_trans_time + dst_trans_time
                        color = get_transition_time_color(total_time)
                        cell_label = get_cell_label(rule)
                    else:
                        color = (60, 60, 60, 200)
                        cell_label = ""
                        total_time = 0

                    btn_tag = dpg.generate_uuid()
                    theme_tag = make_cell_theme(color)

                    # TODO add right click action to add new rule
                    dpg.add_button(
                        label=cell_label,
                        tag=btn_tag,
                        width=cell_size - 4,
                        height=cell_size - 4,
                        callback=open_edit_transition_dialog,
                        user_data=rule,
                    )
                    dpg.bind_item_theme(btn_tag, theme_tag)

                    if rule:
                        trans_seg = rule["transition_object"]["segment_id"]
                        with dpg.tooltip(btn_tag):
                            dpg.add_text(f"Rule #{rule_idx}")
                            dpg.add_spacer(height=3)
                            dpg.add_text(f"Source: {id_label(src)}")
                            dpg.add_text(f"Destination: {id_label(dst)}")
                            dpg.add_text(f"Total transition time: {total_time}ms")
                            dpg.add_text(f"Transition segment: {trans_seg}")

        dpg.pop_container_stack()

    dpg.add_text("Transition rules")
    dpg.add_table(
        header_row=False,
        no_pad_innerX=True,
        scrollX=True,
        scrollY=True,
        height=table_h,
        policy=dpg.mvTable_SizingFixedFit,
        parent=parent,
        tag=tag,
    )

    regenerate()
    return tag
