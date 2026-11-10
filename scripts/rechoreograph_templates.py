"""
Give every non-Signature template a motion language that fits its category.

Before this, 20 templates shared one identical choreography (a bulk script
stamped the same tracks everywhere). Layouts are left untouched; only
motion_tracks and the motion props (clip / stagger / origin) are rewritten.

Run:  python3 scripts/rechoreograph_templates.py
"""

import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def k(t, v, e="expoOut"):
    return {"time": round(t, 3), "value": v, "easing": e}


def tr(prop, phase, *keys):
    return {"property": prop, "phase": phase, "keyframes": list(keys)}


def fade(phase, t0, t1, e=None):
    if phase == "in":
        return tr("opacity", "in", k(t0, 0, e or "quartInOut"), k(t1, 1, e or "quartInOut"))
    return tr("opacity", "out", k(t0, 1, e or "cubicIn"), k(t1, 0, e or "cubicIn"))


def lh(layer):
    try:
        return float(layer["props"].get("size", 0.05)) * 1920.0 / 1080.0
    except (TypeError, ValueError):
        return 0.09


# ---------------------------------------------------------------- recipes
# Each recipe: f(layer, kind, ti, si) -> (tracks, props_to_set)
#   kind: "text" | "line" | "plate" | "shape";  ti: text index;  si: shape index

def r_mask_rise(l, kind, ti, si):
    if kind == "text" and ti == 0:
        d = lh(l) * 0.95
        return [fade("in", 0.1, 0.22, "linear"), tr("translate_y", "in", k(0.1, -d, "quintOut"), k(0.8, 0)),
                tr("translate_y", "out", k(0.0, 0, "expoIn"), k(0.4, -d)), fade("out", 0.34, 0.4, "linear")], {"clip": True}
    if kind == "text":
        t0 = 0.3 + 0.12 * ti
        return [fade("in", t0, t0 + 0.45), tr("blur", "in", k(t0, 6.0), k(t0 + 0.55, 0)),
                tr("translate_y", "in", k(t0, -0.01), k(t0 + 0.6, 0)), fade("out", 0.0, 0.28)], {}
    if kind == "line":
        return [fade("in", 0.0, 0.06, "linear"), tr("scale_x", "in", k(0.0, 0, "expoInOut"), k(0.6, 1)),
                tr("scale_x", "out", k(0.1, 1, "expoIn"), k(0.42, 0)), fade("out", 0.38, 0.42, "linear")], {"origin": "left"}
    return [fade("in", 0.0, 0.08, "linear"), tr("scale_x", "in", k(0.0, 0, "expoInOut"), k(0.55, 1)),
            tr("scale_x", "out", k(0.12, 1, "expoIn"), k(0.45, 0)), fade("out", 0.4, 0.45, "linear")], {"origin": "left"}


def r_blur_breathe(l, kind, ti, si):
    if kind == "text" and ti == 0:
        base = float(l["props"].get("character_spacing", 1.0) or 1.0)
        return [fade("in", 0.0, 0.9), tr("blur", "in", k(0.0, 12.0), k(1.2, 0)),
                tr("tracking", "in", k(0.0, base + 0.35), k(1.6, base)),
                fade("out", 0.0, 0.7, "quartInOut"), tr("blur", "out", k(0.0, 0, "expoIn"), k(0.7, 8.0))], {}
    if kind == "text":
        t0 = 0.7 + 0.15 * ti
        return [fade("in", t0, t0 + 0.6), tr("translate_y", "in", k(t0, -0.01), k(t0 + 0.8, 0)),
                fade("out", 0.0, 0.5)], {}
    return [fade("in", 0.5, 0.6, "linear"), tr("scale_x", "in", k(0.5, 0, "expoInOut"), k(1.4, 1)),
            fade("out", 0.0, 0.5)], {"origin": "center"}


def r_char_cascade(l, kind, ti, si):
    if kind == "text" and ti == 0:
        return [fade("in", 0.0, 0.35), tr("translate_y", "in", k(0.0, -0.02), k(0.5, 0)),
                tr("blur", "in", k(0.0, 6.0), k(0.45, 0)), fade("out", 0.0, 0.3)], {"stagger": {"delay": 1.3}}
    return r_mask_rise(l, kind, ti, si) if kind != "text" else (
        [fade("in", 0.45 + 0.12 * ti, 0.9 + 0.12 * ti), fade("out", 0.0, 0.25)], {})


def r_spring_pop(l, kind, ti, si):
    if kind == "text" and ti == 0:
        return [fade("in", 0.0, 0.08, "linear"), tr("scale", "in", k(0.0, 0.3, "spring"), k(0.5, 1.0)),
                fade("out", 0.05, 0.25), tr("scale", "out", k(0.0, 1, "expoIn"), k(0.25, 0.8))], {"stagger": {"delay": 1.0}}
    if kind == "text":
        t0 = 0.25 + 0.1 * ti
        d = lh(l) * 0.95
        return [fade("in", t0, t0 + 0.06, "linear"), tr("translate_y", "in", k(t0, -d, "quintOut"), k(t0 + 0.45, 0)),
                fade("out", 0.05, 0.25), tr("scale", "out", k(0.0, 1, "expoIn"), k(0.25, 0.85))], {"clip": True}
    return [fade("in", 0.12, 0.18, "linear"), tr("scale", "in", k(0.12, 0.6, "softSpring"), k(0.6, 1)),
            tr("scale", "out", k(0.0, 1, "expoIn"), k(0.25, 0.85)), fade("out", 0.08, 0.25)], {}


def r_slide_stack(l, kind, ti, si):
    if kind == "text":
        t0 = 0.18 + 0.1 * ti
        return [fade("in", t0, t0 + 0.4), tr("translate_x", "in", k(t0, -0.022, "quintOut"), k(t0 + 0.6, 0)),
                fade("out", 0.0, 0.22), tr("translate_x", "out", k(0.0, 0, "expoIn"), k(0.25, -0.015))], {}
    if kind == "line":
        return [fade("in", 0.05, 0.1, "linear"), tr("scale_y", "in", k(0.05, 0, "expoInOut"), k(0.5, 1)),
                tr("scale_y", "out", k(0.1, 1, "expoIn"), k(0.4, 0)), fade("out", 0.36, 0.4, "linear")], {"origin": "bottom"}
    return [fade("in", 0.0, 0.08, "linear"), tr("scale_x", "in", k(0.0, 0, "expoInOut"), k(0.55, 1)),
            tr("scale_x", "out", k(0.15, 1, "expoIn"), k(0.45, 0)), fade("out", 0.42, 0.45, "linear")], {"origin": "left"}


def r_soft_card(l, kind, ti, si):
    if kind in ("plate", "shape"):
        return [fade("in", 0.0, 0.3), tr("scale", "in", k(0.0, 0.92, "softSpring"), k(0.6, 1)),
                tr("translate_y", "in", k(0.0, -0.02), k(0.6, 0)),
                tr("scale", "out", k(0.1, 1, "expoIn"), k(0.45, 0.96)), fade("out", 0.15, 0.45)], {}
    if kind == "text" and ti == 0:
        return [fade("in", 0.15, 0.45), tr("translate_y", "in", k(0.15, -0.015), k(0.6, 0)),
                tr("blur", "in", k(0.15, 5.0), k(0.55, 0)), fade("out", 0.0, 0.25)], {"stagger": {"delay": 0.9}}
    if kind == "text":
        t0 = 0.4 + 0.12 * ti
        return [fade("in", t0, t0 + 0.4), tr("translate_y", "in", k(t0, -0.01), k(t0 + 0.55, 0)),
                fade("out", 0.0, 0.25)], {}
    return [fade("in", 0.35, 0.4, "linear"), tr("scale_x", "in", k(0.35, 0, "expoInOut"), k(0.9, 1)),
            fade("out", 0.0, 0.3)], {"origin": "left"}


def r_kinetic_slam(l, kind, ti, si):
    if kind == "text" and ti == 0:
        return [fade("in", 0.0, 0.06, "linear"), tr("scale", "in", k(0.0, 1.55, "expoOut"), k(0.4, 1.0)),
                tr("rotation", "in", k(0.0, -5.0), k(0.4, 0.0)), tr("blur", "in", k(0.0, 8.0), k(0.25, 0)),
                tr("scale", "out", k(0.0, 1, "expoIn"), k(0.22, 1.12)), fade("out", 0.06, 0.22)], {}
    if kind == "text":
        t0 = 0.22 + 0.1 * ti
        return [fade("in", t0, t0 + 0.06, "linear"), tr("scale", "in", k(t0, 0.4, "spring"), k(t0 + 0.45, 1)),
                fade("out", 0.0, 0.2)], {"stagger": {"delay": 0.8}}
    return r_spring_pop(l, kind, ti, si)


RECIPES = {
    "A": r_mask_rise, "B": r_blur_breathe, "C": r_char_cascade, "D": r_spring_pop,
    "E": r_slide_stack, "F": r_soft_card, "G": r_kinetic_slam,
}

ASSIGN = {
    "agency_diagonal_stat_split": "F", "agency_one_object_focus": "G", "agency_price_strikethrough": "F",
    "agency_side_by_side_thirds": "E", "agency_testimonial_proof": "B",
    "cine_chapter_card": "B", "cine_intertitle_card": "C", "cine_main_title": "B",
    "doc_archive_caption": "A", "doc_interviewee_rule": "E", "doc_timestamp_hud": "C",
    "edit_drop_cap": "A", "edit_issue_tag": "C", "edit_pull_quote": "B", "edit_section_opener": "A",
    "edit_serif_headline": "C", "edit_split_weight": "A",
    "kin_dynamic_stack": "G", "kin_masked_line": "A", "kin_split_reveal": "A", "kin_word_explosion": "D",
    "kin_word_pop": "D",
    "min_centered_statement": "C", "min_corner_tag": "A", "min_outro_title": "B", "min_single_line": "C",
    "min_subtitle_hairline": "B", "min_underline_reveal": "A",
    "pod_captions_highlight": "D", "pod_chapter_marker": "A", "pod_episode_card": "F",
    "pod_lower_third_slate": "E", "pod_outro_card": "B", "pod_quote_card": "B", "pod_speaker_switch": "E",
    "pod_talking_about": "A",
    "saas_bento_grid": "F", "saas_changelog_title": "C", "saas_cta_card": "D", "saas_feature_callout": "F",
    "saas_glass_card": "F", "saas_gradient_headline": "C", "saas_pill_badge": "D", "saas_shortcut_chips": "D",
    "saas_stat_counter": "F", "saas_step_titles": "A",
    "soc_3line_stack": "G", "soc_hook_pop": "D", "soc_keyword_box": "D", "soc_link_bio": "F",
    "soc_progress_marker": "A", "soc_reaction_tag": "D", "soc_split_twotone": "G",
}


def _is_vertical(layer):
    try:
        return float(layer["props"].get("height", 0)) > float(layer["props"].get("width", 1))
    except (TypeError, ValueError):
        return False


def kind_of(layer):
    t = layer["type"]
    if t == "text":
        return "text"
    if t == "shape_line":
        return "line"
    if layer.get("props", {}).get("role") == "plate":
        return "plate"
    return "shape"


def main():
    done = 0
    for path in sorted(glob.glob(os.path.join(ROOT, "data", "templates", "*", "*.json"))):
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
        recipe = RECIPES.get(ASSIGN.get(d["id"], ""))
        if recipe is None:
            continue
        ti = si = 0
        for layer in d["layers"]:
            kind = kind_of(layer)
            if kind == "text" and layer["props"].get("count"):
                # counters keep a whole-layer entrance so the number stays legible
                tracks, extra = r_soft_card(layer, "text", 1, 0)
            else:
                tracks, extra = recipe(layer, kind, ti, si)
            if kind == "line" and _is_vertical(layer):
                # vertical rules grow upward instead of a sideways wipe
                for t in tracks:
                    if t["property"] == "scale_x":
                        t["property"] = "scale_y"
                if extra.get("origin") in ("left", "right", "center"):
                    extra = dict(extra, origin="bottom")
            for p in ("clip", "stagger", "origin"):
                layer["props"].pop(p, None)
            layer["props"].update(extra)
            layer["motion_tracks"] = tracks
            if kind == "text":
                ti += 1
            else:
                si += 1
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(d, fh, indent=2, ensure_ascii=False)
        done += 1
    print(f"re-choreographed {done} templates")


if __name__ == "__main__":
    main()
