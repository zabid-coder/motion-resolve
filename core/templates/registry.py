"""
Motion Resolve - Typography Template Engine: Template Registry
Discovers, loads, validates, and indexes template specifications from JSON files.
"""

import os
import json
from typing import Dict, List, Optional, Any
from core.templates.schema import TemplateSpec, TemplateParameter, LayerSpec, MotionTrackSpec, KeyframeSpec, ParameterType, LayerType, EasingToken


class TemplateRegistry:
    """Manages the catalog of declarative typography templates."""

    def __init__(self, templates_dir: Optional[str] = None):
        if not templates_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            templates_dir = os.path.join(base_dir, "data", "templates")
        self.templates_dir = templates_dir
        self._templates: Dict[str, TemplateSpec] = {}
        self._template_paths: Dict[str, str] = {}
        self.reload()

    def reload(self):
        """Scans templates directory and loads all valid JSON specs."""
        self._templates.clear()
        self._template_paths.clear()
        if not os.path.exists(self.templates_dir):
            return

        for root, _, files in os.walk(self.templates_dir):
            for file in files:
                if file.endswith(".json") and not file.startswith("."):
                    path = os.path.join(root, file)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            tpl = self._parse_template(data)
                            if tpl:
                                self._templates[tpl.id] = tpl
                                self._template_paths[tpl.id] = path
                    except Exception as e:
                        print(f"[TemplateRegistry] Error loading {path}: {e}")

    def get_template(self, template_id: str) -> Optional[TemplateSpec]:
        return self._templates.get(template_id)

    def get_by_id(self, template_id: str) -> Optional[TemplateSpec]:
        return self.get_template(template_id)

    def get_template_path(self, template_id: str) -> Optional[str]:
        """Returns the full filesystem path for the given template ID."""
        return self._template_paths.get(template_id)

    def get_all(self) -> List[TemplateSpec]:
        return list(self._templates.values())

    def get_by_category(self, category: str) -> List[TemplateSpec]:
        return [t for t in self._templates.values() if t.category.lower() == category.lower()]

    def get_categories(self) -> List[str]:
        cats = sorted(list({t.category for t in self._templates.values()}))
        return cats

    def _parse_template(self, d: Dict[str, Any]) -> Optional[TemplateSpec]:
        if "id" not in d or "name" not in d:
            return None

        params = []
        for p in d.get("parameters", []):
            ptype = ParameterType(p.get("type", "string"))
            params.append(TemplateParameter(
                id=p["id"],
                name=p.get("name", p["id"]),
                type=ptype,
                default=p.get("default"),
                category=p.get("category", "General"),
                min_val=p.get("min_val"),
                max_val=p.get("max_val"),
                step=p.get("step"),
                options=p.get("options"),
                description=p.get("description", "")
            ))

        layers = []
        for l in d.get("layers", []):
            ltype = LayerType(l.get("type", "text"))
            tracks = []
            for m in l.get("motion_tracks", []):
                kfs = []
                raw_keyframes = m.get("keyframes", [])
                if not raw_keyframes and ("from_val" in m or "to_val" in m):
                    start_time = float(m.get("start_time", 0.0))
                    duration = max(0.0, float(m.get("duration", 0.0)))
                    easing = m.get("easing", "expoOut")
                    raw_keyframes = [
                        {"time": start_time, "value": m.get("from_val", 0.0), "easing": easing},
                        {"time": start_time + duration, "value": m.get("to_val", 1.0), "easing": easing},
                    ]
                for k in raw_keyframes:
                    ease = EasingToken(k.get("easing", "expoOut"))
                    kfs.append(KeyframeSpec(
                        time=float(k.get("time", 0.0)),
                        value=k.get("value"),
                        easing=ease
                    ))
                tracks.append(MotionTrackSpec(
                    property=m.get("property", "opacity"),
                    phase=m.get("phase", "in"),
                    keyframes=kfs
                ))

            layers.append(LayerSpec(
                id=l["id"],
                type=ltype,
                name=l.get("name", l["id"]),
                parent_id=l.get("parent_id"),
                props=l.get("props", {}),
                motion_tracks=tracks
            ))

        return TemplateSpec(
            id=d["id"],
            name=d["name"],
            category=d.get("category", "General"),
            description=d.get("description", ""),
            tags=d.get("tags", []),
            aspect_ratios=d.get("aspect_ratios", ["16:9", "9:16", "1:1"]),
            duration_default=float(d.get("duration_default", 3.5)),
            min_hold=float(d.get("min_hold", 1.5)),
            in_duration=float(d.get("in_duration", 0.6)),
            out_duration=float(d.get("out_duration", 0.35)),
            parameters=params,
            layers=layers,
            theme_tokens=d.get("theme_tokens", {})
        )
