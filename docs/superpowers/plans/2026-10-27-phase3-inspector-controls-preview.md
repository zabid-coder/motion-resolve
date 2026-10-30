# Phase 3: Template Inspector Controls & Studio-Grade Previews Plan

**Goal:** Elevate the Template Inspector to support full parameter schemas (Color Picker, Font Picker, Select Dropdowns), compile declarative motion tracks accurately in `FusionCompiler`, render true Text+ painter previews on Preset Cards, and provide full template/preset export and import.

## Tasks Overview

- [x] **Task 1: Add Color, Font, and Select Parameter Controls to Template Inspector (`ui_qt/tabs/templates_tab.py`)**
  - Implement `ParameterType.COLOR`: Color swatch button with `QColorDialog` picker and hex feedback.
  - Implement `ParameterType.FONT`: Styled font selector populated with macOS & OFL bundle fonts.
  - Implement `ParameterType.SELECT`: `QComboBox` populated with parameter's enum options.
  - Test parameter change updates preview canvas and template compiler bindings.

- [x] **Task 2: High-Fidelity Motion Track Compiler in `core/templates/fusion_compiler.py`**
  - Replace simplified heuristic with per-track interpolation from `m.keyframes` across in, hold, and out phases.
  - Support `translate_x`, `translate_y`, `scale_x`, `scale_y`, `opacity`, `write_on`, and `width`/`height`.
  - Interpolate frames using the specified `EasingToken` (`expoOut`, `quartInOut`, `cubicIn`, `softSpring`, `linear`).

- [x] **Task 3: Studio-Grade Preset Card Painter Preview (`ui_qt/tabs/titles_tab.py`)**
  - Replace approximate `QLabel` CSS box with custom `PresetPreviewWidget` using `QPainter` and `QPainterPath`.
  - Render actual character-level stroke outlines (`stroke_thickness`, `stroke_color`).
  - Render ambient drop shadows with offset and softness (`shadow_offset`, `shadow_color`).
  - Render background plates with corner rounding (`box_round`, `box_color`, `box_extend_x`, `box_extend_y`).
  - Apply accurate character tracking (`character_spacing`).

- [x] **Task 4: Template and Preset Export / Import Dialogs**
  - In `titles_tab.py`: Add "Export..." action to export any selected preset to JSON.
  - In `templates_tab.py`: Add "Export JSON" and "Import JSON" for sharing declarative template specs.

- [x] **Task 5: Unit Tests, Live Verification & Visual Artifacts**
  - Add tests in `tests/test_templates.py` and `tests/test_audit.py`.
  - Run full test suite.
  - Capture updated screenshots of all 4 tabs (`tab1_workspace_v10.png`, `tab2_templates_v8.png`, `tab3_presets_v10.png`, `tab4_auto_v10.png`).
