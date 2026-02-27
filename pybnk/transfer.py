from pybnk import Soundbank, Node, calc_hash
from pybnk.convenience import new_event
from pybnk.wem import import_wems
from pybnk.util import format_hierarchy, logger


def extract_structure(bnk: Soundbank, entrypoint) -> list[Node]:
    nodes = []

    # Collect the hierarchy responsible for playing the sound(s)
    action_tree = bnk.get_subtree(entrypoint)
    nodes.extend(bnk[n] for n in action_tree.nodes)

    # Go upwards through the parents chain and see what needs to be transferred
    upchain = bnk.get_parent_chain(entrypoint)
    nodes.extend((bnk[uid] for uid in upchain))

    # Collect additional referenced items
    extras = bnk.find_related_objects(action_tree.nodes)
    nodes.extend(bnk[eid] for eid in extras if eid in bnk)

    return nodes


def copy_event(
    src_bnk: Soundbank,
    dst_bnk: Soundbank,
    event: Node,
) -> Node:
    event = event.copy()
    actions = [src_bnk[aid].copy() for aid in event["actions"]]

    # Some actions make references to other soundbanks
    for a in actions:
        # Look for e.g. params/Play/bank_id
        for params in a.get("params", {}).values():
            action_bank_id = params.get("bank_id", None)
            if action_bank_id == src_bnk.id:
                params["bank_id"] = dst_bnk.id

    dst_bnk.add_nodes(event, *actions)
    return event


def copy_node_structure(
    src_bnk: Soundbank,
    dst_bnk: Soundbank,
    entrypoint: Node,
) -> list[tuple[int, str]]:
    # Collect the hierarchy responsible for playing the sound(s)
    action_tree = src_bnk.get_subtree(entrypoint)
    tree_str = format_hierarchy(src_bnk, action_tree)
    logger.info(f"Hierarchy for node {entrypoint}:\n{tree_str}\n")

    wems = []
    # MusicTrack nodes can have multiple sources
    for nid, n_wems in action_tree.nodes.data("wems"):
        if n_wems:
            wems.extend((nid, w) for w in n_wems)
    
    dst_bnk.add_nodes(*[src_bnk[n].copy() for n in action_tree.nodes])

    # Go upwards through the parents chain and see what needs to be transferred
    upchain = src_bnk.get_parent_chain(entrypoint)
    upchain_str = "\n".join([
        f" ⤷ {up_id} ({src_bnk[up_id].type})"
        for up_id in reversed(upchain)
    ])
    logger.info(f"\nThe parent chain consists of the following nodes:\n{upchain_str}\n")

    up_child = entrypoint
    for up_id in upchain:
        # Once we encounter an existing node we can assume the rest of the chain is
        # intact. Child nodes must be inserted *before* the first existing parent.
        if up_id in dst_bnk:
            up_node = dst_bnk[up_id]
            items = up_node["children/items"]

            if up_child.id not in items:
                items.append(up_child.id)
                up_child.parent = up_node.id
                items.sort()

            break

        # First time we encounter upchain node, clear the children, as non-existing items
        # will make the soundbank invalid
        up = src_bnk[up_id].copy()
        up["children/items"] = []
        dst_bnk.add_nodes(up)

        up_child = up

    # Collect additional referenced items
    extras = src_bnk.find_related_objects(action_tree.nodes)
    extras_str = "\n".join([
        f" - {nid} ({src_bnk[nid].type})"
        for nid in extras
    ])
    logger.info(f"\nThe following extra items were collected:\n{extras_str}\n")

    for oid in extras:
        if oid not in src_bnk:
            continue

        if oid in dst_bnk:
            continue

        dst_bnk.add_nodes(src_bnk[oid].copy())

    return wems


def copy_wems(
    src_bnk: Soundbank,
    dst_bnk: Soundbank,
    wems: list[str],
) -> None:
    wems_str = "\n".join(f"- {w}" for w in wems)
    logger.info(f"Discovered the following WEMs:\n{wems_str}\n")

    logger.info("Copying wems...")
    wem_paths = []
    for nid, wem in wems:
        wp = src_bnk.bnk_dir / f"{wem}.wem"
        if wp.is_file():
            wem_paths.append(wp)
        else:
            sound = src_bnk[nid]
            plugin = sound["bank_source_data/plugin"]
            stype = sound["bank_source_data/source_type"]
            logger.warning(
                f"WEM {wem} ({plugin}, {stype}) not found in source soundbank, skipped"
            )

    import_wems(dst_bnk, wem_paths)


def copy_wwise_events(
    src_bnk: Soundbank,
    dst_bnk: Soundbank,
    wwise_map: dict[str, str],
) -> None:
    wems = []

    for wwise_src, wwise_dst in wwise_map.items():
        # Play event
        play_evt_name = f"Play_{wwise_src}"
        play_evt = src_bnk[play_evt_name].copy()
        play_evt.id = calc_hash(f"Play_{wwise_dst}")
        play_evt = copy_event(src_bnk, dst_bnk, play_evt)

        # Stop event
        stop_evt_name = f"Stop_{wwise_src}"
        stop_evt = src_bnk[stop_evt_name].copy()
        stop_evt.id = calc_hash(f"Stop_{wwise_dst}")
        stop_evt = copy_event(src_bnk, dst_bnk, stop_evt)

        # Collect the structures attached to each action
        for action_id in play_evt["actions"]:
            action = dst_bnk[action_id]  # already copied to dst
            action_bnk_id = action["params/Play/bank_id"]

            # NOTE action_bnk_id will already be translated from src_bnk to dst_bnk
            if action_bnk_id != dst_bnk.id:
                logger.warning(
                    f"Action {action.id} references node in external soundbank {action_bnk_id}"
                )
                return

            entrypoint = src_bnk[action["external_id"]]
            new_wems = copy_node_structure(src_bnk, dst_bnk, entrypoint)
            wems.extend(w for _, w in new_wems)

    # Verify
    logger.info("\nVerifying soundbank...")
    issues = dst_bnk.verify()
    if issues:
        for issue in issues:
            logger.warning(f" - {issue}")
    else:
        logger.info(" - seems surprisingly fine :o\n")

    # Copy WEMs
    copy_wems(src_bnk, dst_bnk, wems)
    
    # Yay!
    logger.info("Done. Yay!")


def copy_structures_with_new_events(
    src_bnk: Soundbank,
    dst_bnk: Soundbank,
    nodes: dict[Node, str],
) -> None:
    wems = []

    for entrypoint, wwise_dst in nodes.items():
        play_event, play_action = new_event(dst_bnk, f"Play_{wwise_dst}", entrypoint, "Play")
        dst_bnk.add_nodes(play_event, play_action)

        stop_event, stop_action = new_event(dst_bnk, f"Stop_{wwise_dst}", entrypoint, "Stop")
        dst_bnk.add_nodes(stop_event, stop_action)

        new_wems = copy_node_structure(src_bnk, dst_bnk, entrypoint)
        wems.extend(w for _, w in new_wems)

    # Verify
    logger.info("\nVerifying soundbank...")
    issues = dst_bnk.verify()
    if issues:
        for issue in issues:
            logger.warning(f" - {issue}")
    else:
        logger.info(" - seems surprisingly fine :o\n")

    # Copy WEMs
    copy_wems(src_bnk, dst_bnk, wems)
    
    # Yay!
    logger.info("Done. Yay!")
