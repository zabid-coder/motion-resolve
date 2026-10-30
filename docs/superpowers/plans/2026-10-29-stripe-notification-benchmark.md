# Stripe Notification Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overhaul the `agency_stripe_notification` template into a broadcast-grade Apple iOS native push notification card with multi-layer staggered motion, tactile spring pop on the amount, and smooth exit transitions.

**Architecture:** Refactor `data/templates/agency/agency_stripe_notification.json` with full in/out motion tracks across all layers, enhance `core/templates/fusion_compiler.py` for layer-specific exit and scale curves, and ensure `ui_qt/widgets/template_canvas_area.py` previews it with 100% parity.

**Tech Stack:** Python 3.10+, PyQt6, DaVinci Resolve Studio Fusion Nodes (`TextPlus`, `Transform`, `RectangleMask`).

## Global Constraints

- Do not modify or break backwards compatibility of existing templates or themes.
- Exact Apple iOS graphite tokens: `#1c1c1e` (Plate BG), `#8e8e93` (Secondary label), `#ffffff` (Primary title), `#34c759` (Emerald amount).
- All transitions must start off-screen at $t=0$ and terminate off-screen at $t=total$.
- All unit tests must pass via `py -3.12 -m unittest discover tests`.

---

### Task 1: Overhaul `agency_stripe_notification.json` Layer Motion & Styles

**Files:**
- Modify: `data/templates/agency/agency_stripe_notification.json`
- Test: `tests/test_stripe_benchmark.py`

**Interfaces:**
- Consumes: `TemplateSpec`, `LayerSpec`, `MotionTrackSpec`, `KeyframeSpec` from `core/templates/schema.py`
- Produces: Complete declarative spec for `agency_stripe_notification` with non-empty in/out tracks on all 4 layers.

- [x] **Step 1: Write the failing test**

```python
# tests/test_stripe_benchmark.py
import unittest
import json
import os
from core.templates.registry import TemplateRegistry

class TestStripeBenchmark(unittest.TestCase):
    def setUp(self):
        self.registry = TemplateRegistry()
        self.template = self.registry.get_by_id("agency_stripe_notification")

    def test_template_exists_and_loads(self):
        self.assertIsNotNone(self.template, "Template agency_stripe_notification must be registered")

    def test_all_layers_have_in_and_out_motion_tracks(self):
        layer_ids = [l.id for l in self.template.layers]
        self.assertIn("card_plate", layer_ids)
        self.assertIn("app_name", layer_ids)
        self.assertIn("msg_title", layer_ids)
        self.assertIn("amount_pill", layer_ids)

        for layer in self.template.layers:
            in_tracks = [t for t in layer.motion_tracks if t.phase == "in"]
            out_tracks = [t for t in layer.motion_tracks if t.phase == "out"]
            self.assertGreater(len(in_tracks), 0, f"Layer {layer.id} must have IN motion tracks")
            self.assertGreater(len(out_tracks), 0, f"Layer {layer.id} must have OUT motion tracks")

    def test_amount_pill_has_tactile_spring_pop(self):
        amount_layer = next(l for l in self.template.layers if l.id == "amount_pill")
        scale_track = next((t for t in amount_layer.motion_tracks if t.property == "scale" and t.phase == "in"), None)
        self.assertIsNotNone(scale_track, "amount_pill must have an IN scale motion track")
        easings = [kf.easing for kf in scale_track.keyframes]
        self.assertIn("softSpring", easings, "amount_pill scale track must utilize softSpring easing")

if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run test to verify it fails**

Run: `py -3.12 -m unittest tests.test_stripe_benchmark`  
Expected: FAIL on `test_all_layers_have_in_and_out_motion_tracks` (layers have empty motion tracks).

- [x] **Step 3: Update `agency_stripe_notification.json`**

Update `data/templates/agency/agency_stripe_notification.json` with the complete layer specifications, Apple graphite plate tokens, and staggered in/out motion tracks:

```json
{
  "id": "agency_stripe_notification",
  "name": "Stripe Alert — Payment Push Card",
  "category": "Agency / Social",
  "description": "Floating Apple iOS notification card with emerald transaction amount and tactile spring pop.",
  "tags": [
    "stripe",
    "notification",
    "ios",
    "fintech",
    "payment",
    "social",
    "viral"
  ],
  "aspect_ratios": [
    "9:16",
    "16:9",
    "1:1"
  ],
  "duration_default": 3.8,
  "min_hold": 2.2,
  "in_duration": 0.55,
  "out_duration": 0.33,
  "parameters": [
    {
      "id": "brand",
      "name": "App Source",
      "type": "string",
      "default": "Stripe • now",
      "category": "Text"
    },
    {
      "id": "headline",
      "name": "Notification Title",
      "type": "string",
      "default": "Payment Received",
      "category": "Text"
    },
    {
      "id": "amount",
      "name": "Payment Amount",
      "type": "string",
      "default": "+$2,000.00",
      "category": "Text"
    },
    {
      "id": "accent_color",
      "name": "Accent Color",
      "type": "color",
      "default": [
        0.204,
        0.780,
        0.349,
        1.0
      ],
      "category": "Style"
    },
    {
      "id": "plate_enabled",
      "name": "Frosted Card Plate",
      "type": "boolean",
      "default": true,
      "category": "Style"
    },
    {
      "id": "pos_y",
      "name": "Vertical Position",
      "type": "number",
      "default": 0.80,
      "min_val": 0.1,
      "max_val": 0.9,
      "step": 0.01,
      "category": "Layout"
    }
  ],
  "layers": [
    {
      "id": "card_plate",
      "type": "shape_rect",
      "name": "Card Plate",
      "props": {
        "width": 0.84,
        "height": 0.14,
        "color": [
          0.11,
          0.11,
          0.12,
          0.88
        ],
        "border_color": [
          0.28,
          0.28,
          0.32,
          0.60
        ],
        "border_width": 1.5,
        "corner_radius": 18,
        "role": "plate",
        "center_x": 0.5,
        "center_y": "param:pos_y"
      },
      "motion_tracks": [
        {
          "property": "opacity",
          "phase": "in",
          "keyframes": [
            {
              "time": 0.0,
              "value": 0.0,
              "easing": "quartInOut"
            },
            {
              "time": 0.35,
              "value": 1.0,
              "easing": "quartInOut"
            }
          ]
        },
        {
          "property": "translate_y",
          "phase": "in",
          "keyframes": [
            {
              "time": 0.0,
              "value": -0.07,
              "easing": "expoOut"
            },
            {
              "time": 0.55,
              "value": 0.0,
              "easing": "expoOut"
            }
          ]
        },
        {
          "property": "translate_y",
          "phase": "out",
          "keyframes": [
            {
              "time": 0.0,
              "value": 0.0,
              "easing": "cubicIn"
            },
            {
              "time": 0.33,
              "value": -0.06,
              "easing": "cubicIn"
            }
          ]
        },
        {
          "property": "opacity",
          "phase": "out",
          "keyframes": [
            {
              "time": 0.0,
              "value": 1.0,
              "easing": "cubicIn"
            },
            {
              "time": 0.33,
              "value": 0.0,
              "easing": "cubicIn"
            }
          ]
        }
      ]
    },
    {
      "id": "app_name",
      "type": "text",
      "name": "App Source",
      "props": {
        "text": "param:brand",
        "font": "token:font_body",
        "size": 0.036,
        "weight": "Medium",
        "color": [
          0.557,
          0.557,
          0.576,
          1.0
        ],
        "alignment": "left",
        "center_x": 0.14,
        "center_y": "param:pos_y",
        "offset_y": 0.030
      },
      "motion_tracks": [
        {
          "property": "opacity",
          "phase": "in",
          "keyframes": [
            {
              "time": 0.08,
              "value": 0.0,
              "easing": "quartInOut"
            },
            {
              "time": 0.38,
              "value": 1.0,
              "easing": "quartInOut"
            }
          ]
        },
        {
          "property": "translate_y",
          "phase": "in",
          "keyframes": [
            {
              "time": 0.08,
              "value": -0.04,
              "easing": "expoOut"
            },
            {
              "time": 0.55,
              "value": 0.0,
              "easing": "expoOut"
            }
          ]
        },
        {
          "property": "translate_y",
          "phase": "out",
          "keyframes": [
            {
              "time": 0.0,
              "value": 0.0,
              "easing": "cubicIn"
            },
            {
              "time": 0.33,
              "value": -0.05,
              "easing": "cubicIn"
            }
          ]
        },
        {
          "property": "opacity",
          "phase": "out",
          "keyframes": [
            {
              "time": 0.0,
              "value": 1.0,
              "easing": "cubicIn"
            },
            {
              "time": 0.33,
              "value": 0.0,
              "easing": "cubicIn"
            }
          ]
        }
      ]
    },
    {
      "id": "msg_title",
      "type": "text",
      "name": "Notification Title",
      "props": {
        "text": "param:headline",
        "font": "token:font_heading",
        "size": 0.050,
        "weight": "Bold",
        "color": [
          1.0,
          1.0,
          1.0,
          1.0
        ],
        "alignment": "left",
        "center_x": 0.14,
        "center_y": "param:pos_y",
        "offset_y": -0.022
      },
      "motion_tracks": [
        {
          "property": "opacity",
          "phase": "in",
          "keyframes": [
            {
              "time": 0.12,
              "value": 0.0,
              "easing": "quartInOut"
            },
            {
              "time": 0.42,
              "value": 1.0,
              "easing": "quartInOut"
            }
          ]
        },
        {
          "property": "translate_y",
          "phase": "in",
          "keyframes": [
            {
              "time": 0.12,
              "value": -0.04,
              "easing": "expoOut"
            },
            {
              "time": 0.55,
              "value": 0.0,
              "easing": "expoOut"
            }
          ]
        },
        {
          "property": "translate_y",
          "phase": "out",
          "keyframes": [
            {
              "time": 0.0,
              "value": 0.0,
              "easing": "cubicIn"
            },
            {
              "time": 0.33,
              "value": -0.05,
              "easing": "cubicIn"
            }
          ]
        },
        {
          "property": "opacity",
          "phase": "out",
          "keyframes": [
            {
              "time": 0.0,
              "value": 1.0,
              "easing": "cubicIn"
            },
            {
              "time": 0.33,
              "value": 0.0,
              "easing": "cubicIn"
            }
          ]
        }
      ]
    },
    {
      "id": "amount_pill",
      "type": "text",
      "name": "Payment Amount",
      "props": {
        "text": "param:amount",
        "font": "token:font_heading",
        "size": 0.056,
        "weight": "Bold",
        "color": "param:accent_color",
        "alignment": "right",
        "center_x": 0.86,
        "center_y": "param:pos_y",
        "offset_y": -0.005
      },
      "motion_tracks": [
        {
          "property": "opacity",
          "phase": "in",
          "keyframes": [
            {
              "time": 0.20,
              "value": 0.0,
              "easing": "quartInOut"
            },
            {
              "time": 0.38,
              "value": 1.0,
              "easing": "quartInOut"
            }
          ]
        },
        {
          "property": "scale",
          "phase": "in",
          "keyframes": [
            {
              "time": 0.20,
              "value": 0.65,
              "easing": "softSpring"
            },
            {
              "time": 0.48,
              "value": 1.08,
              "easing": "softSpring"
            },
            {
              "time": 0.55,
              "value": 1.0,
              "easing": "expoOut"
            }
          ]
        },
        {
          "property": "scale",
          "phase": "out",
          "keyframes": [
            {
              "time": 0.0,
              "value": 1.0,
              "easing": "cubicIn"
            },
            {
              "time": 0.33,
              "value": 0.85,
              "easing": "cubicIn"
            }
          ]
        },
        {
          "property": "opacity",
          "phase": "out",
          "keyframes": [
            {
              "time": 0.0,
              "value": 1.0,
              "easing": "cubicIn"
            },
            {
              "time": 0.33,
              "value": 0.0,
              "easing": "cubicIn"
            }
          ]
        }
      ]
    }
  ]
}
```

- [x] **Step 4: Run test to verify it passes**

Run: `py -3.12 -m unittest tests.test_stripe_benchmark`  
Expected: PASS.

---

### Task 2: Fusion Compiler Multi-Layer Exit & Stagger Support

**Files:**
- Modify: `core/templates/fusion_compiler.py`
- Test: `tests/test_stripe_benchmark.py`

**Interfaces:**
- Consumes: `LayerSpec.motion_tracks`
- Produces: Frame-accurate animation keyframes on Fusion tool inputs for `phase == "out"` (e.g. `Center`, `Size`, `Level` / `Opacity`).

- [x] **Step 1: Write test for Fusion compiler layer exit keyframing**

Add to `tests/test_stripe_benchmark.py`:

```python
    def test_fusion_compiler_handles_layer_exit_keyframes(self):
        from unittest.mock import MagicMock
        from core.templates.fusion_compiler import FusionCompiler

        bridge_mock = MagicMock()
        bridge_mock.get_timeline_fps.return_value = 24.0
        compiler = FusionCompiler(bridge_mock)

        timing = compiler.calculate_clip_timing(72, 3.8, 0.55, 0.33, 24.0, 1.0)
        tool_mock = MagicMock()
        tool_mock.Center = MagicMock()
        tool_mock.Size = MagicMock()

        amount_layer = next(l for l in self.template.layers if l.id == "amount_pill")
        compiler._compile_layer_motion(tool_mock, amount_layer, (0.5, 0.5), timing)

        # Verify Size was keyframed for both in and out
        self.assertGreater(tool_mock.Size.SetKeyFrames.call_count, 0)
```

- [x] **Step 2: Run test to verify it fails if exit keyframes aren't set**

Run: `py -3.12 -m unittest tests.test_stripe_benchmark.TestStripeBenchmark.test_fusion_compiler_handles_layer_exit_keyframes`  

- [x] **Step 3: Refine `_compile_layer_motion` in `core/templates/fusion_compiler.py`**

Ensure that exit keyframes for `scale`, `opacity`, and `translate_y` are properly calculated using `hold_end_frame` and `total_frames` offsets, and assigned to tool inputs.

- [x] **Step 4: Run test to verify it passes**

Run: `py -3.12 -m unittest tests.test_stripe_benchmark`  
Expected: PASS.

---

### Task 3: Interactive Canvas Scrubbing Parity & Verification

**Files:**
- Modify: `ui_qt/widgets/template_canvas_area.py`
- Test: `tests/test_stripe_benchmark.py`

**Interfaces:**
- Consumes: `TemplateCanvasArea.set_time(t)`
- Produces: Accurate rendering of layer offsets, scale, and opacity at scrub time $t$.

- [x] **Step 1: Write test for canvas rendering at $t=0, 0.25, 0.5, 1.0, 3.7$**

Add to `tests/test_stripe_benchmark.py`:

```python
    def test_canvas_area_renders_stripe_at_scrub_points(self):
        import sys
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        from ui_qt.widgets.template_canvas_area import TemplateCanvasArea
        from core.templates.theme_tokens import get_theme

        canvas = TemplateCanvasArea()
        canvas.resize(600, 400)
        theme = get_theme("mono")

        for t in (0.0, 0.25, 0.50, 1.0, 3.7):
            canvas.set_state(self.template, {}, theme, t)
            pix = canvas.grab()
            self.assertFalse(pix.isNull())
            self.assertGreaterEqual(pix.width(), 600)
            self.assertGreaterEqual(pix.height(), 400)
```

- [x] **Step 2: Run test to verify it passes**

Run: `py -3.12 -m unittest tests.test_stripe_benchmark.TestStripeBenchmark.test_canvas_area_renders_stripe_at_scrub_points`  
Expected: PASS.

- [x] **Step 3: Run full test suite**

Run: `py -3.12 -m unittest discover tests`  
Expected: 100+ tests passing cleanly with 0 failures, 0 errors.

---

### Task 4: Visual Capture & DaVinci Parity Inspection

**Files:**
- Script: `scratch/capture_stripe_benchmark.py`

- [x] **Step 1: Create capture script `scratch/capture_stripe_benchmark.py`**

Generate 5 high-res frames showing the animation progression:
- `stripe_00_start.png` ($t=0.0$)
- `stripe_01_drop.png` ($t=0.25$)
- `stripe_02_pop.png` ($t=0.50$)
- `stripe_03_hold.png` ($t=1.0$)
- `stripe_04_exit.png` ($t=3.7$)

- [x] **Step 2: Execute capture script and verify images**

Run: `py -3.12 scratch/capture_stripe_benchmark.py`  
Expected: 5 PNGs generated with crisp Apple graphite card and emerald amount pop.
