#!/usr/bin/env python3
import sys
import traceback
import re

from pybnk import Soundbank
from pybnk.transfer import copy_structure


# ------------------------------------------------------------------------------------------
# Set these paths so they point to your extracted source and destination soundbanks.
SRC_BNK_DIR = "soundbanks/nr_cs_main"
DST_BNK_DIR = "soundbanks/cs_main"

# NPC sounds are usually named "c<npc-id>0<sound-id>". When moving npc sounds to the player, I
# recommend renaming them as follows.
#
#     <soundtype>4<npc-id><sound-id>
#
# This should make it easy to avoid collisions and allows you to keep track of which IDs you've
# ported so far and from where.
#
# The soundtype has (afaik) no meaning other than being used for calculating the event hashes, so
# you should be able to use whatever you like from this list:
#
WWISE_IDS = {
    "c512006630": "s451206630",
    "c512006635": "s451206635",
}

# Enables writing to the destination.
ENABLE_WRITE = True

# If True, don't ask for confirmation: make reasonable assumptions and write once ready
NO_QUESTIONS = False
# ------------------------------------------------------------------------------------------


if __name__ == "__main__":
    if len(sys.argv) == 1:
        src_bnk_dir = SRC_BNK_DIR
        dst_bnk_dir = DST_BNK_DIR
        wwise_ids = WWISE_IDS
        enable_write = ENABLE_WRITE
        no_questions = NO_QUESTIONS
    else:
        import argparse

        parser = argparse.ArgumentParser(
            description="A nifty tool for transfering wwise sounds between From software soundbanks."
        )

        parser.add_argument("src_bnk", type=str, help="The source soundbank folder")
        parser.add_argument(
            "dst_bnk", type=str, help="The destination soundbank folder"
        )
        parser.add_argument(
            "sound_ids",
            type=str,
            nargs="+",
            help="Specify as '<type><source-id>:=<type><destination-id>', e.g. 'c123456789:=s0987654321' (or just <type><id> if you want to copy as is)",
        )
        parser.add_argument(
            "--disable_write",
            action="store_true",
            help="If True, no changes to the destination soundbank will be made",
        )
        parser.add_argument(
            "--no_questions",
            action="store_true",
            help="Assume sensible defaults instead of asking for confirmations",
        )

        args = parser.parse_args()

        if args.help:
            parser.print_help()
            sys.exit(1)

        src_bnk_dir = args.src_bnk
        dst_bnk_dir = args.dst_bnk
        enable_write = not args.disable_write
        no_questions = args.no_questions

        wwise_ids = {}
        wwise_id_check = re.compile(r"[a-z][0-9]+")

        for s in args.sound_ids:
            if ":=" in s:
                src_id, dst_id = s.split(":=")
            else:
                src_id = dst_id = s

            if not (
                re.fullmatch(wwise_id_check, src_id)
                and re.fullmatch(wwise_id_check, dst_id)
            ):
                raise ValueError(f"Invalid sound ID specification {s}")

            wwise_ids[src_id] = dst_id

    try:
        src_bnk = Soundbank.load(src_bnk_dir)
        dst_bnk = Soundbank.load(dst_bnk_dir)
        copy_structure(src_bnk, dst_bnk, wwise_ids)
    except Exception:
        if hasattr(sys, "gettrace") and sys.gettrace() is not None:
            # Debugger is active, let the debugger handle it
            raise

        # In case we are run from a temporary terminal, otherwise we won't see what's wrong
        print(traceback.format_exc())

    input("Press enter to exit...")
