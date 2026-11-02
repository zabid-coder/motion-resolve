# Phase 4: Professional Preset Library Rebranding & Multilingual Support Plan

**Goal:** Rebrand the 21 presets to professional, agency-grade neutral names organized by visual language and use case, add native Bengali / multilingual presets, implement automatic Bengali font fallback in `TextPlusBuilder` and `PresetPreviewCanvas`, and polish category filtering.

## Tasks Overview

- [x] **Task 1: Rebrand 21 Style Presets to Agency-Grade Names in `data/styles/*.json` and `core/style_manager.py`**
  - Replace creator names with visual style & use case names (e.g., "Highlight Word Punch", "High Retention Impact", "Editorial Magenta Hook", "Insight Badge Clean", "Documentary Highlight Box", "Editorial Luxury Serif").
  - Organize into standard categories: `Clean Subtitles`, `Bold Social`, `Documentary`, `Brand / Corporate`, `Cinematic`, `Kinetic / Tech`, `Bengali / Multilingual`.

- [x] **Task 2: Add Native Bengali / Multilingual Presets**
  - Create `data/styles/bengali_editorial_sub.json` ("Bangla Editorial Subtitle").
  - Create `data/styles/bengali_speaker_plate.json` ("Bangla Speaker ID Plate").
  - Register in `core/style_manager.py`.

- [x] **Task 3: Automatic Bengali Script & Conjunct Fallback Engine**
  - In `core/text_plus_builder.py:apply_style`: Automatically detect Bengali characters and resolve to `Hind Siliguri` / `Noto Sans Bengali` / `font_bn`.
  - In `ui_qt/tabs/titles_tab.py:PresetPreviewCanvas`: Automatically apply Bengali font in preset preview cards.
  - In `ui_qt/tabs/titles_tab.py`: Update category filter combo with `Clean Subtitles`, `Bold Social`, `Documentary`, `Brand / Corporate`, `Cinematic`, `Kinetic / Tech`, `Bengali / Multilingual`.

- [x] **Task 4: Unit Tests, Verification & Visual Artifacts**
  - Add test in `tests/test_audit.py` to verify all renamed and multilingual presets pass line spacing 0.0, valid typography, and category matching.
  - Run full test suite.
  - Capture updated screenshots of all 4 tabs (`tab1_workspace_v11.png`, `tab2_templates_v9.png`, `tab3_presets_v11.png`, `tab4_auto_v11.png`).
