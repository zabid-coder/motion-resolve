# Masked Reveal Motion Engine & Premium Typography Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Overhaul the motion engine and typography styling across Motion Resolve to implement true Matte / Masked Reveal and Masked Hide (clipping text so it starts 100% hidden, slides into view through an invisible clipping boundary, and tucks back into hiding on exit), while upgrading all 21 style presets and 46 declarative templates to world-class, premium studio typography.

**Architecture:** 
1. In `core/animation_engine.py`, inject a `RectangleMask` node (`MR_Mask`) into the Fusion pipeline connected directly to `MR_Transform.EffectMask`. Animate `MR_Transform.Center` with micro-displacements ($0.04-0.06$ normalized height) starting outside the mask boundary, using an `expoOut` curve for entrance and `cubicIn` for exit so text is 100% invisible at frame 0 and frame end.
2. In `core/templates/fusion_compiler.py`, generate per-layer or group reveal masks (`MR_RevealMask`) with staggered entry ($t_0$ accent hairline, $t_0+3$f headline, $t_0+6$f subtitle).
3. In `ui_qt/widgets/template_preview_canvas.py`, apply `QPainter.setClipRect()` matching the Fusion mask bounds during entrance and exit for 1:1 preview parity.
4. Elevate all 21 style presets and 46 templates with modern typography tokens (Geist, Inter, JetBrains Mono, SF Pro, Instrument Serif), wide tracking for uppercase tags, tight display tracking, frosted glassmorphism plates, glowing keyword pills, and single line spacing 1.0 (`LineSpacingClone = 0.0`).

**Tech Stack:** Python 3.14, PyQt6, DaVinci Resolve Studio 21.1 Fusion Scripting API, JSON Schema specs.

## Global Constraints

- Keep PyQt6 high-performance Python desktop architecture.
- All line spacing must strictly remain 1.0 (`LineSpacingClone: 0.0` in Fusion).
- Text must NEVER fly visibly across the full screen from screen edges; motion must be a disciplined mask reveal ($\le 40$px displacement).
- Exit must be a clean reverse slide into mask hiding or smooth opacity fade.
- 100% unit test pass rate across `tests/`.

---

### Task 1: Fusion Pipeline Masked Reveal & Masked Hide in AnimationEngine

**Files:**
- Modify: `core/animation_engine.py:35-185`
- Test: `tests/test_core.py`

**Interfaces:**
- Consumes: `timeline_item.GetFusionCompByIndex(1)`, `comp.AddTool("RectangleMask")`, `mr_trans.EffectMask.ConnectTo(mr_mask.Mask)`
- Produces: `MR_Mask` tool in pipeline, `MR_Transform` Center expressions with micro-displacement clamped behind `MR_Mask` bounds.

- [x] **Step 1: Write test for Masked Reveal pipeline structure**

```python
def test_masked_reveal_pipeline(self):
    from core.animation_engine import AnimationEngine
    engine = AnimationEngine()
    self.assertEqual(engine.MASK_NODE_NAME, "MR_Mask")
```

- [x] **Step 2: Run test to verify failure**

Run: `python3 -m unittest tests/test_core.py`
Expected: FAIL (AttributeError: 'AnimationEngine' object has no attribute 'MASK_NODE_NAME')

- [x] **Step 3: Implement MR_Mask in AnimationEngine pipeline**

In `core/animation_engine.py`:
1. Define `MASK_NODE_NAME = "MR_Mask"`.
2. In `get_or_create_pipeline(comp)`:
   - Create `MR_Mask` as a `RectangleMask` tool.
   - Set `mr_mask.Center = [0.5, 0.5]` (or text center).
   - Set `mr_mask.Width = 0.95` and `mr_mask.Height = 0.14`.
   - Connect `mr_trans.EffectMask.ConnectTo(mr_mask.Mask)`.
3. In `apply_motion_preset`:
   - Replace the large `0.30` fly-in displacement with a disciplined mask reveal offset ($0.055 \times \text{distance}$).
   - Set entrance expression: Text starts at $-0.055$ (below mask bottom boundary) at `time == comp.RenderStart` and reveals into $0.0$ via `expoOut` curve.
   - Set exit expression: At `time >= comp.RenderEnd - dur`, text slides down to $-0.055$ (into mask hiding) via `cubicIn` curve.
   - For `slide_left` / `slide_right`: displace along $X$-axis ($-0.12 \times \text{distance}$) behind vertical mask boundary.

- [x] **Step 4: Run test to verify pass**

Run: `python3 -m unittest tests/test_core.py`
Expected: PASS

---

### Task 2: Mask Reveal & Exit in Template Fusion Compiler

**Files:**
- Modify: `core/templates/fusion_compiler.py:115-285`
- Test: `tests/test_templates.py`

**Interfaces:**
- Consumes: `comp.AddTool("RectangleMask")`, `layer.motion_tracks`
- Produces: `MR_RevealMask` connected to `MR_Transform.EffectMask` or `TextPlus.EffectMask` with keyframed reveal.

- [x] **Step 1: Write test for Template Compiler Mask Reveal**

In `tests/test_templates.py`:
Verify `fusion_compiler.py` creates and attaches `MR_RevealMask` to clip text elements.

- [x] **Step 2: Implement Mask Reveal in FusionCompiler**

In `core/templates/fusion_compiler.py`:
1. Add `MR_RevealMask` creation in `compile_and_apply`.
2. Anchor `MR_RevealMask.Center = [0.5, pos_y]`, `Width = 0.95`, `Height = 0.22`.
3. Connect `mr_trans.EffectMask.ConnectTo(reveal_mask.Mask)`.
4. Update `_apply_motion_tracks`:
   - Entrance: `translate_y` from $-28$px to $0$px using `expoOut`. Outside the mask, text is clipped to 0 opacity.
   - Exit: `translate_y` from $0$px to $-28$px using `cubicIn` or clean opacity fade.

- [x] **Step 3: Run test to verify pass**

Run: `python3 -m unittest tests/test_templates.py`
Expected: PASS

---

### Task 3: QPainter Mask Clipping in Template Preview Canvas

**Files:**
- Modify: `ui_qt/widgets/template_preview_canvas.py:90-205`
- Test: `tests/test_ui.py`

**Interfaces:**
- Consumes: `painter.setClipRect(clip_box)`
- Produces: 1:1 visual parity in preview canvas where text reveals from hidden and tucks into mask on exit.

- [x] **Step 1: Implement setClipRect in TemplateCanvasArea.paintEvent**

In `ui_qt/widgets/template_preview_canvas.py`:
1. Compute `mask_rect = QRectF(center_x - w * 0.48, center_y - 48, w * 0.96, 96)`.
2. During entrance ($t < t_{\text{in}}$):
   - `dy = (1.0 - ease_in) * 36.0` (starts 36px below resting line).
   - Set `painter.setClipRect(mask_rect)`.
   - Text is drawn with offset `dy`, so everything below `mask_rect` is invisible.
3. During hold:
   - Full opacity, `dy = 0`.
4. During exit ($t > t_{\text{hold\_end}}$):
   - `dy = ease_out * 36.0`.
   - Set `painter.setClipRect(mask_rect)`.
   - Text slides down through mask boundary into complete invisibility.

- [x] **Step 2: Run tests to verify UI stability**

Run: `python3 -m unittest tests/test_ui.py`
Expected: PASS

---

### Task 4: Premium Typography & Aesthetic Overhaul for All 21 Presets

**Files:**
- Modify: `core/style_manager.py:20-220`
- Modify: `data/styles/*.json` (21 files)
- Test: `tests/test_audit.py`

**Interfaces:**
- Consumes: Modern typography tokens, tracking, shadow, stroke, box paddings
- Produces: 21 studio-grade preset specifications with world-class aesthetics.

- [x] **Step 1: Define Premium Typography Standards**

1. **Modern SaaS & Tech (Linear / Vercel style)**:
   - Fonts: Inter, Helvetica Neue, JetBrains Mono.
   - Subtle 1px translucent stroke, frosted dark glass plate, accent cyan/orange badge.
2. **Editorial & Documentary (Vox / Netflix / NYT style)**:
   - Fonts: Playfair Display, Instrument Serif, Georgia, Noto Serif Bengali.
   - Elegant split-weight contrast, signature Vox yellow highlight box (`#FFE500`), thin hairline divider rules.
3. **Pop Culture & Kinetic Video Essay (Ali Abdaal / Hormozi / MrBeast)**:
   - Fonts: Impact, Montserrat ExtraBold, Komika Axis.
   - Refined 3px stroke with soft ambient drop shadow ($0.006, -0.006$), mint green/vibrant yellow high-retention highlights.
4. **All Presets**:
   - Strictly single line spacing 1.0 (`line_spacing: 0.0`).
   - Standardized `animation_in` and `animation_out` with mask reveals.

- [x] **Step 2: Update all 21 preset JSON files with new specs**

Execute python batch upgrade script on `data/styles/*.json` and `core/style_manager.py`.

- [x] **Step 3: Run audit tests to verify integrity**

Run: `python3 -m unittest tests/test_audit.py`
Expected: PASS (All 21 presets validated with line spacing 0.0)

---

### Task 5: Live Verification & Visual Artifacts

**Files:**
- Run: `Motion Resolve.py`
- Verify in DaVinci Resolve Studio 21.1 live timeline.
- Capture screenshots of updated Workspace Tab, Templates Tab, Presets Tab, and Auto Tab into artifact directory.

- [x] **Step 1: Execute headless test render to capture updated UI**
- [x] **Step 2: Verify in DaVinci Resolve Studio with real timeline title item**
- [x] **Step 3: Run full unittest suite across all test modules**
