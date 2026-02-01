from enum import StrEnum


class SoundType(StrEnum):
    ENVIRONMENT = "a"
    CHARACTER = "c"
    MENU = "f"
    OBJECT = "o"
    CUTSCENE_SE = "p"
    SFX = "s"
    BGM = "m"
    VOICE = "v"
    FLOOR_MATERIAL_DETERMINED = "x"
    ARMOR_MATERIAL_DETERMINED = "b"
    PHANTOM = "i"
    MULTI_CHANNEL_STREAMING = "y"
    MATERIAL_RELATED = "z"
    FOOT_EFFECT = "e"
    GEOMETRY_ASSET = "g"
    DYNAMIC_DIALOG = "d"


# TODO incomplete, check cs_main and cs_smain
enums = {
    "Action": {
        "action_type": [
            "Play",
            "PlayEvent",
            "Stop_E_O",
        ],
    },
    "RandomSequenceContainer": {
        "initial_values/node_base_params": {
            "positioning_params": {
                "path_mode": [
                    "StepSequence"
                ],
                "speaker_panning_type": [
                    "DirectSpeakerAssignment",
                ],
                "three_dimensional_spatialization_mode": [
                    "None",
                    "PositionOnly",
                ],
                "three_dimensional_position_type": [
                    "Emitter",
                ],
            },
            "adv_settings_params": {
                "below_threshold_behavior": [
                    "ContinueToPlay",
                    "KillIfOneShotElseVirtual",
                    "KillVoice",
                ],
                "virtual_queue_behavior": [
                    "PlayFromBeginning",
                    "PlayFromElapsedTime",
                    "Resume",
                ],
            }
        },
        "mode": [
            "Random"
        ],
        "random_mode": [
            "Normal"
        ],
        "transition_mode": [
            "Disabled"
        ],
    },
    "Sound": {
        "bank_source_data": {
            "plugin": [
                "WwisseCodecVorbis",
            ],
            "source_type": [
                "BnkData",
            ],
        }
    },
    "property": {
        "prop_type": [
            "AttenuationID",
            "CenterPCT",
            "GameAuxSendVolume",
            "HPF",
            "Pitch",
            "PriorityDistanceOffset",
            "UserAuxSendVolume0",
            "Volume",
        ],
    }
}
