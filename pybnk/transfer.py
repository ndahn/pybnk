from pprint import pprint

from pybnk import Soundbank, Node, calc_hash
from pybnk.modify import add_children
from pybnk.wem import import_wems
from pybnk.util import print_hierarchy, logger


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

    dst_bnk.add_event(event, actions)
    return event


def copy_structure(
    src_bnk: Soundbank,
    dst_bnk: Soundbank,
    wwise_map: dict[str, str],
    quiet: bool = False,
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
                print(
                    f"Action {action_id} of event {play_evt} references node in external soundbank {action_bnk_id}"
                )
                continue

            entrypoint = src_bnk[action["external_id"]]

            # Collect the hierarchy responsible for playing the sound(s)
            action_tree = src_bnk.get_hierarchy(entrypoint)

            if not quiet:
                print_hierarchy(src_bnk, action_tree)

            wems.extend(((nid, wem) for nid, wem in action_tree.nodes.data("wem") if wem))
            dst_bnk.add_nodes(src_bnk[n].copy() for n in action_tree.nodes)

            # Go upwards through the parents chain and see what needs to be transferred
            upchain = src_bnk.get_parent_chain(entrypoint)

            if not quiet:
                logger.info("\nThe parent chain consists of the following nodes:")
                for up_id in reversed(upchain):
                    print(f" ⤷ {up_id} ({src_bnk[up_id].type})")
                print()

            up_child = entrypoint
            for up_id in upchain:
                # Once we encounter an existing node we can assume the rest of the chain is
                # intact. Child nodes must be inserted *before* the first existing parent.
                if up_id in dst_bnk:
                    add_children(dst_bnk[up_id], up_child)
                    break

                # First time we encounter upchain node, clear the children, as non-existing items
                # will make the soundbank invalid
                up = src_bnk[up_id].copy()
                up["children/items"] = []
                dst_bnk.add_nodes([up])

                up_child = up

            # Collect additional referenced items
            extras = src_bnk.find_related_objects(action_tree.nodes)

            if extras and not quiet:
                logger.info("\nThe following extra items were collected:")
                for nid in extras:
                    print(f" - {nid} ({src_bnk[nid].type})")
                print()

            for oid in extras:
                if oid not in src_bnk:
                    continue

                if oid in dst_bnk:
                    continue

                dst_bnk.add_nodes(src_bnk[oid].copy())

    # Verify
    logger.info("\nVerifying soundbank...")
    issues = dst_bnk.verify()
    if issues:
        for issue in issues:
            logger.warning(f" - {issue}")
    else:
        logger.info(" - seems surprisingly fine :o\n")

    # Copy WEMs
    if not quiet:
        logger.info("Discovered the following WEMs:")
        pprint(wems)

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
    
    # Yay!
    print()
    logger.info("Done. Yay!")
