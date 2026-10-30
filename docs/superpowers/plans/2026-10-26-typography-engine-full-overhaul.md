# Typography Template Engine Full Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the complete studio-grade Typography Template Engine for DaVinci Resolve: full 42-template catalog across 8 categories, multi-layer Fusion compiler with real node hierarchy and shape lines, and a live 60fps scrubbable preview player in the UI.

**Architecture:** 
1. `core/templates/fusion_compiler.py`: Multi-layer Fusion pipeline generator merging separate TextPlus and Background/Rectangle shape tools into a master Transform with baked keyframe easing (entrance, hold, exit).
2. `data/templates/<category>/*.json`: Declarative template specifications defining layers, parameters, themes, and motion tracks for 42 templates.
3. `ui_qt/widgets/template_preview_canvas.py`: Scrubbable 60fps HTML/QPainter canvas with play/pause, timecode display, and real-time easing evaluation.
4. `ui_qt/tabs/templates_tab.py`: Split layout with category filtering, template gallery, live animated preview, dynamic inspector, and one-click Resolve generation.

**Tech Stack:** Python 3.14, PyQt6, DaVinci Resolve Studio 21.1 Fusion Scripting API, JSON Schema.

## Global Constraints
- High-performance PyQt6 desktop architecture with dark cyber aesthetic (`#0c0916`, `#151124`, `#ff5500`).
- Line spacing strictly 1.0 (`LineSpacingClone: 0.0` in Fusion Text+).
- Clean-room implementation (no proprietary binaries or trademarked names).
- Frame-rate independent animation authored in seconds and mapped to project FPS.
- Easing tokens: `expoOut`, `quartInOut`, `cubicIn`, `softSpring`, `linear`.

---

### Task 1: Multi-Layer Fusion Compiler Upgrade

**Files:**
- Modify: `core/templates/fusion_compiler.py`
- Test: `tests/test_templates.py`

**Interfaces:**
- Consumes: `TemplateSpec`, `ThemeTokens`, `ResolveBridge`
- Produces: `FusionCompiler.compile_and_apply(timeline_item, template, param_overrides, theme_id, speed, intensity)` producing multi-node Fusion compositions (`TextPlus`, `Background`, `Rectangle`, `Merge`, `Transform`, `MediaOut1`).

- [ ] **Step 1: Write failing test in `tests/test_templates.py` for multi-layer Fusion generation**
- [ ] **Step 2: Upgrade `FusionCompiler` to support multiple text layers with distinct fonts/sizes/colors**
- [ ] **Step 3: Implement shape line (`shape_line`) and rectangle/pill (`shape_rect`, `shape_pill`) generation via Background + Rectangle mask**
- [ ] **Step 4: Chain multi-layer tools using sequential Fusion `Merge` nodes leading into master `MR_Transform`**
- [ ] **Step 5: Implement complete In, Hold, and Out keyframing on `MR_Transform`**
- [ ] **Step 6: Run tests and verify all pass**

---

### Task 2: Build Complete 42-Template Catalog

**Files:**
- Create: `data/templates/podcast/*.json` (8 templates)
- Create: `data/templates/saas/*.json` (10 templates)
- Create: `data/templates/minimal/*.json` (6 templates)
- Create: `data/templates/editorial/*.json` (6 templates)
- Create: `data/templates/social/*.json` (7 templates)
- Create: `data/templates/documentary/*.json` (2 templates)
- Create: `data/templates/cinematic/*.json` (2 templates)
- Create: `data/templates/kinetic/*.json` (2 templates)
- Modify: `core/templates/registry.py`
- Test: `tests/test_templates.py`

**Interfaces:**
- Consumes: `TemplateRegistry.load_all()`
- Produces: 42 verified `TemplateSpec` objects with valid layers, parameters, and motion tracks.

- [ ] **Step 1: Author remaining 7 Podcast templates**
- [ ] **Step 2: Author remaining 9 SaaS/Tech templates**
- [ ] **Step 3: Author remaining 5 Minimal Clean templates**
- [ ] **Step 4: Author remaining 5 Editorial/Magazine templates**
- [ ] **Step 5: Author remaining 6 Social/Reels 9:16 templates**
- [ ] **Step 6: Author remaining Documentary, Cinematic, and Kinetic templates**
- [ ] **Step 7: Update `tests/test_templates.py` to assert catalog size >= 40 templates**
- [ ] **Step 8: Run tests and verify all 42 load cleanly without schema errors**

---

### Task 3: Live Scrubbable 60fps Animation Preview Player

**Files:**
- Create: `ui_qt/widgets/template_preview_canvas.py`
- Modify: `ui_qt/tabs/templates_tab.py`
- Test: `tests/test_ui.py`

**Interfaces:**
- Consumes: `TemplateSpec`, `ThemeTokens`, `active_params`
- Produces: `TemplatePreviewCanvasWidget` with time scrubber, play/pause controls, live 60fps rendering of multi-layer text and shapes.

- [ ] **Step 1: Create `TemplatePreviewCanvasWidget` with QTimer 60fps loop and QPainter layer rendering**
- [ ] **Step 2: Add time scrubber (QSlider), Play/Pause button, and timecode label**
- [ ] **Step 3: Evaluate motion tracks per layer at scrubbed time `t` (translate, scale, opacity)**
- [ ] **Step 4: Integrate `TemplatePreviewCanvasWidget` into `TemplatesTab` above the inspector**
- [ ] **Step 5: Connect parameter changes in inspector to live update the preview canvas**
- [ ] **Step 6: Run tests and verify smooth playback**

---

### Task 4: End-to-End Verification & Desktop Process Refresh

**Files:**
- Modify: `tests/test_templates.py`, `tests/test_ui.py`
- Artifacts: Recapture UI tabs (`tab1_workspace_v6.png`, `tab2_templates_v4.png`, `tab3_presets_v6.png`, `tab4_auto_v6.png`)

- [ ] **Step 1: Run full unit test suite (`python3 -m unittest discover tests`)**
- [ ] **Step 2: Verify live DaVinci Resolve Studio timeline with multi-layer template application**
- [ ] **Step 3: Capture high-resolution visual screenshots of all 4 tabs**
- [ ] **Step 4: Restart background desktop process and confirm zero errors**
