# Stripe Alert Notification Card Benchmark Design

> **Document:** `docs/superpowers/specs/2026-10-29-stripe-notification-benchmark-design.md`  
> **Topic:** Overhaul and benchmark implementation of `agency_stripe_notification` template into an Apple iOS native, broadcast-grade notification card with staggered multi-layer motion physics and exit animations.

---

## 1. Executive Summary & Objective

The user identified that existing templates and presets lack professional, "up to the mark" motion, in/out transitions, and typography. The goal of this design is to establish the gold standard benchmark starting with the **Stripe Notification Card (`agency_stripe_notification`)**, perfecting its In/Out motion curves, layer stagger timings, Apple iOS native graphite/emerald aesthetics, and Fusion timeline compilation.

---

## 2. Design System & Aesthetics (Apple iOS Native)

| Element | Specification | Tokens & Values |
| :--- | :--- | :--- |
| **Card Plate** | Frosted Apple Graphite Glass | Color: `[0.11, 0.11, 0.12, 0.88]` (`#1c1c1e`), Corner Radius: `18`, Border: `[0.25, 0.25, 0.28, 0.6]`, Ambient Soft Shadow: `0.045` |
| **App Source Header** | Clean Secondary Label | Text: `"Stripe • now"`, Font: `Inter` / `SF Pro Display`, Color: `[0.56, 0.56, 0.58, 1.0]` (`#8e8e93`), Size: `0.036`, Tracking: `+0.8` |
| **Notification Title** | Crisp White Headline | Text: `"Payment Received"`, Font: `Inter` / `SF Pro Display`, Weight: `Bold`, Color: `[1.0, 1.0, 1.0, 1.0]`, Size: `0.050` |
| **Payment Amount** | iOS Emerald Pill | Text: `"+$2,000.00"`, Font: `Inter` / `SF Pro Display`, Weight: `Heavy`, Color: `[0.20, 0.78, 0.35, 1.0]` (`#34c759`), Size: `0.056` |

---

## 3. Motion Curves & Staggered Timing Architecture

The card enters from the top via a mobile push alert drop, settles smoothly, staggers each text line, pops the amount, and cleanly drives off-screen during exit.

### Timing Breakdown (Normalized & Frame Offsets at 24fps)

- **Total Default Duration:** 3.8s (91 frames)
- **Entrance Window:** 0.55s (~13 frames)
- **Hold Window:** Frames 14 to (Total - 8)
- **Exit Window:** 0.33s (~8 frames)

### Layer Motion Track Specs

```
Frame:  0   1   2   3   4   5   6   7   8   9  10  11  12  13  ...  End-8   End
Plate:  [======= Top-Drop translate_y (-0.07 -> 0.0) =======]        [=== Push Up & Fade ===]
App:        [======= Stagger Rise (-0.04 -> 0.0) =======]            [=== Push Up & Fade ===]
Title:          [======= Stagger Rise (-0.04 -> 0.0) =======]        [=== Push Up & Fade ===]
Amount:                 [==== Tactile Spring Pop (0.65 -> 1.08 -> 1.0) ===]  [=== Zoom Out & Fade ===]
```

1. **`card_plate`**:
   - `phase: "in"`, `opacity`: 0.0 -> 1.0 (Frames 0–8, `quartInOut`)
   - `phase: "in"`, `translate_y`: -0.07 -> 0.0 (Frames 0–12, `expoOut`)
   - `phase: "out"`, `translate_y`: 0.0 -> -0.06 (Frames End-8 to End, `cubicIn`)
   - `phase: "out"`, `opacity`: 1.0 -> 0.0 (Frames End-8 to End, `cubicIn`)

2. **`app_name` ("Stripe • now")**:
   - `phase: "in"`, `opacity`: 0.0 -> 1.0 (Frames 2–10, `quartInOut`)
   - `phase: "in"`, `translate_y`: -0.04 -> 0.0 (Frames 2–12, `expoOut`)
   - `phase: "out"`, `translate_y`: 0.0 -> -0.05 (Frames End-8 to End, `cubicIn`)
   - `phase: "out"`, `opacity`: 1.0 -> 0.0 (Frames End-8 to End, `cubicIn`)

3. **`msg_title` ("Payment Received")**:
   - `phase: "in"`, `opacity`: 0.0 -> 1.0 (Frames 3–11, `quartInOut`)
   - `phase: "in"`, `translate_y`: -0.04 -> 0.0 (Frames 3–13, `expoOut`)
   - `phase: "out"`, `translate_y`: 0.0 -> -0.05 (Frames End-8 to End, `cubicIn`)
   - `phase: "out"`, `opacity`: 1.0 -> 0.0 (Frames End-8 to End, `cubicIn`)

4. **`amount_pill` ("+$2,000.00")**:
   - `phase: "in"`, `opacity`: 0.0 -> 1.0 (Frames 5–9, `quartInOut`)
   - `phase: "in"`, `scale`: 0.65 -> 1.08 -> 1.0 (Frames 5–15, `softSpring`)
   - `phase: "out"`, `scale`: 1.0 -> 0.85 (Frames End-8 to End, `cubicIn`)
   - `phase: "out"`, `opacity`: 1.0 -> 0.0 (Frames End-8 to End, `cubicIn`)

---

## 4. Fusion Compiler & Canvas View Parity

1. **`core/templates/fusion_compiler.py`**:
   - Ensure layer motion compiler parses all layer tracks for `translate_y`, `scale`, and `opacity` across both `phase == "in"` and `phase == "out"`.
   - Maintain relative offset from `comp.RenderStart` for `in` and `comp.RenderEnd` for `out`.
2. **`ui_qt/widgets/template_canvas_area.py`**:
   - The interactive 60fps scrubbable preview must evaluate each layer's motion tracks at scrub time $t$, rendering the top-drop, stagger, and spring pop with 100% fidelity to Fusion.

---

## 5. Verification Plan

1. **Unit Tests (`tests/test_stripe_benchmark.py`)**:
   - Validate JSON schema compliance of `agency_stripe_notification.json`.
   - Verify every layer (`card_plate`, `app_name`, `msg_title`, `amount_pill`) has non-empty `in` and `out` motion tracks.
   - Verify `amount_pill` has spring easing (`softSpring`) and scale keyframes.
   - Verify out phase keyframes terminate with `opacity == 0.0` and negative `translate_y`.
2. **Full Test Suite Integrity**:
   - All 98 existing tests continue to pass with 0 regressions.
3. **Canvas Grab & Visual Verification**:
   - Capture rendered canvas pixmaps at:
     - $t = 0.0$ (Hidden off-screen top)
     - $t = 0.25$ (Mid-drop with stagger)
     - $t = 0.50$ (Amount pop overshoot)
     - $t = 1.0$ (Resting hold state)
     - $t = 3.7$ (Exit transition)
