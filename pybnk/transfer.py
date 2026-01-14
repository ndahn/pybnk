from pprint import pprint

from pybnk import Soundbank, Node, calc_hash
from pybnk.modify import add_children
from pybnk.wem import import_wems
from pybnk.util import print_hierarchy


def copy_structure(
    src_bnk: Soundbank,
    dst_bnk: Soundbank,
    wwise_map: dict[str, str],
    quiet: bool = False,
) -> None:
    wems = []

    def fix_soundbank_references(actions: list[Node]) -> None:
        # Some actions make references to other soundbanks or even their own
        for a in actions:
            bank_id = a.get("params/bank_id", None)
            if bank_id == src_bnk.id:
                a["params/bank_id"] = dst_bnk.id

    for wwise_src, wwise_dst in wwise_map.items():
        # Play event
        play_evt_name = f"Play_{wwise_src}"
        play_evt = src_bnk[play_evt_name].copy()
        play_evt.id = calc_hash(f"Play_{wwise_dst}")
        play_actions = [src_bnk[a].copy() for a in play_evt["actions"]]
        fix_soundbank_references(play_actions)
        dst_bnk.add_event(play_evt, play_actions)

        # Stop event
        stop_evt_name = f"Stop_{wwise_src}"
        stop_evt = src_bnk[stop_evt_name].copy()
        stop_evt.id = calc_hash(f"Stop_{wwise_dst}")
        stop_actions = [src_bnk[a].copy() for a in stop_evt["actions"]]
        fix_soundbank_references(stop_actions)
        dst_bnk.add_event(stop_evt, stop_actions)

        # Collect the structures attached to each action
        for action_id in play_evt["actions"]:
            action = src_bnk[action_id]
            entrypoint = src_bnk[action["external_id"]]

            # Collect the hierarchy responsible for playing the sound(s)
            action_tree = src_bnk.get_hierarchy(entrypoint)

            if not quiet:
                print_hierarchy(src_bnk, action_tree)

            wems.extend([d for d in action_tree.nodes.data("wem").values() if d])
            dst_bnk.add_nodes(src_bnk[n].copy() for n in action_tree.nodes)

            # Go upwards through the parents chain and see what needs to be transferred
            upchain = src_bnk.get_parent_chain(entrypoint)

            if not quiet:
                print("\nThe parent chain consists of the following nodes:")
                for up_id in reversed(upchain):
                    print(f" ⤷ {up_id} ({src_bnk[up_id].type})")

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
                print("\nThe following extra items were collected:")
                for nid in extras:
                    print(f" - {nid} ({src_bnk[nid].type})")
                print()

            for oid in extras:
                if oid not in src_bnk:
                    continue

                if oid in dst_bnk:
                    continue

                dst_bnk.add_nodes(src_bnk[oid].copy())

    if not quiet:
        print("All hierarchies transferred")
        print("\nFound the following WEMs:")
        pprint(wems)

    print("\nVerifying soundbank...")
    issues = dst_bnk.verify()
    if issues:
        for issue in issues:
            print(f" - {issue}")
    else:
        print(" - seems surprisingly fine :o")

    wem_paths = []
    for wem in wems:
        wp = src_bnk.bnk_dir / f"{wem}.wem"
        if wp.is_file():
            wem_paths.append(wp)
        else:
            print(f"WEM {wem} not found in source soundbank, probably streamed?")

    import_wems(dst_bnk, wem_paths)
