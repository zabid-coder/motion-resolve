"""
Build the "Trend 2026" templates (data/templates/trend/*.json).

Original designs informed by the patterns in docs/design/motion-trends-2026.md
(two-tone stacked lower thirds, role chips, AI prompt typing, kinetic stacks,
glow hero words, count-up stats, typewriter heroes, per-line boxes).
They live in the Signature category so they appear under the ★ filter.

Run:  python3 scripts/build_trend_pack.py
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_signature_pack import (  # noqa: E402
    WHITE, SOFT, MUTED, INK, k, tr, fade_in, fade_out, rise_in, blur_in,
    text, shape, param, pos_params, template, X, Y, ACCENT,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "templates", "trend")
CAT = "Signature"
T = []


def wipe(t0, t1, out0=0.1, out1=0.42, origin="left"):
    return [fade_in(t0, t0 + 0.04, "linear"), tr("scale_x", "in", k(t0, 0, "expoInOut"), k(t1, 1)),
            tr("scale_x", "out", k(out0, 1, "expoIn"), k(out1, 0)), fade_out(out1 - 0.04, out1, "linear")]


# 1. Two-tone stacked lower third ------------------------------------------------
T.append(template(
    "trend_two_tone_stack", "Two-Tone Stack", CAT,
    "Name on a solid accent block, role on a dark block beneath; both wipe in from the left and the name rises inside its block.",
    ["lower third", "trend", "news", "creator", "interview"], 4.5, 0.9, 0.45,
    [param("name", "Name", "string", "Arif Hossain"), param("role", "Role", "string", "Field Producer"),
     param("accent_color", "Name Block", "color", [0.99, 0.82, 0.18, 1.0], "Style")] + pos_params(0.07, 0.2),
    [
        shape("name_block", "Name Block", width=0.25, height=0.078, color=ACCENT, center_x=X, offset_x=0.125,
              center_y=Y, offset_y=0.03, origin="left", motion=wipe(0.0, 0.42)),
        shape("role_block", "Role Block", width=0.17, height=0.052, color=[0.06, 0.06, 0.07, 0.94], center_x=X,
              offset_x=0.085, center_y=Y, offset_y=-0.038, origin="left", motion=wipe(0.12, 0.55, 0.0, 0.34)),
        text("name", "Name", "param:name", font="Inter", weight="ExtraBold", size=0.03, uppercase=True,
             alignment="left", center_x=X, offset_x=0.016, center_y=Y, offset_y=0.03, color=INK, clip=True,
             shadow={"off": True}, font_bn="Hind Siliguri",
             motion=[fade_in(0.2, 0.26, "linear"), rise_in(0.2, 0.62, 0.065), fade_out(0.0, 0.18)]),
        text("role", "Role", "param:role", font="Inter", weight="SemiBold", size=0.019, uppercase=True,
             character_spacing=1.12, alignment="left", center_x=X, offset_x=0.016, center_y=Y, offset_y=-0.038,
             color=WHITE, shadow={"off": True}, font_bn="Hind Siliguri",
             motion=[fade_in(0.36, 0.6), tr("translate_x", "in", k(0.36, -0.015), k(0.75, 0)), fade_out(0.0, 0.16)]),
    ]))

# 2. Role chip -------------------------------------------------------------------
T.append(template(
    "trend_role_chip", "Name + Role Chip", CAT,
    "Clean name that cascades in letter by letter, with a coloured role chip that pops beside it.",
    ["lower third", "trend", "podcast", "minimal", "interview"], 4.0, 0.9, 0.4,
    [param("name", "Name", "string", "Nusrat Jahan"), param("role", "Role", "string", "DIRECTOR"),
     param("accent_color", "Chip", "color", [0.36, 0.55, 1.0, 1.0], "Style")] + pos_params(0.07, 0.18),
    [
        text("name", "Name", "param:name", font="Inter", weight="SemiBold", size=0.034, alignment="left",
             center_x=X, center_y=Y, offset_y=0.024, color=WHITE, stagger={"delay": 1.0}, font_bn="Hind Siliguri",
             shadow={"opacity": 0.4, "softness": 0.03, "offset": [0, -0.003]},
             motion=[fade_in(0.0, 0.3), tr("translate_y", "in", k(0.0, -0.018), k(0.45, 0)),
                     tr("blur", "in", k(0.0, 5.0), k(0.4, 0)), fade_out(0.0, 0.26)]),
        shape("chip", "Role Chip", "shape_rect", fit_to="role", color=ACCENT, pad_x=0.55, pad_y=0.32, round=0.5),
        text("role", "Role", "param:role", font="Inter", weight="Bold", size=0.0165, uppercase=True,
             character_spacing=1.12, alignment="left", center_x=X, offset_x=0.006, center_y=Y, offset_y=-0.03,
             color=[1, 1, 1, 1], shadow={"off": True}, font_bn="Hind Siliguri",
             motion=[fade_in(0.45, 0.5, "linear"), tr("scale", "in", k(0.45, 0.5, "softSpring"), k(0.9, 1)),
                     tr("scale", "out", k(0.0, 1, "expoIn"), k(0.25, 0.8)), fade_out(0.05, 0.25)]),
    ]))

# 3. AI prompt bar ---------------------------------------------------------------
T.append(template(
    "trend_ai_prompt", "AI Prompt Bar", CAT,
    "A rounded prompt bar springs up, the question types itself in, and the send button lights up.",
    ["ai", "prompt", "search", "trend", "tech", "social"], 5.0, 2.2, 0.45,
    [param("prompt", "Prompt", "string", "How do floods change a village?"),
     param("send_icon", "Send Icon", "string", "\u2191", "Style"),
     param("accent_color", "Send Button", "color", [0.55, 0.42, 1.0, 1.0], "Style")] + pos_params(0.5, 0.5),
    [
        shape("bar", "Prompt Bar", "shape_pill", width=0.56, height=0.1, color=[0.09, 0.09, 0.11, 0.95],
              border_color=[1, 1, 1, 0.16], border_width=1.5, center_x=X, center_y=Y,
              motion=[fade_in(0.0, 0.25), tr("scale", "in", k(0.0, 0.9, "softSpring"), k(0.6, 1)),
                      rise_in(0.0, 0.6, 0.02), tr("scale", "out", k(0.1, 1, "expoIn"), k(0.45, 0.94)),
                      fade_out(0.15, 0.45)]),
        text("prompt", "Prompt", "param:prompt", font="Inter", weight="Medium", size=0.025, alignment="left",
             center_x=X, offset_x=-0.25, center_y=Y, color=WHITE, shadow={"off": True}, font_bn="Hind Siliguri",
             motion=[fade_in(0.3, 0.34, "linear"), tr("write_on", "in", k(0.35, 0.0, "linear"), k(2.0, 1.0)),
                     fade_out(0.0, 0.25)]),
        shape("send", "Send Button", "shape_pill", width=0.034, height=0.0604, color=ACCENT, center_x=X,
              offset_x=0.245, center_y=Y,
              motion=[fade_in(1.9, 1.95, "linear"), tr("scale", "in", k(1.9, 0.3, "spring"), k(2.2, 1)),
                      fade_out(0.05, 0.3)]),
        text("arrow", "Send Arrow", "param:send_icon", font="Inter", weight="Bold", size=0.024, alignment="center",
             center_x=X, offset_x=0.245, center_y=Y, color=[1, 1, 1, 1], shadow={"off": True},
             motion=[fade_in(2.0, 2.1), rise_in(2.0, 2.2, 0.01), fade_out(0.0, 0.2)]),
    ]))

# 4. Kinetic stack with scribble underline ----------------------------------------
T.append(template(
    "trend_kinetic_stack", "Kinetic Stack + Underline", CAT,
    "Three heavy lines: the first slams, the second pops letter by letter, the third lands in accent with a marker underline.",
    ["kinetic", "social", "hook", "trend", "reels", "bold"], 3.2, 1.1, 0.3,
    [param("line1", "Line 1", "string", "Fastest"), param("line2", "Line 2", "string", "Way to"),
     param("line3", "Line 3", "string", "Grow"),
     param("accent_color", "Accent", "color", [1.0, 0.24, 0.24, 1.0], "Style")] + pos_params(0.5, 0.5),
    [
        text("line1", "Line 1", "param:line1", font="Montserrat", weight="Black", size=0.06, uppercase=True,
             alignment="center", center_x=X, center_y=Y, offset_y=0.105, color=WHITE, font_bn="Hind Siliguri",
             shadow={"opacity": 0.5, "softness": 0.04, "offset": [0, -0.004]},
             motion=[fade_in(0.0, 0.05, "linear"), tr("scale", "in", k(0.0, 1.6, "expoOut"), k(0.35, 1)),
                     tr("blur", "in", k(0.0, 8.0), k(0.2, 0)), tr("scale", "out", k(0.0, 1, "expoIn"), k(0.22, 1.12)),
                     fade_out(0.06, 0.22)]),
        text("line2", "Line 2", "param:line2", font="Montserrat", weight="Black", size=0.06, uppercase=True,
             alignment="center", center_x=X, center_y=Y, offset_y=0.0, color=WHITE, stagger={"delay": 1.2},
             font_bn="Hind Siliguri", shadow={"opacity": 0.5, "softness": 0.04, "offset": [0, -0.004]},
             motion=[fade_in(0.25, 0.3, "linear"), tr("scale", "in", k(0.25, 0.2, "spring"), k(0.7, 1)),
                     fade_out(0.0, 0.18)]),
        text("line3", "Line 3", "param:line3", font="Montserrat", weight="Black", size=0.075, uppercase=True,
             alignment="center", center_x=X, center_y=Y, offset_y=-0.12, color=ACCENT, clip=True,
             font_bn="Hind Siliguri", shadow={"opacity": 0.5, "softness": 0.04, "offset": [0, -0.004]},
             motion=[fade_in(0.55, 0.6, "linear"), rise_in(0.55, 0.95, 0.14), fade_out(0.0, 0.18)]),
        shape("underline", "Marker Underline", "shape_rect", width=0.24, height=0.014, corner_radius=8,
              color=ACCENT, center_x=X, center_y=Y, offset_y=-0.205, origin="left",
              motion=wipe(0.85, 1.1, 0.0, 0.22)),
    ]))

# 5. Glow hero word --------------------------------------------------------------
T.append(template(
    "trend_glow_hero", "Glow Hero Word", CAT,
    "A quiet setup line, then a hero word that resolves out of its own neon glow.",
    ["glow", "neon", "title", "trend", "tech", "hero"], 4.5, 1.4, 0.5,
    [param("setup", "Setup", "string", "Welcome to the"), param("hero", "Hero Word", "string", "Future"),
     param("accent_color", "Glow Colour", "color", [0.38, 0.86, 1.0, 1.0], "Style")] + pos_params(0.5, 0.5),
    [
        text("setup", "Setup", "param:setup", font="Inter", weight="Medium", size=0.03, alignment="center",
             center_x=X, center_y=Y, offset_y=0.075, color=SOFT, font_bn="Hind Siliguri", stagger={"delay": 0.8},
             motion=[fade_in(0.0, 0.3), tr("translate_y", "in", k(0.0, -0.012), k(0.45, 0)), fade_out(0.0, 0.3)]),
        text("hero_glow", "Hero Glow", "param:hero", font="Montserrat", weight="ExtraBold", size=0.085,
             alignment="center", center_x=X, center_y=Y, offset_y=-0.02, color=ACCENT, glow_blur=18.0,
             shadow={"off": True}, font_bn="Hind Siliguri",
             motion=[fade_in(0.45, 0.9), tr("opacity", "out", k(0.0, 1, "cubicIn"), k(0.45, 0, "cubicIn")),
                     tr("scale", "in", k(0.45, 1.25, "expoOut"), k(1.3, 1))]),
        text("hero", "Hero Word", "param:hero", font="Montserrat", weight="ExtraBold", size=0.085,
             alignment="center", center_x=X, center_y=Y, offset_y=-0.02, color=[1, 1, 1, 1], shadow={"off": True},
             font_bn="Hind Siliguri",
             motion=[fade_in(0.55, 1.0), blur_in(0.55, 1.2, 10.0), tr("scale", "in", k(0.55, 1.08, "expoOut"), k(1.3, 1)),
                     fade_out(0.0, 0.4), tr("blur", "out", k(0.0, 0, "expoIn"), k(0.4, 6.0))]),
    ]))

# 6. Count-up stat card ----------------------------------------------------------
T.append(template(
    "trend_count_stat", "Count-Up Stat Card", CAT,
    "The figure counts up while a progress bar fills in sync; label and source follow.",
    ["stat", "counter", "number", "data", "trend", "report"], 5.0, 1.8, 0.45,
    [param("figure", "Figure", "string", "2,450"), param("label", "Label", "string", "families reached this year"),
     param("source", "Source", "string", "Field data, 2026"),
     param("count_up", "Count Up Number", "boolean", True, "Motion"),
     param("count_duration", "Count Duration (s)", "number", 1.6, "Motion", min_val=0.4, max_val=4.0, step=0.1),
     param("accent_color", "Accent", "color", [0.29, 0.87, 0.6, 1.0], "Style")] + pos_params(0.5, 0.52),
    [
        shape("card", "Card", "shape_rect", role="plate", width=0.4, height=0.3, corner_radius=26,
              color=[0.06, 0.06, 0.07, 0.86], border_color=[1, 1, 1, 0.1], border_width=1.5, center_x=X,
              center_y=Y, offset_y=-0.01,
              motion=[fade_in(0.0, 0.3), tr("scale", "in", k(0.0, 0.94, "softSpring"), k(0.6, 1)),
                      tr("scale", "out", k(0.1, 1, "expoIn"), k(0.45, 0.96)), fade_out(0.15, 0.45)]),
        text("figure", "Figure", "param:figure", font="Montserrat", weight="ExtraBold", size=0.075, count=True,
             alignment="center", center_x=X, center_y=Y, offset_y=0.055, color=WHITE, shadow={"off": True},
             font_bn="Hind Siliguri",
             motion=[fade_in(0.15, 0.4), rise_in(0.15, 0.6, 0.015), fade_out(0.0, 0.25)]),
        shape("track", "Bar Track", "shape_rect", width=0.3, height=0.008, corner_radius=4,
              color=[1, 1, 1, 0.12], center_x=X, center_y=Y, offset_y=-0.02,
              motion=[fade_in(0.15, 0.35), fade_out(0.0, 0.25)]),
        shape("bar", "Progress Bar", "shape_rect", width=0.3, height=0.008, corner_radius=4, color=ACCENT,
              center_x=X, center_y=Y, offset_y=-0.02, origin="left",
              motion=[fade_in(0.15, 0.2, "linear"), tr("scale_x", "in", k(0.15, 0, "expoOut"), k(1.75, 1)),
                      fade_out(0.0, 0.25)]),
        text("label", "Label", "param:label", font="Inter", weight="Medium", size=0.021, alignment="center",
             center_x=X, center_y=Y, offset_y=-0.068, color=SOFT, shadow={"off": True}, font_bn="Hind Siliguri",
             motion=[fade_in(0.55, 0.95), rise_in(0.55, 1.0, 0.01), fade_out(0.0, 0.22)]),
        text("source", "Source", "param:source", font="Inter", weight="Regular", size=0.0145, alignment="center",
             center_x=X, center_y=Y, offset_y=-0.112, color=MUTED, shadow={"off": True}, font_bn="Hind Siliguri",
             motion=[fade_in(0.9, 1.2), fade_out(0.0, 0.2)]),
    ]))

# 7. Typewriter + hero ------------------------------------------------------------
T.append(template(
    "trend_typewriter_hero", "Typewriter + Hero", CAT,
    "The first line types itself on; then the hero line rises in accent from behind a mask.",
    ["typewriter", "title", "trend", "documentary", "hook"], 4.8, 2.0, 0.45,
    [param("line", "Typed Line", "string", "The future is"), param("hero", "Hero Line", "string", "already here"),
     param("accent_color", "Hero Colour", "color", [0.74, 1.0, 0.36, 1.0], "Style")] + pos_params(0.5, 0.5),
    [
        text("line", "Typed Line", "param:line", font="Inter", weight="Medium", size=0.04, alignment="center",
             center_x=X, center_y=Y, offset_y=0.04, color=WHITE, font_bn="Hind Siliguri",
             shadow={"opacity": 0.35, "softness": 0.03, "offset": [0, -0.003]},
             motion=[fade_in(0.0, 0.04, "linear"), tr("write_on", "in", k(0.0, 0.0, "linear"), k(1.1, 1.0)),
                     fade_out(0.0, 0.3)]),
        text("hero", "Hero Line", "param:hero", font="Inter", weight="ExtraBold", size=0.052, alignment="center",
             center_x=X, center_y=Y, offset_y=-0.04, color=ACCENT, clip=True, font_bn="Hind Siliguri",
             shadow={"opacity": 0.35, "softness": 0.03, "offset": [0, -0.003]},
             motion=[fade_in(1.15, 1.2, "linear"), rise_in(1.15, 1.75, 0.1),
                     tr("translate_y", "out", k(0.0, 0, "expoIn"), k(0.4, -0.1)), fade_out(0.34, 0.4, "linear")]),
    ]))

# 8. Per-line boxes ---------------------------------------------------------------
T.append(template(
    "trend_line_boxes", "Per-Line Box Caption", CAT,
    "Each line gets its own tight box; the lines slide in one after the other.",
    ["caption", "boxes", "social", "trend", "reels"], 3.6, 0.8, 0.35,
    [param("line1", "Line 1", "string", "Nobody tells you"), param("line2", "Line 2", "string", "this about editing"),
     param("accent_color", "Box Colour", "color", [1.0, 1.0, 1.0, 1.0], "Style")] + pos_params(0.5, 0.3),
    [
        shape("box1", "Box 1", "shape_rect", fit_to="line1", color=ACCENT, pad_x=0.32, pad_y=0.14, round=0.18),
        shape("box2", "Box 2", "shape_rect", fit_to="line2", color=ACCENT, pad_x=0.32, pad_y=0.14, round=0.18),
        text("line1", "Line 1", "param:line1", font="Inter", weight="ExtraBold", size=0.034, alignment="center",
             center_x=X, center_y=Y, offset_y=0.032, color=INK, shadow={"off": True}, font_bn="Hind Siliguri",
             motion=[fade_in(0.0, 0.12), tr("translate_x", "in", k(0.0, -0.04, "quintOut"), k(0.45, 0)),
                     tr("translate_x", "out", k(0.0, 0, "expoIn"), k(0.3, 0.03)), fade_out(0.1, 0.3)]),
        text("line2", "Line 2", "param:line2", font="Inter", weight="ExtraBold", size=0.034, alignment="center",
             center_x=X, center_y=Y, offset_y=-0.032, color=INK, shadow={"off": True}, font_bn="Hind Siliguri",
             motion=[fade_in(0.14, 0.26), tr("translate_x", "in", k(0.14, 0.04, "quintOut"), k(0.6, 0)),
                     tr("translate_x", "out", k(0.05, 0, "expoIn"), k(0.33, -0.03)), fade_out(0.13, 0.33)]),
    ]))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for t in T:
        for tg in ("signature",):
            if tg in t["tags"]:
                t["tags"].remove(tg)
        t["tags"].append("trend 2026")
        with open(os.path.join(OUT_DIR, t["id"] + ".json"), "w", encoding="utf-8") as fh:
            json.dump(t, fh, ensure_ascii=False, indent=2)
        print("wrote", t["id"])


if __name__ == "__main__":
    main()
