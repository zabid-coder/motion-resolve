# Motion Resolve — Full Upgrade Implementation Plan (Options 1, 2, 3, 4)

> **Goal**: Transform Motion Resolve into an industry-leading, studio-grade motion graphics and captioning suite with ultra-premium presets, smart contraction-preserving captions, 1-word viral rapid punch, Whisper word-timing import, staggered Fusion template animations, and platform-specific social safe zones.

---

## Proposed Changes

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Captions Core (SubtitleParser & AutoTab)                 │
│    - Contraction preservation: don't, it's, can't preserved │
│    - Capitalization selector: ALL CAPS / Title / Sentence   │
│    - 1-Word & 2-Word Rapid Viral Punch mode                 │
│    - Word-level Whisper JSON timestamp parser               │
├─────────────────────────────────────────────────────────────┤
│ 2. Studio Presets & Typography Catalog (data/styles/)       │
│    - 8 curated ultra-premium presets (Syne, Montserrat,     │
│      Inter, Playfair, Hind Siliguri, Anek Bangla)           │
│    - Layered soft ambient drop shadows & glass plates       │
│    - True 2-color hero word contrast across all styles      │
├─────────────────────────────────────────────────────────────┤
│ 3. Staggered Fusion Template Engine (FusionCompiler)        │
│    - Per-layer stagger timing (plate -> headline -> subline)│
│    - Split-seam masked reveal animation                     │
│    - Dynamic bounding box plate sizing                      │
│    - 2 new kinetic templates: kin_split_reveal, word_pop    │
├─────────────────────────────────────────────────────────────┤
│ 4. Interactive UX & Safe Zones (CanvasView & WorkspaceTab)  │
│    - TikTok, Instagram Reels, YouTube Shorts UI safe zones  │
│    - Motion scrub & live playhead preview in canvas         │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Tasks

### Task 1: Smart Punctuation, Contraction Preservation & Capitalization

**Files to modify:**
- `core/subtitle_parser.py`
- `ui_qt/tabs/auto_tab.py`
- `tests/test_subtitle_parser.py`

**Steps:**
1. Update `SubtitleParser.clean_punctuation()`:
   - Preserve internal apostrophes (e.g. `don't`, `it's`, `can't`, `we're`).
   - Strip only leading/trailing punctuation (`.!?,:;"()[]{}`).
2. Add `SubtitleParser.format_case(text, case_mode)`:
   - `"upper"`: `text.upper()`
   - `"title"`: `text.title()`
   - `"sentence"`: capitalize first letter of sentence.
3. In `ui_qt/tabs/auto_tab.py`:
   - Add `combo_case` (ALL CAPS, Title Case, Sentence Case, As-Is).
   - In `_rebuild_plan()`, format cue text through `format_case()`.
4. Unit tests in `tests/test_subtitle_parser.py`:
   - Verify `clean_punctuation("Don't stop, it's amazing!")` $\to$ `"Don't stop it's amazing"`.
   - Verify case formatting across English & Bengali.

---

### Task 2: 1-Word & 2-Word Rapid Viral Punch Mode + Whisper JSON Import

**Files to modify:**
- `core/subtitle_parser.py`
- `ui_qt/tabs/auto_tab.py`
- `tests/test_subtitle_parser.py`

**Steps:**
1. In `SubtitleParser.chunk_cues()`:
   - When `words_per_slide == 1`: each word becomes its own cue with seamless frame continuity (`start_frame` of next is `end_frame` of previous).
   - Add min-duration protection (minimum 3-4 frames so text is readable).
2. Add `SubtitleParser.parse_whisper_json(filepath, fps=30.0)`:
   - Parses word-level timestamps (`[{"word": "Hello", "start": 0.0, "end": 0.3}, ...]`).
   - Converts to frame-accurate `SubtitleCue` list.
3. In `ui_qt/tabs/auto_tab.py`:
   - Extend `slider_wps` minimum to 1, updating label to `"1 word (Rapid Punch)"`.
   - Add `Import Whisper JSON...` option to file dialog.
4. Unit test word-level parsing and 1-word punch mode.

---

### Task 3: 8 Ultra-Premium Studio Typography Presets

**Files to modify / create:**
- `data/styles/cyber_punk_mint.json`
- `data/styles/editorial_silk_serif.json`
- `data/styles/tech_mono_hud.json`
- `data/styles/retention_impact_yellow.json`
- `data/styles/doc_lower_third_slate.json`
- `data/styles/creator_bold_stack.json`
- `data/styles/bengali_pro_doc.json`
- `data/styles/bengali_viral_vlogger.json`
- `core/style_manager.py`
- `tests/test_audit.py`

**Design Specifications:**
1. **Cyber Punk Mint**: Syne / Montserrat ExtraBold, color: `#FFFFFF`, accent: `#00FF9D`, box: `#0B0A12` (75% opacity), stroke: 0.022.
2. **Editorial Silk Serif**: Playfair Display, color: `#FAF6F0`, accent: `#D97736`, subtle soft shadow (softness 0.035).
3. **Tech Monospace HUD**: JetBrains Mono, color: `#E6F7FF`, accent: `#00D2FF`, border box plate with cyan edge.
4. **Retention Impact Yellow**: Anton / Montserrat Black, color: `#FFFFFF`, accent: `#FFE600`, layered soft shadow.
5. **Doc Lower Third Slate**: Inter Tight SemiBold, charcoal backdrop plate, clean white text, terracotta pill.
6. **Creator Bold Stack**: Bebas Neue / Impact, gold accent `#FFB800`, optical 2-line layout.
7. **Bangla Pro Documentary**: Hind Siliguri SemiBold, white text, ruby accent plate `#C8102E`, soft shadow.
8. **Bangla Viral Vlogger**: Hind Siliguri Bold, yellow punch `#FFEA00`, stroke 0.028, bounce in.

---

### Task 4: Staggered Fusion Template Animations & Split Seam Reveal

**Files to modify:**
- `core/templates/fusion_compiler.py`
- `data/templates/kinetic/kin_split_reveal.json`
- `data/templates/kinetic/kin_word_explosion.json`
- `tests/test_templates.py`

**Steps:**
1. In `core/templates/fusion_compiler.py`:
   - Implement `_compile_layer_motion(comp, tool, layer_spec, stagger_delay, fps)`:
     - Background plate moves at $t = 0.00\text{s}$.
     - Primary headline moves at $t = 0.06\text{s}$.
     - Subline / secondary text moves at $t = 0.14\text{s}$.
   - Add `MatteControl` split mask support (top line reveals upwards from seam, bottom line reveals downwards).
2. Author 2 new kinetic template JSON specifications:
   - `kin_split_reveal.json`: Razor-sharp split seam reveal.
   - `kin_word_explosion.json`: Kinetic pop with expanding border box.
3. Unit test staggered timing evaluation and compilation.

---

### Task 5: Platform-Specific Social Safe Zones & Canvas Motion Preview

**Files to modify:**
- `ui_qt/widgets/canvas_view.py`
- `ui_qt/tabs/workspace_tab.py`
- `tests/test_ui.py`

**Steps:**
1. In `ui_qt/widgets/canvas_view.py`:
   - Add Safe Zone selector pills: `[TikTok]`, `[Reels]`, `[Shorts]`, `[Broadcast]`.
   - Render exact UI overlays in `paintEvent` (engagement rail, caption danger zone, sound bar).
2. Add animation scrub bar in Canvas View:
   - Play/Pause toggle with spacebar.
   - Animates the caption preview inside the canvas area matching Resolve's timeline curve.
3. Unit test safe zone switching and canvas paint.

---

## Verification Plan

### Automated Tests
- Run full unit test discovery: `python3 -m unittest discover tests`
- Assert all 42+ existing tests pass.
- Assert new tests for contraction preservation, Whisper JSON, staggered timing, and presets pass.

### Live DaVinci Resolve Studio Verification
- Verify DaVinci Resolve connection with active timeline.
- Test 1-word rapid punch batch creation on video track.
- Verify staggered animation playback in Fusion node graph.
- Verify 2-Color hero accent with new presets.
- Capture updated screenshot artifacts for all 4 tabs.
