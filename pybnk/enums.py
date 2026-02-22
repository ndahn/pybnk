from typing import Literal, TypeAlias
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


RtcpType: TypeAlias = Literal["GameParameter"]
AccumulationType: TypeAlias = Literal["Additive"]
ScalingType: TypeAlias = Literal["DB", "Linear", "None"]
CurveType: TypeAlias = Literal["Linear", "SCurve", "Log1", "Log3", "Sine", "Constant"]
SourceType: TypeAlias = Literal["Embedded", "Streaming", "PrefetchStreaming"]
