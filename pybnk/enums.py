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
VirtualQueueBehavior: TypeAlias = Literal["Resume", "PlayFromElapsedTime", "PlayFromBeginning"]


property_defaults = {
    "Volume": -3.0,
    "PriorityDistanceOffset": -49.0,
    "UserAuxSendVolume0": -96.0,
    "UserAuxSendVolume1": -96.0,
    "UserAuxSendVolume2": -96.0,
    "UserAuxSendVolume3": -96.0,
    "GameAuxSendVolume": -6.0,
    "CenterPCT": 50.0,
    "AttenuationID": 0,
    "Priority": 20.0,
    "LPF": 20.0,
    "HPF": 35.0,
    "Pitch": -500.0,
}


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
