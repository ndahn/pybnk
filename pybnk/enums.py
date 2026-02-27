from typing import Literal, TypeAlias
from enum import StrEnum, IntFlag


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


# Not a flag, just a convenient way to map the known types
class ActionType(IntFlag):
    PLAY = 1027
    STOP = 259
    MUTE_BUS = 1538
    RESET_BUS_VOLUME = 2818
    RESET_BUS_LPFM = 3842


RtcpType: TypeAlias = Literal["GameParameter"]
AccumulationType: TypeAlias = Literal["Additive"]
ScalingType: TypeAlias = Literal["DB", "Linear", "None"]
CurveType: TypeAlias = Literal["Linear", "SCurve", "Log1", "Log3", "Sine", "Constant"]
SourceType: TypeAlias = Literal["Embedded", "Streaming", "PrefetchStreaming"]
PluginType: TypeAlias = Literal["VORBIS", "PCM"]


reference_fields = {
    "*": [
        "**/node_base_params/override_bus_id",
        "**/node_base_params/aux_params/aux1",
        "**/node_base_params/aux_params/aux2",
        "**/node_base_params/aux_params/aux3",
        "**/node_base_params/aux_params/aux4",
        "**/node_base_params/aux_params/reflections_aux_bus",
        "**/initial_rtcp/rtpcs:*/curve_id",
        "**/children/items:*",
    ],
    "Action": [
        "external_id",
    ],
    "Bus": [
        "initial_values/ducks:*/bus_id",
    ],
    "Event": [
        "actions:*",
    ],
    "MusicRandomSequenceContainer": [
        "playlist_items/segment_id",
        
    ],
}
