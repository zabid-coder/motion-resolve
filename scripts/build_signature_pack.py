"""
Build the "Signature" premium template pack (data/templates/signature/*.json).

Every template here is art-directed: explicit layout on a 1920x1080 reference
frame, real typography (installed weights such as 'Demi Bold'), and its own
motion language - masked rises, line draws, tracking breathes, blur-ins and
damped springs - all of which compile to real Fusion splines in Resolve.

Run:  python3 scripts/build_signature_pack.py
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "data", "templates", "signature")

WHITE = [0.98, 0.97, 0.95, 1.0]
SOFT = [0.98, 0.97, 0.95, 0.72]
MUTED = [0.98, 0.97, 0.95, 0.52]
INK = [0.05, 0.05, 0.06, 1.0]


# ---------------------------------------------------------------- helpers
def k(t, v, e="expoOut"):
    return {"time": round(t, 3), "value": v, "easing": e}


def tr(prop, phase, *keys):
    return {"property": prop, "phase": phase, "keyframes": list(keys)}


def fade_in(t0, t1, e="quartInOut"):
    return tr("opacity", "in", k(t0, 0, e), k(t1, 1, e))


def fade_out(t0, t1, e="cubicIn"):
    return tr("opacity", "out", k(t0, 1, e), k(t1, 0, e))


def rise_in(t0, t1, dist, e="quintOut"):
    return tr("translate_y", "in", k(t0, -dist, e), k(t1, 0, e))


def blur_in(t0, t1, amount=8.0):
    return tr("blur", "in", k(t0, amount, "expoOut"), k(t1, 0, "expoOut"))


def text(id_, name, text_, **props):
    p = {"text": text_}
    p.update(props)
    motion = p.pop("motion", [])
    return {"id": id_, "type": "text", "name": name, "props": p, "motion_tracks": motion}


def shape(id_, name, kind="shape_rect", **props):
    motion = props.pop("motion", [])
    return {"id": id_, "type": kind, "name": name, "props": props, "motion_tracks": motion}


def param(id_, name, type_, default, category="Text", **extra):
    d = {"id": id_, "name": name, "type": type_, "default": default, "category": category}
    d.update(extra)
    return d


def pos_params(x, y):
    return [
        param("pos_x", "Horizontal Anchor", "number", x, "Layout", min_val=0.04, max_val=0.96, step=0.005),
        param("pos_y", "Vertical Anchor", "number", y, "Layout", min_val=0.08, max_val=0.92, step=0.005),
    ]


def template(id_, name, category, description, tags, duration, in_d, out_d, params, layers):
    return {
        "id": id_, "name": name, "category": category, "tier": "premium",
        "description": description, "tags": tags + ["signature", "premium"],
        "aspect_ratios": ["16:9", "9:16", "1:1", "4:5"],
        "duration_default": duration, "min_hold": 1.5,
        "in_duration": in_d, "out_duration": out_d,
        "parameters": params, "layers": layers,
    }


X, Y = "param:pos_x", "param:pos_y"
ACCENT = "param:accent_color"

# ---------------------------------------------------------------- templates
T = []

# 1. Editorial name plate - line draw + masked rise + blurred role
T.append(template(
    "sig_editorial_lower_third", "Editorial Name Plate", "Signature",
    "Amber hairline draws in, the name rises from behind an invisible mask and the role settles out of a soft blur.",
    ["lower third", "interview", "documentary", "name"], 4.5, 0.95, 0.5,
    [param("name", "Name", "string", "Zara Khan"),
     param("role", "Role", "string", "Creative Director · Studio North"),
     param("accent_color", "Accent", "color", [0.96, 0.71, 0.36, 1.0], "Style")] + pos_params(0.075, 0.19),
    [
        shape("rule", "Accent Hairline", "shape_line", width=0.05, height=0.0042, color=ACCENT,
              center_x=X, offset_x=0.025, center_y=Y, offset_y=0.058, origin="left",
              motion=[fade_in(0.0, 0.08, "linear"),
                      tr("scale_x", "in", k(0.0, 0, "expoInOut"), k(0.6, 1)),
                      tr("scale_x", "out", k(0.1, 1, "expoIn"), k(0.45, 0)),
                      fade_out(0.4, 0.45, "linear")]),
        text("name", "Name", "param:name", font="Avenir Next", weight="Demi Bold", size=0.036,
             alignment="left", center_x=X, center_y=Y, offset_y=0.014, color=WHITE, clip=True,
             font_bn="Hind Siliguri", shadow={"opacity": 0.32, "softness": 0.03, "offset": [0, -0.003]},
             motion=[fade_in(0.12, 0.3, "linear"), rise_in(0.12, 0.8, 0.072),
                     tr("translate_y", "out", k(0.0, 0, "expoIn"), k(0.42, -0.072)),
                     fade_out(0.36, 0.42, "linear")]),
        text("role", "Role", "param:role", font="Avenir Next", weight="Medium", size=0.0185,
             character_spacing=1.14, uppercase=True, alignment="left", center_x=X, center_y=Y,
             offset_y=-0.036, color=SOFT, font_bn="Hind Siliguri",
             motion=[fade_in(0.38, 0.85), blur_in(0.38, 0.95, 7.0),
                     tr("translate_x", "in", k(0.38, -0.012), k(0.95, 0)),
                     fade_out(0.0, 0.3), tr("blur", "out", k(0.0, 0, "cubicIn"), k(0.3, 5.0, "cubicIn"))]),
    ]))

# 2. Documentary locator - tracking breath + rule growth
T.append(template(
    "sig_doc_locator", "Documentary Locator", "Signature",
    "Place and time super for field documentaries: a rule grows upward while the location breathes into its tracking.",
    ["documentary", "location", "date", "news", "ngo"], 5.0, 1.2, 0.6,
    [param("place", "Location", "string", "Kurigram, Bangladesh"),
     param("detail", "Date / Detail", "string", "14 July 2024  ·  06:42"),
     param("accent_color", "Accent", "color", [0.98, 0.80, 0.42, 1.0], "Style")] + pos_params(0.07, 0.78),
    [
        shape("rule", "Vertical Rule", "shape_line", width=0.0021, height=0.082, color=ACCENT,
              center_x=X, offset_x=-0.014, center_y=Y, offset_y=-0.002, origin="bottom",
              motion=[fade_in(0.0, 0.1, "linear"),
                      tr("scale_y", "in", k(0.0, 0, "expoInOut"), k(0.7, 1)),
                      tr("scale_y", "out", k(0.15, 1, "expoIn"), k(0.6, 0)),
                      fade_out(0.55, 0.6, "linear")]),
        text("place", "Location", "param:place", font="Avenir Next", weight="Demi Bold", size=0.03,
             uppercase=True, character_spacing=1.08, alignment="left", center_x=X, center_y=Y,
             offset_y=0.017, color=WHITE, font_bn="Hind Siliguri",
             shadow={"opacity": 0.45, "softness": 0.035, "offset": [0, -0.003]},
             motion=[fade_in(0.15, 0.6), blur_in(0.15, 0.9, 9.0),
                     tr("tracking", "in", k(0.15, 1.55, "expoOut"), k(1.2, 1.08)),
                     fade_out(0.0, 0.4), tr("tracking", "out", k(0.0, 1.08, "cubicIn"), k(0.4, 1.3, "cubicIn"))]),
        text("detail", "Date / Detail", "param:detail", font="Avenir Next", weight="Medium", size=0.019,
             character_spacing=1.06, alignment="left", center_x=X, center_y=Y, offset_y=-0.026,
             color=SOFT, font_bn="Hind Siliguri",
             shadow={"opacity": 0.45, "softness": 0.03, "offset": [0, -0.002]},
             motion=[fade_in(0.5, 0.95), rise_in(0.5, 1.1, 0.012), fade_out(0.0, 0.32)]),
    ]))

# 3. Cinematic title - long blur + tracking settle, hairline under
T.append(template(
    "sig_cinematic_title", "Cinematic Title", "Signature",
    "Film-title treatment: a Didot headline condenses out of a wide, blurred spread while a hairline opens beneath it.",
    ["title", "film", "opener", "cinematic", "trailer"], 6.0, 2.0, 1.0,
    [param("title", "Title", "string", "The Long Road Home"),
     param("credit", "Credit", "string", "A film by Tapash"),
     param("accent_color", "Hairline", "color", [1.0, 1.0, 1.0, 0.55], "Style")] + pos_params(0.5, 0.5),
    [
        text("title", "Title", "param:title", font="Didot", weight="Regular", size=0.058, uppercase=True,
             character_spacing=1.16, alignment="center", center_x=X, center_y=Y, offset_y=0.018,
             color=WHITE, font_bn="Tiro Bangla",
             shadow={"opacity": 0.35, "softness": 0.05, "offset": [0, 0]},
             motion=[fade_in(0.0, 1.0), blur_in(0.0, 1.4, 16.0),
                     tr("tracking", "in", k(0.0, 1.62, "expoOut"), k(2.0, 1.16)),
                     fade_out(0.0, 0.9, "quartInOut"), tr("blur", "out", k(0.0, 0, "expoIn"), k(0.9, 12.0)),
                     tr("tracking", "out", k(0.0, 1.16, "cubicIn"), k(1.0, 1.3, "cubicIn"))]),
        shape("hairline", "Hairline", "shape_line", width=0.14, height=0.0016, color=ACCENT,
              center_x=X, center_y=Y, offset_y=-0.036,
              motion=[fade_in(0.6, 0.8, "linear"),
                      tr("scale_x", "in", k(0.6, 0, "expoInOut"), k(1.6, 1)),
                      fade_out(0.0, 0.6)]),
        text("credit", "Credit", "param:credit", font="Avenir Next", weight="Medium", size=0.0165,
             uppercase=True, character_spacing=1.45, alignment="center", center_x=X, center_y=Y,
             offset_y=-0.07, color=SOFT, font_bn="Hind Siliguri",
             motion=[fade_in(1.0, 1.7), rise_in(1.0, 1.9, 0.01), fade_out(0.0, 0.5)]),
    ]))

# 4. Social hook - spring punch + highlighter wipe + masked line
T.append(template(
    "sig_social_hook", "Viral Hook Punch", "Signature",
    "Retention hook for Reels / Shorts: the first line springs in with a tilt, a highlighter wipes, the payoff rises inside it.",
    ["social", "hook", "reels", "shorts", "tiktok", "kinetic"], 2.8, 0.75, 0.3,
    [param("line1", "Setup", "string", "Wait for"),
     param("line2", "Payoff", "string", "The Twist"),
     param("accent_color", "Highlighter", "color", [1.0, 0.86, 0.12, 1.0], "Style")] + pos_params(0.5, 0.52),
    [
        shape("marker", "Highlighter", "shape_rect", width=0.36, height=0.118, corner_radius=10, color=ACCENT,
              center_x=X, center_y=Y, offset_y=-0.04, origin="left",
              motion=[fade_in(0.14, 0.16, "linear"),
                      tr("scale_x", "in", k(0.14, 0, "expoOut"), k(0.5, 1)),
                      tr("scale", "out", k(0.0, 1, "expoIn"), k(0.28, 0.85)), fade_out(0.1, 0.28)]),
        text("line1", "Setup", "param:line1", font="Montserrat", weight="Black", size=0.046, uppercase=True,
             alignment="center", center_x=X, center_y=Y, offset_y=0.058, color=[1, 1, 1, 1],
             shadow={"opacity": 0.55, "softness": 0.04, "offset": [0, -0.004]}, font_bn="Hind Siliguri",
             motion=[fade_in(0.0, 0.06, "linear"),
                     tr("scale", "in", k(0.0, 0.55, "spring"), k(0.55, 1.0)),
                     tr("rotation", "in", k(0.0, -7.0, "expoOut"), k(0.5, 0.0)),
                     tr("scale", "out", k(0.0, 1, "expoIn"), k(0.26, 0.8)), fade_out(0.08, 0.26)]),
        text("line2", "Payoff", "param:line2", font="Montserrat", weight="Black", size=0.066, uppercase=True,
             alignment="center", center_x=X, center_y=Y, offset_y=-0.04, color=INK, clip=True,
             shadow={"off": True}, font_bn="Hind Siliguri",
             motion=[fade_in(0.24, 0.3, "linear"), rise_in(0.24, 0.72, 0.12),
                     tr("scale", "out", k(0.0, 1, "expoIn"), k(0.28, 0.85)), fade_out(0.1, 0.28)]),
    ]))

# 5. Glass quote card
T.append(template(
    "sig_glass_quote", "Glass Pull Quote", "Signature",
    "Smoked-glass card springs up, a Didot quote mark lands, the quote resolves from blur with an accent attribution.",
    ["quote", "testimonial", "editorial", "interview"], 6.0, 1.2, 0.55,
    [param("quote", "Quote", "string", "We didn't move the river. We moved with it."),
     param("author", "Attribution", "string", "Rahima Begum, fisher"),
     param("quote_mark", "Quote Mark", "string", "\u201C", "Style"),
     param("accent_color", "Accent", "color", [0.96, 0.71, 0.36, 1.0], "Style"),
     param("plate_enabled", "Glass Card", "boolean", True, "Style")] + pos_params(0.5, 0.5),
    [
        shape("card", "Glass Card", "shape_rect", role="plate", width=0.44, height=0.33, corner_radius=30,
              color=[0.06, 0.06, 0.07, 0.82], border_color=[1, 1, 1, 0.14], border_width=1.5,
              center_x=X, center_y=Y, offset_y=-0.004,
              motion=[fade_in(0.0, 0.3), tr("scale", "in", k(0.0, 0.93, "softSpring"), k(0.65, 1)),
                      rise_in(0.0, 0.65, 0.025),
                      tr("scale", "out", k(0.1, 1, "expoIn"), k(0.55, 0.96)), fade_out(0.15, 0.55)]),
        text("mark", "Quote Mark", "param:quote_mark", font="Didot", weight="Bold", size=0.085, alignment="center",
             center_x=X, center_y=Y, offset_y=0.1, color=ACCENT, shadow={"off": True},
             motion=[fade_in(0.25, 0.45), tr("scale", "in", k(0.25, 0.4, "spring"), k(0.8, 1)), fade_out(0.0, 0.3)]),
        text("quote", "Quote", "param:quote", font="Hoefler Text", weight="Italic", size=0.033,
             alignment="center", text_width=0.4, wrap=True, line_spacing=1.02, center_x=X,
             center_y=Y, offset_y=0.012, color=WHITE, font_bn="Tiro Bangla", shadow={"off": True},
             motion=[fade_in(0.35, 0.9), blur_in(0.35, 1.05, 8.0), rise_in(0.35, 1.05, 0.012),
                     fade_out(0.0, 0.35)]),
        text("author", "Attribution", "param:author", font="Avenir Next", weight="Demi Bold", size=0.0165,
             uppercase=True, character_spacing=1.2, alignment="center", center_x=X,
             center_y=Y, offset_y=-0.098, color=ACCENT, font_bn="Hind Siliguri", shadow={"off": True},
             motion=[fade_in(0.7, 1.15), rise_in(0.7, 1.2, 0.01), fade_out(0.0, 0.3)]),
    ]))

# 6. Stat reveal
T.append(template(
    "sig_stat_reveal", "Impact Stat Reveal", "Signature",
    "Report-grade statistic: the figure springs out of blur, an accent bar measures across, the context line follows.",
    ["stat", "data", "number", "report", "ngo", "explainer"], 5.0, 1.3, 0.5,
    [param("figure", "Figure", "string", "87%"),
     param("label", "Context", "string", "of children in the char villages now attend school"),
     param("source", "Source", "string", "Source: District Education Office, 2024"),
     param("count_up", "Count Up Number", "boolean", True, "Motion"),
     param("count_duration", "Count Duration (s)", "number", 1.6, "Motion", min_val=0.4, max_val=4.0, step=0.1),
     param("accent_color", "Accent", "color", [0.36, 0.82, 0.98, 1.0], "Style")] + pos_params(0.5, 0.54),
    [
        text("figure", "Figure", "param:figure", font="Montserrat", weight="ExtraBold", size=0.1, count=True,
             alignment="center", center_x=X, center_y=Y, offset_y=0.06, color=ACCENT,
             shadow={"opacity": 0.4, "softness": 0.06, "offset": [0, -0.004]}, font_bn="Hind Siliguri",
             motion=[fade_in(0.0, 0.3), blur_in(0.0, 0.7, 12.0),
                     tr("scale", "in", k(0.0, 0.72, "spring"), k(0.8, 1.0)),
                     fade_out(0.0, 0.4), tr("scale", "out", k(0.0, 1, "expoIn"), k(0.4, 0.94))]),
        shape("bar", "Measure Bar", "shape_rect", width=0.16, height=0.0055, corner_radius=3, color=ACCENT,
              center_x=X, center_y=Y, offset_y=-0.032,
              motion=[fade_in(0.35, 0.4, "linear"), tr("scale_x", "in", k(0.35, 0, "expoInOut"), k(1.1, 1)),
                      tr("scale_x", "out", k(0.0, 1, "expoIn"), k(0.4, 0)), fade_out(0.35, 0.4, "linear")]),
        text("label", "Context", "param:label", font="Inter", weight="Medium", size=0.026, text_width=0.46, wrap=True,
             alignment="center", center_x=X, center_y=Y, offset_y=-0.09, color=WHITE, font_bn="Hind Siliguri",
             motion=[fade_in(0.6, 1.1), rise_in(0.6, 1.25, 0.014), fade_out(0.0, 0.32)]),
        text("source", "Source", "param:source", font="Inter", weight="Regular", size=0.0145,
             character_spacing=1.04, alignment="center", center_x=X, center_y=Y, offset_y=-0.168,
             color=MUTED, font_bn="Hind Siliguri",
             motion=[fade_in(1.0, 1.3), fade_out(0.0, 0.25)]),
    ]))

# 7. Chapter card
T.append(template(
    "sig_chapter_card", "Chapter Card", "Signature",
    "Chapter divider: twin rules open outward from the chapter number while a serif title settles out of blur.",
    ["chapter", "section", "documentary", "divider", "title"], 5.0, 1.5, 0.7,
    [param("chapter", "Chapter", "string", "Chapter 02"),
     param("title", "Title", "string", "The River Remembers"),
     param("accent_color", "Accent", "color", [0.96, 0.71, 0.36, 1.0], "Style")] + pos_params(0.5, 0.5),
    [
        shape("rule_l", "Left Rule", "shape_line", width=0.07, height=0.0018, color=ACCENT,
              center_x=X, offset_x=-0.125, center_y=Y, offset_y=0.068, origin="right",
              motion=[fade_in(0.1, 0.15, "linear"), tr("scale_x", "in", k(0.1, 0, "expoInOut"), k(0.9, 1)),
                      tr("scale_x", "out", k(0.0, 1, "expoIn"), k(0.5, 0)), fade_out(0.45, 0.5, "linear")]),
        shape("rule_r", "Right Rule", "shape_line", width=0.07, height=0.0018, color=ACCENT,
              center_x=X, offset_x=0.125, center_y=Y, offset_y=0.068, origin="left",
              motion=[fade_in(0.1, 0.15, "linear"), tr("scale_x", "in", k(0.1, 0, "expoInOut"), k(0.9, 1)),
                      tr("scale_x", "out", k(0.0, 1, "expoIn"), k(0.5, 0)), fade_out(0.45, 0.5, "linear")]),
        text("chapter", "Chapter", "param:chapter", font="Avenir Next", weight="Demi Bold", size=0.0175,
             uppercase=True, character_spacing=1.4, alignment="center", center_x=X, center_y=Y,
             offset_y=0.068, color=ACCENT, font_bn="Hind Siliguri", shadow={"off": True},
             motion=[fade_in(0.0, 0.5), tr("tracking", "in", k(0.0, 2.0, "expoOut"), k(1.0, 1.4)),
                     fade_out(0.0, 0.4)]),
        text("title", "Title", "param:title", font="Hoefler Text", weight="Regular", size=0.056,
             alignment="center", center_x=X, center_y=Y, offset_y=-0.004, color=WHITE, font_bn="Tiro Bangla",
             shadow={"opacity": 0.3, "softness": 0.05, "offset": [0, 0]},
             motion=[fade_in(0.3, 1.1), blur_in(0.3, 1.4, 12.0), rise_in(0.3, 1.5, 0.018),
                     fade_out(0.1, 0.7, "quartInOut"), tr("blur", "out", k(0.1, 0, "expoIn"), k(0.7, 8.0))]),
    ]))

# 8. News update tag
T.append(template(
    "sig_news_tag", "Live Update Bar", "Signature",
    "Broadcast update bar: the red tag snaps open, the label rises inside it, the headline bar sweeps out and the copy slides in.",
    ["news", "breaking", "update", "broadcast", "lower third"], 5.0, 0.9, 0.45,
    [param("tag", "Tag", "string", "Update"),
     param("headline", "Headline", "string", "Flood waters recede across northern districts"),
     param("accent_color", "Tag Colour", "color", [0.90, 0.13, 0.18, 1.0], "Style")] + pos_params(0.07, 0.16),
    [
        shape("bar", "Headline Bar", "shape_rect", width=0.62, height=0.072, corner_radius=4,
              color=[0.06, 0.06, 0.07, 0.92], center_x=X, offset_x=0.31, center_y=Y, offset_y=-0.03,
              origin="left",
              motion=[fade_in(0.12, 0.16, "linear"), tr("scale_x", "in", k(0.12, 0, "expoInOut"), k(0.62, 1)),
                      tr("scale_x", "out", k(0.05, 1, "expoIn"), k(0.42, 0)), fade_out(0.38, 0.42, "linear")]),
        shape("tag_block", "Tag Block", "shape_rect", width=0.105, height=0.05, corner_radius=4, color=ACCENT,
              center_x=X, offset_x=0.0525, center_y=Y, offset_y=0.034, origin="left",
              motion=[fade_in(0.0, 0.04, "linear"), tr("scale_x", "in", k(0.0, 0, "expoOut"), k(0.32, 1)),
                      tr("scale_x", "out", k(0.12, 1, "expoIn"), k(0.45, 0)), fade_out(0.42, 0.45, "linear")]),
        text("tag", "Tag", "param:tag", font="Inter", weight="ExtraBold", size=0.0185, uppercase=True,
             character_spacing=1.16, alignment="center", center_x=X, offset_x=0.0525, center_y=Y,
             offset_y=0.034, color=[1, 1, 1, 1], clip=True, shadow={"off": True}, font_bn="Hind Siliguri",
             motion=[fade_in(0.14, 0.18, "linear"), rise_in(0.14, 0.5, 0.04), fade_out(0.0, 0.2)]),
        text("headline", "Headline", "param:headline", font="Inter", weight="SemiBold", size=0.026,
             alignment="left", center_x=X, offset_x=0.018, center_y=Y, offset_y=-0.03, color=WHITE,
             clip=True, shadow={"off": True}, font_bn="Hind Siliguri",
             motion=[fade_in(0.3, 0.6), tr("translate_x", "in", k(0.3, -0.04), k(0.85, 0)), fade_out(0.0, 0.22)]),
    ]))

# 9. Speaker pill
T.append(template(
    "sig_speaker_pill", "Live Speaker Pill", "Signature",
    "Podcast / panel speaker pill: the capsule unrolls from its live dot, which pops with a spring before the name lands.",
    ["podcast", "speaker", "panel", "live", "social"], 4.0, 0.85, 0.4,
    [param("name", "Name", "string", "Nusrat Jahan"),
     param("detail", "Detail", "string", "Host · The Long Table"),
     param("accent_color", "Live Dot", "color", [0.24, 0.86, 0.52, 1.0], "Style")] + pos_params(0.06, 0.15),
    [
        shape("pill", "Capsule", "shape_pill", width=0.25, height=0.082, color=[0.08, 0.08, 0.09, 0.9],
              border_color=[1, 1, 1, 0.12], border_width=1.5, center_x=X, offset_x=0.125, center_y=Y,
              origin="left",
              motion=[fade_in(0.0, 0.12), tr("scale_x", "in", k(0.0, 0.17, "expoInOut"), k(0.6, 1)),
                      tr("scale_x", "out", k(0.05, 1, "expoIn"), k(0.4, 0.17)), fade_out(0.25, 0.4)]),
        shape("dot", "Live Dot", "shape_pill", width=0.0115, height=0.0204, color=ACCENT,
              center_x=X, offset_x=0.03, center_y=Y,
              motion=[fade_in(0.05, 0.1, "linear"), tr("scale", "in", k(0.05, 0, "spring"), k(0.5, 1)),
                      fade_out(0.2, 0.35)]),
        text("name", "Name", "param:name", font="Inter", weight="SemiBold", size=0.023, alignment="left",
             center_x=X, offset_x=0.05, center_y=Y, offset_y=0.011, color=WHITE, shadow={"off": True},
             font_bn="Hind Siliguri",
             motion=[fade_in(0.28, 0.6), tr("translate_x", "in", k(0.28, -0.01), k(0.75, 0)), fade_out(0.0, 0.2)]),
        text("detail", "Detail", "param:detail", font="Inter", weight="Medium", size=0.0155, alignment="left",
             center_x=X, offset_x=0.05, center_y=Y, offset_y=-0.015, color=MUTED, shadow={"off": True},
             font_bn="Hind Siliguri",
             motion=[fade_in(0.4, 0.8), tr("translate_x", "in", k(0.4, -0.01), k(0.85, 0)), fade_out(0.0, 0.2)]),
    ]))

# 10. Follow CTA end card
T.append(template(
    "sig_follow_cta", "Follow End Card", "Signature",
    "End-card call to action: the handle resolves from blur and the button lands with a damped spring.",
    ["cta", "end card", "subscribe", "follow", "social"], 4.0, 1.1, 0.4,
    [param("kicker", "Kicker", "string", "More stories every week"),
     param("handle", "Handle", "string", "@tapash.films"),
     param("button", "Button", "string", "Follow"),
     param("accent_color", "Button", "color", [1.0, 0.27, 0.36, 1.0], "Style")] + pos_params(0.5, 0.5),
    [
        text("kicker", "Kicker", "param:kicker", font="Inter", weight="Medium", size=0.019, alignment="center",
             center_x=X, center_y=Y, offset_y=0.1, color=SOFT, font_bn="Hind Siliguri",
             motion=[fade_in(0.0, 0.4), rise_in(0.0, 0.6, 0.012), fade_out(0.0, 0.25)]),
        text("handle", "Handle", "param:handle", font="Inter", weight="Bold", size=0.042, alignment="center",
             center_x=X, center_y=Y, offset_y=0.028, color=WHITE, font_bn="Hind Siliguri",
             shadow={"opacity": 0.4, "softness": 0.05, "offset": [0, -0.003]},
             motion=[fade_in(0.1, 0.5), blur_in(0.1, 0.7, 10.0),
                     tr("scale", "in", k(0.1, 0.92, "expoOut"), k(0.8, 1)), fade_out(0.0, 0.3)]),
        shape("btn", "Button", "shape_pill", width=0.13, height=0.072, color=ACCENT,
              center_x=X, center_y=Y, offset_y=-0.072,
              motion=[fade_in(0.4, 0.45, "linear"), tr("scale", "in", k(0.4, 0, "spring"), k(1.05, 1)),
                      tr("scale", "out", k(0.0, 1, "backIn"), k(0.38, 0)), fade_out(0.3, 0.38, "linear")]),
        text("btn_label", "Button Label", "param:button", font="Inter", weight="ExtraBold", size=0.019,
             uppercase=True, character_spacing=1.14, alignment="center", center_x=X, center_y=Y,
             offset_y=-0.072, color=[1, 1, 1, 1], shadow={"off": True}, font_bn="Hind Siliguri",
             motion=[fade_in(0.55, 0.7), tr("scale", "in", k(0.5, 0.6, "spring"), k(1.05, 1)),
                     tr("scale", "out", k(0.0, 1, "backIn"), k(0.3, 0.5)), fade_out(0.1, 0.3)]),
    ]))

# 11. Bengali headline
T.append(template(
    "sig_bengali_headline", "বাংলা শিরোনাম · Bengali Headline", "Signature",
    "Bengali-first headline super set in Hind Siliguri with conjunct-safe masks, an accent tag and Bengali numerals.",
    ["bengali", "bangla", "news", "headline", "lower third"], 5.0, 1.0, 0.45,
    [param("tag", "Tag", "string", "বিশেষ প্রতিবেদন"),
     param("headline", "Headline", "string", "নদীভাঙনে ঘরহারা হাজারো পরিবার"),
     param("detail", "Detail", "string", "কুড়িগ্রাম  ·  ১৪ জুলাই ২০২৪"),
     param("accent_color", "Accent", "color", [0.98, 0.33, 0.27, 1.0], "Style")] + pos_params(0.07, 0.2),
    [
        shape("tag_block", "Tag Block", "shape_rect", width=0.135, height=0.054, corner_radius=5, color=ACCENT,
              center_x=X, offset_x=0.0675, center_y=Y, offset_y=0.084, origin="left",
              motion=[fade_in(0.0, 0.04, "linear"), tr("scale_x", "in", k(0.0, 0, "expoOut"), k(0.35, 1)),
                      tr("scale_x", "out", k(0.1, 1, "expoIn"), k(0.45, 0)), fade_out(0.42, 0.45, "linear")]),
        text("tag", "Tag", "param:tag", font="Hind Siliguri", font_bn="Hind Siliguri", weight="SemiBold",
             size=0.021, alignment="center", center_x=X, offset_x=0.0675, center_y=Y, offset_y=0.082,
             color=[1, 1, 1, 1], clip=True, shadow={"off": True},
             motion=[fade_in(0.14, 0.2, "linear"), rise_in(0.14, 0.55, 0.045), fade_out(0.0, 0.2)]),
        text("headline", "Headline", "param:headline", font="Hind Siliguri", font_bn="Hind Siliguri",
             weight="Bold", size=0.04, alignment="left", center_x=X, center_y=Y, offset_y=0.012, color=WHITE,
             clip=True, shadow={"opacity": 0.4, "softness": 0.035, "offset": [0, -0.003]},
             motion=[fade_in(0.25, 0.4, "linear"), rise_in(0.25, 0.9, 0.08),
                     tr("translate_y", "out", k(0.0, 0, "expoIn"), k(0.42, -0.08)), fade_out(0.36, 0.42, "linear")]),
        text("detail", "Detail", "param:detail", font="Hind Siliguri", font_bn="Hind Siliguri", weight="Medium",
             size=0.021, alignment="left", center_x=X, center_y=Y, offset_y=-0.05, color=SOFT,
             shadow={"opacity": 0.4, "softness": 0.03, "offset": [0, -0.002]},
             motion=[fade_in(0.55, 0.95), blur_in(0.55, 1.0, 6.0), fade_out(0.0, 0.3)]),
    ]))


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    for t in T:
        path = os.path.join(OUT_DIR, t["id"] + ".json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(t, fh, ensure_ascii=False, indent=2)
        print("wrote", os.path.relpath(path, ROOT))


if __name__ == "__main__":
    main()
