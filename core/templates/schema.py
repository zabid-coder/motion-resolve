"""
Motion Resolve - Typography Template Engine: Declarative Schema
Defines the schema for templates, layers, parameters, layout constraints, and motion tracks.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class LayerType(str, Enum):
    TEXT = "text"
    SHAPE_RECT = "shape_rect"
    SHAPE_LINE = "shape_line"
    SHAPE_PILL = "shape_pill"
    CONTAINER = "container"
    MASK = "mask"


class ParameterType(str, Enum):
    STRING = "string"
    NUMBER = "number"
    COLOR = "color"
    BOOLEAN = "boolean"
    SELECT = "select"
    FONT = "font"


class EasingToken(str, Enum):
    EXPO_OUT = "expoOut"
    QUART_IN_OUT = "quartInOut"
    CUBIC_IN = "cubicIn"
    SOFT_SPRING = "softSpring"
    LINEAR = "linear"


@dataclass
class TemplateParameter:
    id: str
    name: str
    type: ParameterType
    default: Any
    category: str = "General"  # Text, Style, Layout, Motion
    min_val: Optional[float] = None
    max_val: Optional[float] = None
    step: Optional[float] = None
    options: Optional[List[str]] = None
    description: str = ""


@dataclass
class KeyframeSpec:
    time: float            # Time in seconds relative to phase start (in/out)
    value: Any             # Numeric or coordinate value
    easing: EasingToken = EasingToken.EXPO_OUT


@dataclass
class MotionTrackSpec:
    property: str          # opacity, translate_x, translate_y, scale_x, scale_y, width, height, blur, write_on
    phase: str             # "in", "hold", "out"
    keyframes: List[KeyframeSpec] = field(default_factory=list)


@dataclass
class TypographySpec:
    font_family: str = ""
    font_style: str = "Regular"
    font_size: float = 0.05
    tracking: float = 1.0
    color: Any = None


@dataclass
class LayerSpec:
    id: str
    type: LayerType
    name: str
    parent_id: Optional[str] = None
    # Static properties
    props: Dict[str, Any] = field(default_factory=dict)
    # Motion tracks (in seconds)
    motion_tracks: List[MotionTrackSpec] = field(default_factory=list)

    @property
    def typography(self) -> Optional[TypographySpec]:
        if self.type != LayerType.TEXT:
            return None
        font = str(self.props.get("font") or "token:font_body")
        style = str(self.props.get("weight") or "Regular")
        try:
            size = float(self.props.get("size", 0.05))
        except (ValueError, TypeError):
            size = 0.05
        try:
            tracking = float(self.props.get("character_spacing", 1.0))
        except (ValueError, TypeError):
            tracking = 1.0
        color = self.props.get("color")
        return TypographySpec(font_family=font, font_style=style, font_size=size, tracking=tracking, color=color)


@dataclass
class TemplateSpec:
    id: str
    name: str
    category: str          # Podcast, SaaS, Minimal, Editorial, Social, Documentary, Cinematic, Kinetic
    description: str = ""
    tags: List[str] = field(default_factory=list)
    aspect_ratios: List[str] = field(default_factory=lambda: ["16:9", "9:16", "1:1"])
    duration_default: float = 3.5    # Total duration in seconds
    min_hold: float = 1.5           # Minimum reading hold time in seconds
    in_duration: float = 0.6        # In animation duration
    out_duration: float = 0.35      # Out animation duration
    parameters: List[TemplateParameter] = field(default_factory=list)
    layers: List[LayerSpec] = field(default_factory=list)
    theme_tokens: Dict[str, str] = field(default_factory=dict)  # token mapping

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "tags": self.tags,
            "aspect_ratios": self.aspect_ratios,
            "duration_default": self.duration_default,
            "min_hold": self.min_hold,
            "in_duration": self.in_duration,
            "out_duration": self.out_duration,
            "parameters": [
                {
                    "id": p.id,
                    "name": p.name,
                    "type": p.type.value if isinstance(p.type, ParameterType) else str(p.type),
                    "default": p.default,
                    "category": p.category,
                    "min_val": p.min_val,
                    "max_val": p.max_val,
                    "step": p.step,
                    "options": p.options,
                    "description": p.description,
                }
                for p in self.parameters
            ],
            "layers": [
                {
                    "id": l.id,
                    "type": l.type.value if isinstance(l.type, LayerType) else str(l.type),
                    "name": l.name,
                    "parent_id": l.parent_id,
                    "props": l.props,
                    "motion_tracks": [
                        {
                            "property": m.property,
                            "phase": m.phase,
                            "keyframes": [
                                {
                                    "time": k.time,
                                    "value": k.value,
                                    "easing": k.easing.value if isinstance(k.easing, EasingToken) else str(k.easing)
                                }
                                for k in m.keyframes
                            ]
                        }
                        for m in l.motion_tracks
                    ]
                }
                for l in self.layers
            ]
        }
