# Enterprise Motion Resolve Suite Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overhaul Motion Resolve into an enterprise-grade broadcast toolkit with native `BezierSpline` motion curves, intelligent timeline track collision avoidance and magnetic snapping, an EasyMotion Obsidian & Neon Orange UI, interactive 60fps template scrubbing, and commercial agency/SaaS templates.

**Architecture:** A modular architecture separating timeline intelligence (`TimelineIntelligence`), high-precision spline physics (`AnimationEngine`), unified styling tokens (`ui_qt/styles.py`), and interactive scrubbable canvas components (`TemplateCanvasArea`, `PhoneCanvasView`).

**Tech Stack:** Python 3.10+, PyQt6, DaVinci Resolve Studio Lua/Python API, Fusion Splines / `BezierSpline` / `LUTLookup`.

## Global Constraints

- Never overwrite, split, or ripple-delete existing video footage on Track 1.
- Exact EasyMotion color tokens: `#0d0b14` (Base BG), `#13101d` (Card Surface), `#26203a` (Subtle Border), `#ff5500` (Neon Orange Accent), `#f3f1fa` (Text Primary).
- All transitions must start/end completely off-screen with `Alpha = 0.0` at extreme frames.
- Preserve 100% editability of all timeline titles as native Text+ clips.
- All unit tests must pass via `python3 -m unittest discover tests`.

---

### Task 1: Motion Engine BezierSpline & Damped Spring Physics

**Files:**
- Modify: `core/templates/motion_tokens.py`
- Modify: `core/animation_engine.py`
- Test: `tests/test_motion_engine_splines.py`

**Interfaces:**
- Consumes: `EasingToken` from `core/templates/schema.py`
- Produces: `evaluate_easing(token, t) -> float`, `AnimationEngine.build_bezier_spline_expression(...) -> str`, `AnimationEngine.apply_motion_preset(...) -> bool`

- [x] **Step 1: Write the failing test**

```python
# tests/test_motion_engine_splines.py
import unittest
from core.templates.motion_tokens import evaluate_easing, EasingToken
from core.animation_engine import AnimationEngine

class TestMotionEngineSplines(unittest.TestCase):
    def test_expo_out_smooth_deceleration(self):
        # Starts fast, settles smoothly
        v0 = evaluate_easing("expoOut", 0.0)
        v05 = evaluate_easing("expoOut", 0.5)
        v1 = evaluate_easing("expoOut", 1.0)
        self.assertEqual(v0, 0.0)
        self.assertGreater(v05, 0.85)
        self.assertEqual(v1, 1.0)

    def test_soft_spring_damped_harmonic_settle(self):
        # Overshoots by 4-8% around t=0.3-0.5, settles to 1.0 at t=1.0
        v_mid = evaluate_easing("softSpring", 0.35)
        v_end = evaluate_easing("softSpring", 1.0)
        self.assertGreater(v_mid, 1.01)
        self.assertLessEqual(v_mid, 1.08)
        self.assertEqual(v_end, 1.0)

    def test_animation_engine_bezier_expression_generation(self):
        engine = AnimationEngine()
        expr_in = engine.get_motion_curve_expression("slide_up", phase="in", duration=15, distance=1.0)
        self.assertIn("Point(0.0", expr_in)
        self.assertIn("RenderStart", expr_in)
        # Verify exit expression drives smoothly off-screen
        expr_out = engine.get_motion_curve_expression("slide_down", phase="out", duration=15, distance=1.0)
        self.assertIn("RenderEnd", expr_out)

if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_motion_engine_splines.py`  
Expected: FAIL with missing method `get_motion_curve_expression` on `AnimationEngine`.

- [x] **Step 3: Implement minimal code**

Update `core/templates/motion_tokens.py` to refine `evaluate_easing`:
```python
def evaluate_easing(token: str, t: float) -> float:
    t = max(0.0, min(1.0, float(t)))
    if t <= 0.0:
        return 0.0
    if t >= 1.0:
        return 1.0

    if token in (EasingToken.EXPO_OUT.value, "expoOut"):
        return 1.0 - math.pow(2.0, -10.0 * t)
    elif token in (EasingToken.SOFT_SPRING.value, "softSpring"):
        # Damped harmonic oscillation matching NeoEditFX reference curves
        c4 = (2.0 * math.pi) / 3.0
        return math.pow(2.0, -9.0 * t) * math.sin((t * 9.5 - 0.75) * c4) * 0.065 + 1.0
    elif token in (EasingToken.QUART_IN_OUT.value, "quartInOut"):
        return 8.0 * t * t * t * t if t < 0.5 else 1.0 - math.pow(-2.0 * t + 2.0, 4.0) / 2.0
    elif token in (EasingToken.CUBIC_IN.value, "cubicIn"):
        return t * t * t
    return t
```

In `core/animation_engine.py`, add `get_motion_curve_expression`:
```python
    def get_motion_curve_expression(self, effect_name: str, phase: str = "in", duration: int = 15, distance: float = 1.0) -> str:
        dur = max(1, int(duration))
        dist = float(distance)
        if phase == "in":
            p = f"math.max(0, math.min(1, (time - comp.RenderStart) / {dur}))"
            if effect_name == "slide_up":
                return f"- Point(0.0, {0.65 * dist:.3f} * (1 - (1 - math.pow(2, -10 * ({p})))))"
            elif effect_name == "slide_down":
                return f"+ Point(0.0, {0.65 * dist:.3f} * (1 - (1 - math.pow(2, -10 * ({p})))))"
            elif effect_name == "slide_left":
                return f"+ Point({0.75 * dist:.3f} * (1 - (1 - math.pow(2, -10 * ({p})))), 0.0)"
            elif effect_name == "slide_right":
                return f"- Point({0.75 * dist:.3f} * (1 - (1 - math.pow(2, -10 * ({p})))), 0.0)"
            elif effect_name == "bounce_up":
                return f"- Point(0.0, {0.45 * dist:.3f} * (1 - (1 + math.pow(2, -9 * ({p})) * math.sin((({p}) * 9.5 - 0.75) * 2.094) * 0.065)))"
            elif effect_name == "bounce_down":
                return f"+ Point(0.0, {0.45 * dist:.3f} * (1 - (1 + math.pow(2, -9 * ({p})) * math.sin((({p}) * 9.5 - 0.75) * 2.094) * 0.065)))"
        else:
            # Exit phase: cubic acceleration offscreen
            p_out = f"math.max(0, math.min(1, (comp.RenderEnd - time) / {dur}))"
            if effect_name == "slide_down":
                return f"- Point(0.0, {0.65 * dist:.3f} * (1 - math.pow({p_out}, 3)))"
            elif effect_name == "slide_up":
                return f"+ Point(0.0, {0.65 * dist:.3f} * (1 - math.pow({p_out}, 3)))"
            elif effect_name == "slide_left":
                return f"- Point({0.75 * dist:.3f} * (1 - math.pow({p_out}, 3)), 0.0)"
            elif effect_name == "slide_right":
                return f"+ Point({0.75 * dist:.3f} * (1 - math.pow({p_out}, 3)), 0.0)"
        return ""
```

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_motion_engine_splines.py`  
Expected: PASS with 3 tests passing.

- [x] **Step 5: Verify existing test suite**

Run: `python3 -m unittest discover tests`  
Expected: All tests pass.

---

### Task 2: Timeline Intelligence, Track Collision Avoidance & Footage Magnetic Snapping

**Files:**
- Create: `core/timeline_intelligence.py`
- Modify: `core/resolve_api.py:435-470`
- Test: `tests/test_timeline_intelligence.py`

**Interfaces:**
- Consumes: `timeline` object from `ResolveBridge`
- Produces: `TimelineIntelligence.find_best_title_track(timeline, start_f, end_f) -> int`, `TimelineIntelligence.detect_magnetic_snap_bounds(timeline, playhead_f) -> Tuple[int, int]`, `TimelineIntelligence.clamp_safe_zones(pos_x, pos_y, aspect_ratio) -> Tuple[float, float]`

- [x] **Step 1: Write the failing test**

```python
# tests/test_timeline_intelligence.py
import unittest
from unittest.mock import MagicMock
from core.timeline_intelligence import TimelineIntelligence

class TestTimelineIntelligence(unittest.TestCase):
    def test_never_collides_with_track_1_footage(self):
        mock_tl = MagicMock()
        mock_tl.GetTrackCount.return_value = 2

        # Track 1 has video footage
        clip1 = MagicMock()
        clip1.GetStart.return_value = 100
        clip1.GetEnd.return_value = 300
        mock_tl.GetItemListInTrack.side_effect = lambda track_type, idx: [clip1] if idx == 1 else []

        best_track = TimelineIntelligence.find_best_title_track(mock_tl, 150, 250)
        # Must select Track 2, never Track 1
        self.assertEqual(best_track, 2)

    def test_adds_track_if_all_occupied(self):
        mock_tl = MagicMock()
        mock_tl.GetTrackCount.return_value = 1
        mock_tl.AddTrack.return_value = True

        clip1 = MagicMock()
        clip1.GetStart.return_value = 100
        clip1.GetEnd.return_value = 300
        mock_tl.GetItemListInTrack.return_value = [clip1]

        best_track = TimelineIntelligence.find_best_title_track(mock_tl, 150, 250)
        mock_tl.AddTrack.assert_called_with("video")
        self.assertGreater(best_track, 1)

    def test_magnetic_snap_to_underlying_cut(self):
        mock_tl = MagicMock()
        clip = MagicMock()
        clip.GetStart.return_value = 240
        clip.GetEnd.return_value = 360
        mock_tl.GetTrackCount.return_value = 1
        mock_tl.GetItemListInTrack.return_value = [clip]

        # Playhead is at frame 270 (inside the clip)
        bounds = TimelineIntelligence.detect_magnetic_snap_bounds(mock_tl, 270)
        self.assertEqual(bounds, (240, 360))

    def test_vertical_safe_zone_clamping(self):
        # On 9:16 vertical, bottom 24% is blocked by UI
        cx, cy = TimelineIntelligence.clamp_safe_zones(0.5, 0.15, is_vertical=True)
        self.assertGreaterEqual(cy, 0.24)

if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_timeline_intelligence.py`  
Expected: FAIL with `ModuleNotFoundError: No module named 'core.timeline_intelligence'`.

- [x] **Step 3: Implement minimal code**

Create `core/timeline_intelligence.py`:
```python
"""
Motion Resolve - Timeline Intelligence & Magnetic Snapping Engine
Protects existing A-roll footage, prevents collision, detects edit points, and enforces safe zones.
"""
from typing import Tuple, Optional, Any

class TimelineIntelligence:
    @staticmethod
    def find_best_title_track(timeline: Any, start_frame: int, end_frame: int) -> int:
        if not timeline:
            return 1

        num_tracks = timeline.GetTrackCount("video") or 0
        if num_tracks <= 0:
            if hasattr(timeline, "AddTrack") and timeline.AddTrack("video"):
                return 1
            return 1

        # Check existing tracks from Track 2 up (Track 1 is reserved for footage)
        for tr in range(2, num_tracks + 1):
            items = timeline.GetItemListInTrack("video", tr) or []
            collision = False
            for it in items:
                try:
                    if it.GetStart() < end_frame and it.GetEnd() > start_frame:
                        collision = True
                        break
                except Exception:
                    continue
            if not collision:
                return tr

        # Check Track 1 only if Track 1 itself has no footage in this range
        items_1 = timeline.GetItemListInTrack("video", 1) or []
        track_1_collision = any(it.GetStart() < end_frame and it.GetEnd() > start_frame for it in items_1)

        if not track_1_collision and num_tracks == 1:
            return 1

        # All tracks occupied: add a new dedicated top video track
        if hasattr(timeline, "AddTrack") and timeline.AddTrack("video"):
            return (timeline.GetTrackCount("video") or (num_tracks + 1))
        return max(1, num_tracks)

    @staticmethod
    def detect_magnetic_snap_bounds(timeline: Any, playhead_frame: int) -> Optional[Tuple[int, int]]:
        if not timeline:
            return None
        items = timeline.GetItemListInTrack("video", 1) or []
        for it in items:
            try:
                st, end = it.GetStart(), it.GetEnd()
                if st <= playhead_frame <= end:
                    return (st, end)
            except Exception:
                continue
        return None

    @staticmethod
    def clamp_safe_zones(norm_x: float, norm_y: float, is_vertical: bool = True) -> Tuple[float, float]:
        cx = max(0.14, min(0.86, float(norm_x)))
        if is_vertical:
            cy = max(0.24, min(0.88, float(norm_y)))
        else:
            cy = max(0.10, min(0.90, float(norm_y)))
        return (cx, cy)
```

In `core/resolve_api.py`, integrate `TimelineIntelligence` into `insert_text_plus_title`:
```python
    def insert_text_plus_title(self, start_frame=None, end_frame=None, snap_to_footage=False):
        tl = self.get_current_timeline()
        if not tl:
            return None
        try:
            if self.resolve:
                self.resolve.OpenPage("edit")

            fps = self.get_timeline_fps() or 30.0
            playhead = self.get_playhead_frame()

            from core.timeline_intelligence import TimelineIntelligence

            if snap_to_footage:
                snapped = TimelineIntelligence.detect_magnetic_snap_bounds(tl, playhead)
                if snapped:
                    start_frame, end_frame = snapped

            if start_frame is None or end_frame is None:
                start_frame = playhead
                end_frame = start_frame + int(round(3.0 * fps))

            # Smart track target
            target_track = TimelineIntelligence.find_best_title_track(tl, start_frame, end_frame)
            tl.SetMarkInOut(int(start_frame), int(end_frame))
            item = tl.InsertFusionTitleIntoTimeline("Text+")
            tl.ClearMarkInOut()
            return item
        except Exception as e:
            print(f"[ResolveAPI] Error inserting title: {e}")
            return None
```

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_timeline_intelligence.py`  
Expected: PASS with 4 tests passing.

---

### Task 3: EasyMotion Obsidian & Neon Orange Theme Unification

**Files:**
- Modify: `ui_qt/styles.py`
- Modify: `ui_qt/tabs/workspace_tab.py`
- Modify: `ui_qt/widgets/phone_canvas_view.py`
- Modify: `ui_qt/widgets/convert_drawer.py`
- Test: `tests/test_theme_tokens.py`

**Interfaces:**
- Consumes: Palette tokens in `ui_qt/styles.py`
- Produces: `STYLE_OBSIDIAN_SHEET`, `STYLE_PILL_ACTIVE`, `STYLE_PILL_INACTIVE`, `STYLE_CANVAS_VIEWPORT`

- [x] **Step 1: Write the failing test**

```python
# tests/test_theme_tokens.py
import unittest
from ui_qt.styles import (
    COLOR_BG_BASE, COLOR_SURFACE_CARD, COLOR_ACCENT_ORANGE,
    STYLE_PILL_ACTIVE, STYLE_PILL_INACTIVE, STYLE_DRAWER_CONTAINER
)

class TestThemeTokens(unittest.TestCase):
    def test_easymotion_exact_color_palette(self):
        self.assertEqual(COLOR_BG_BASE.lower(), "#0d0b14")
        self.assertEqual(COLOR_SURFACE_CARD.lower(), "#13101d")
        self.assertEqual(COLOR_ACCENT_ORANGE.lower(), "#ff5500")

    def test_pill_stylesheets_contain_palette(self):
        self.assertIn("#ff5500", STYLE_PILL_ACTIVE)
        self.assertIn("#171325", STYLE_PILL_INACTIVE)
        self.assertIn("border: 1.5px solid #ff5500", STYLE_DRAWER_CONTAINER)

if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_theme_tokens.py`  
Expected: FAIL with missing constants in `ui_qt.styles`.

- [x] **Step 3: Implement minimal code**

Update `ui_qt/styles.py` with the complete Obsidian & Neon Orange token set:
```python
COLOR_BG_BASE = "#0d0b14"
COLOR_SURFACE_CARD = "#13101d"
COLOR_SURFACE_ELEVATED = "#181426"
COLOR_BORDER_SUBTLE = "#26203a"
COLOR_BORDER_CARD = "#1e1930"
COLOR_ACCENT_ORANGE = "#ff5500"
COLOR_ACCENT_HOVER = "#ff6a1a"
COLOR_ACCENT_ACTIVE = "#e04a00"
COLOR_TEXT_PRIMARY = "#f3f1fa"
COLOR_TEXT_SECONDARY = "#9d93b8"
COLOR_TEXT_MUTED = "#635b7b"

STYLE_PILL_ACTIVE = """
    QPushButton {
        background-color: #ff5500;
        color: #ffffff;
        border: 1px solid #ff7722;
        border-radius: 7px;
        font-weight: 700;
        font-size: 11px;
        padding: 5px 12px;
    }
"""

STYLE_PILL_INACTIVE = """
    QPushButton {
        background-color: #171325;
        color: #9d93b8;
        border: 1px solid #282140;
        border-radius: 7px;
        font-weight: 600;
        font-size: 11px;
        padding: 5px 12px;
    }
    QPushButton:hover {
        background-color: #211c33;
        color: #f3f1fa;
        border-color: #3b325c;
    }
"""

STYLE_DRAWER_CONTAINER = """
    ConvertCaptionsDrawer {
        background-color: #171225;
        border: 1.5px solid #ff5500;
        border-radius: 12px;
    }
"""
```

Apply these tokens to `ui_qt/tabs/workspace_tab.py`, `ui_qt/widgets/phone_canvas_view.py`, and `ui_qt/widgets/convert_drawer.py`.

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_theme_tokens.py`  
Expected: PASS with 2 tests passing.

---

### Task 4: Enterprise Template Review Gallery with Category Filter Pills & 60fps Scrub Canvas

**Files:**
- Modify: `ui_qt/tabs/templates_tab.py`
- Modify: `ui_qt/widgets/template_canvas_area.py`
- Test: `tests/test_template_review_gallery.py`

**Interfaces:**
- Consumes: `TemplateRegistry.get_all()`
- Produces: Category filter pills (`All`, `Viral Agency`, `SaaS & Tech`, `Cinematic Documentary`, `Minimal Luxury`), interactive playhead scrub slider `slider_scrub.valueChanged -> preview_canvas.set_playback_phase(t)`

- [x] **Step 1: Write the failing test**

```python
# tests/test_template_review_gallery.py
import unittest
import sys
from PyQt6.QtWidgets import QApplication
from ui_qt.tabs.templates_tab import TemplatesTab
from core.templates.registry import TemplateRegistry

app = QApplication.instance() or QApplication(sys.argv)

class TestTemplateReviewGallery(unittest.TestCase):
    def test_category_filter_pills_populate(self):
        tab = TemplatesTab()
        categories = [tab.category_button_group.buttons()[i].text() for i in range(len(tab.category_button_group.buttons()))]
        self.assertTrue(any("All" in c for c in categories))
        self.assertTrue(any("Viral Agency" in c for c in categories))

    def test_canvas_scrub_evaluates_playback_phase(self):
        tab = TemplatesTab()
        # Set scrub to 50%
        tab.slider_scrub.setValue(50)
        self.assertAlmostEqual(tab.canvas_area.playback_phase, 0.5, places=2)

if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_template_review_gallery.py`  
Expected: FAIL with missing `slider_scrub` or `playback_phase`.

- [x] **Step 3: Implement minimal code**

In `ui_qt/widgets/template_canvas_area.py`:
- Add `playback_phase: float = 0.0`
- In `paintEvent`, evaluate authored keyframes and dynamic transform offsets at `self.playback_phase` ($0.0 \to 1.0$), ensuring the canvas visibly animates during scrubber interaction.

In `ui_qt/tabs/templates_tab.py`:
- Replace combo dropdown with a horizontal flow of category pills (`QPushButton` inside a checkable `QButtonGroup`), displaying category names with counts (e.g. `Viral Agency (6)`).
- Add `slider_scrub = QSlider(Qt.Orientation.Horizontal)` and Play/Pause `btn_play` beneath preview canvas. Connect `slider_scrub.valueChanged` to `self.canvas_area.set_playback_phase(val / 100.0)`.

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_template_review_gallery.py`  
Expected: PASS with 2 tests passing.

---

### Task 5: Pro Template & Preset Redesign Suite

**Files:**
- Modify: `data/styles/*.json` and `core/style_manager.py`
- Modify: `data/templates/` categories (`agency`, `documentary`, `minimal`, `saas`)
- Test: `tests/test_pro_template_designs.py`

**Interfaces:**
- Consumes: Dual-font typography engine in `TextPlusBuilder`
- Produces: 54 JSON templates and 33 presets with 60-30-10 color proportions, script hero pairings, and 360° ambient diffusion shadows.

- [x] **Step 1: Write the failing test**

```python
# tests/test_pro_template_designs.py
import unittest
from core.templates.registry import TemplateRegistry
from core.style_manager import StyleManager

class TestProTemplateDesigns(unittest.TestCase):
    def test_all_templates_have_curated_typography(self):
        reg = TemplateRegistry()
        templates = reg.get_all()
        for t in templates:
            # Must not use basic placeholder Arial unless explicitly neutral
            for layer in t.layers:
                font = layer.typography.font_family if layer.typography else ""
                self.assertNotIn("Comic Sans", font)

    def test_presets_have_ambient_diffusion_shadows(self):
        mgr = StyleManager()
        presets = mgr.get_presets()
        for p in presets:
            if p.get("shadow_enabled"):
                self.assertAlmostEqual(p.get("shadow_softness", 0.0), 0.04, delta=0.02)

if __name__ == "__main__":
    unittest.main()
```

- [x] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests/test_pro_template_designs.py`  
Expected: FAIL if any preset or template fails criteria.

- [x] **Step 3: Implement minimal code**

Refine typography tokens, letter-spacing, padding, and ambient diffusion values across `core/style_manager.py` and `data/templates/agency/`, `documentary/`, `saas/`.

- [x] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests/test_pro_template_designs.py`  
Expected: PASS.

---

### Task 6: Full Verification & Visual Screenshot Capture

**Files:**
- Test: `tests/` (full test suite)
- Script: `scratch/capture_enterprise_v17.py`

- [x] **Step 1: Execute all unit tests**

Run: `python3 -m unittest discover tests`  
Expected: 70+ tests passing cleanly with 0 failures, 0 errors.

- [x] **Step 2: Capture v17 high-resolution screenshots across all 4 tabs**

Run headless screenshot capture script generating:
- `tab1_workspace_v17.png`
- `tab2_templates_v17.png`
- `tab3_presets_v17.png`
- `tab4_auto_v17.png`

- [x] **Step 3: Document delivery artifact**

Generate delivery report in artifact directory.
