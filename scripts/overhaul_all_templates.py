import os
import sys
import json
import glob

repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

def build_motion_tracks_for_layer(layer, layer_idx, total_layers, category, is_lower_third=False):
    ltype = layer.get("type", "")
    lid = layer.get("id", "").lower()
    props = layer.get("props", {})
    role = props.get("role", "")

    tracks = []

    # -------------------------------------------------------------
    # 1. Background Plates & Cards
    # -------------------------------------------------------------
    if ltype in ("shape_rect", "shape_pill") or role == "plate" or "plate" in lid or "card" in lid or "bg" in lid:
        if is_lower_third:
            # Rise from bottom
            in_ty_start = 0.06
            out_ty_end = 0.05
        else:
            # Drop from top
            in_ty_start = -0.06
            out_ty_end = -0.05

        tracks.append({
            "property": "opacity",
            "phase": "in",
            "keyframes": [
                {"time": 0.0, "value": 0.0, "easing": "quartInOut"},
                {"time": 0.30, "value": 1.0, "easing": "quartInOut"}
            ]
        })
        tracks.append({
            "property": "translate_y",
            "phase": "in",
            "keyframes": [
                {"time": 0.0, "value": in_ty_start, "easing": "expoOut"},
                {"time": 0.48, "value": 0.0, "easing": "expoOut"}
            ]
        })
        tracks.append({
            "property": "translate_y",
            "phase": "out",
            "keyframes": [
                {"time": 0.0, "value": 0.0, "easing": "cubicIn"},
                {"time": 0.32, "value": out_ty_end, "easing": "cubicIn"}
            ]
        })
        tracks.append({
            "property": "opacity",
            "phase": "out",
            "keyframes": [
                {"time": 0.0, "value": 1.0, "easing": "cubicIn"},
                {"time": 0.32, "value": 0.0, "easing": "cubicIn"}
            ]
        })

    # -------------------------------------------------------------
    # 2. Accent Lines & Dividers
    # -------------------------------------------------------------
    elif ltype == "shape_line" or "line" in lid or "strike" in lid or "divider" in lid:
        tracks.append({
            "property": "scale_x",
            "phase": "in",
            "keyframes": [
                {"time": 0.10, "value": 0.0, "easing": "expoOut"},
                {"time": 0.38, "value": 1.0, "easing": "expoOut"}
            ]
        })
        tracks.append({
            "property": "opacity",
            "phase": "in",
            "keyframes": [
                {"time": 0.10, "value": 0.0, "easing": "quartInOut"},
                {"time": 0.28, "value": 1.0, "easing": "quartInOut"}
            ]
        })
        tracks.append({
            "property": "scale_x",
            "phase": "out",
            "keyframes": [
                {"time": 0.0, "value": 1.0, "easing": "cubicIn"},
                {"time": 0.28, "value": 0.0, "easing": "cubicIn"}
            ]
        })
        tracks.append({
            "property": "opacity",
            "phase": "out",
            "keyframes": [
                {"time": 0.0, "value": 1.0, "easing": "cubicIn"},
                {"time": 0.28, "value": 0.0, "easing": "cubicIn"}
            ]
        })

    # -------------------------------------------------------------
    # 3. Pills, Badges, CTAs, Hero Amount / Numbers
    # -------------------------------------------------------------
    elif any(kw in lid for kw in ("pill", "badge", "amount", "price", "cta", "stat", "num", "counter", "chip")):
        t_start = 0.16 + layer_idx * 0.04
        tracks.append({
            "property": "opacity",
            "phase": "in",
            "keyframes": [
                {"time": t_start, "value": 0.0, "easing": "quartInOut"},
                {"time": t_start + 0.16, "value": 1.0, "easing": "quartInOut"}
            ]
        })
        tracks.append({
            "property": "scale",
            "phase": "in",
            "keyframes": [
                {"time": t_start, "value": 0.65, "easing": "softSpring"},
                {"time": t_start + 0.26, "value": 1.08, "easing": "softSpring"},
                {"time": t_start + 0.34, "value": 1.0, "easing": "expoOut"}
            ]
        })
        tracks.append({
            "property": "scale",
            "phase": "out",
            "keyframes": [
                {"time": 0.0, "value": 1.0, "easing": "cubicIn"},
                {"time": 0.30, "value": 0.82, "easing": "cubicIn"}
            ]
        })
        tracks.append({
            "property": "opacity",
            "phase": "out",
            "keyframes": [
                {"time": 0.0, "value": 1.0, "easing": "cubicIn"},
                {"time": 0.30, "value": 0.0, "easing": "cubicIn"}
            ]
        })

    # -------------------------------------------------------------
    # 4. Standard Text Layers (Staggered Entrance & Exit)
    # -------------------------------------------------------------
    else:
        stagger_time = 0.06 + layer_idx * 0.04
        in_ty = -0.035 if not is_lower_third else 0.035
        out_ty = -0.04 if not is_lower_third else 0.04

        tracks.append({
            "property": "opacity",
            "phase": "in",
            "keyframes": [
                {"time": stagger_time, "value": 0.0, "easing": "quartInOut"},
                {"time": stagger_time + 0.24, "value": 1.0, "easing": "quartInOut"}
            ]
        })
        tracks.append({
            "property": "translate_y",
            "phase": "in",
            "keyframes": [
                {"time": stagger_time, "value": in_ty, "easing": "expoOut"},
                {"time": stagger_time + 0.38, "value": 0.0, "easing": "expoOut"}
            ]
        })
        tracks.append({
            "property": "translate_y",
            "phase": "out",
            "keyframes": [
                {"time": 0.0, "value": 0.0, "easing": "cubicIn"},
                {"time": 0.30, "value": out_ty, "easing": "cubicIn"}
            ]
        })
        tracks.append({
            "property": "opacity",
            "phase": "out",
            "keyframes": [
                {"time": 0.0, "value": 1.0, "easing": "cubicIn"},
                {"time": 0.30, "value": 0.0, "easing": "cubicIn"}
            ]
        })

    return tracks


def overhaul_all_templates():
    template_paths = glob.glob(os.path.join(repo_root, "data", "templates", "*", "*.json"))
    print(f"Starting broadcast overhaul on {len(template_paths)} templates...")

    upgraded_count = 0

    for path in sorted(template_paths):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        tid = data.get("id", "")
        # Skip benchmark templates already manually customized
        if tid in ("agency_stripe_notification", "kin_split_reveal", "kin_word_explosion"):
            continue

        cat = data.get("category", "")
        layers = data.get("layers", [])
        if not layers:
            continue

        # Detect position (lower third if pos_y <= 0.35 or lower in name)
        pos_y = 0.5
        for p in data.get("parameters", []):
            if p.get("id") == "pos_y":
                pos_y = float(p.get("default", 0.5))
                break
        is_lower = (pos_y <= 0.35) or ("lower" in tid) or ("sub" in tid)

        # Ensure in_duration and out_duration are snappier
        data["in_duration"] = min(0.65, max(0.45, data.get("in_duration", 0.55)))
        data["out_duration"] = min(0.40, max(0.28, data.get("out_duration", 0.33)))

        # Update layers
        for idx, layer in enumerate(layers):
            # Only update if tracks are empty or incomplete
            existing_tracks = layer.get("motion_tracks", [])
            in_tracks = [t for t in existing_tracks if t.get("phase") == "in"]
            out_tracks = [t for t in existing_tracks if t.get("phase") == "out"]

            if not in_tracks or not out_tracks or len(existing_tracks) < 2:
                new_tracks = build_motion_tracks_for_layer(layer, idx, len(layers), cat, is_lower_third=is_lower)
                layer["motion_tracks"] = new_tracks

            # Upgrade Plate styling if applicable
            props = layer.get("props", {})
            if layer.get("type") in ("shape_rect", "shape_pill") or props.get("role") == "plate":
                # Ensure 16-18px corner radius and modern border
                if props.get("corner_radius", 0) < 12:
                    props["corner_radius"] = 16
                if "border_color" not in props:
                    props["border_color"] = [0.26, 0.25, 0.34, 0.65]
                if "border_width" not in props:
                    props["border_width"] = 1.2

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        upgraded_count += 1

    print(f"\nSuccessfully overhauled {upgraded_count} templates with professional staggered motion tracks and tokens!")

if __name__ == "__main__":
    overhaul_all_templates()
