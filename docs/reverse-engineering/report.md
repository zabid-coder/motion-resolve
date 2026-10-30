# Reverse-Engineering Report: EasyMotion Toolkit to CaptionForge for Resolve

**Author:** Senior DaVinci Resolve Plugin Engineer & Clean-Room Systems Architect  
**Target Application:** EasyMotion Toolkit (beta) by Jamie Fenn  
**Reconstructed System:** CaptionForge for Resolve (Aliased as Motion Resolve)  
**Protocol:** Clean-Room Reconstruction (zero proprietary code reuse, original design system, open JSON presets)

---

## 1. Product Summary
EasyMotion Toolkit is a vertical companion desktop panel for DaVinci Resolve Studio designed to streamline the creation, styling, animation, and batch transcription-to-caption conversion of social media captions (Shorts, Reels, TikTok) and dialogue titles. It interacts directly with the Resolve timeline and Fusion Text+ title generator, enabling creators to position, align, format, and animate captions with procedural physics (bounce, pop, directional slide, shake, flicker) without opening the Fusion page or manually adjusting keyframe curves.

---

## 2. Target User
- **Short-Form Content Creators & Video Editors:** Producing YouTube Shorts, TikToks, and Instagram Reels requiring dynamic animated subtitles.
- **Agency & Commercial Editors:** Requiring consistent subtitle branding, fast transcription conversion, and reusable team styling presets.
- **DaVinci Resolve Users:** Moving away from CapCut, Premiere Pro, or Premiere Auto-Captions to keep their entire workflow native inside DaVinci Resolve Studio.

---

## 3. Core Job-to-be-Done (JTBD)
> *"When I transcribe dialogue or build title hooks in DaVinci Resolve, I want to automatically convert spoken cues into animated, high-retention Text+ captions with custom branding and motion physics, so that I can create professional viral videos in seconds without opening Fusion or setting manual keyframes."*

---

## 4. Screen, Tab & Control Area Inventory

### 4.1 Master Window Frame
- **Vertical Aspect Ratio:** 440×890px vertical companion layout placed adjacent to Resolve's 9:16 or 16:9 viewer.
- **Top Header Bar:**
  - App Logo branding (`captionforge` / `Motion Resolve`).
  - `CC Convert Captions` drawer trigger pill button.
  - Collapse / Minimize for Playback button (`−`/`+`).
  - Utility menu (`···`): Reconnect, Render Cache advice, Undo last batch, About.
- **Navigation Tab Bar:**
  - Three primary tabs: `[ Workspace ]`, `[ Titles ]`, `[ Auto ]`.
- **Bottom Status Bar:**
  - Dynamic status feedback, target caption count, and undo shortcut indicator.

### 4.2 Workspace Tab
- **Sub-Toolbar:**
  - Target Mode selector: `[ Playhead ]` vs `[ In/Out ]`.
  - Layout Template triggers: `[ T1★ ]` (Hero Word), `[ T2 ]` (2-Line), `[ T3 ]` (3-Line).
  - Quick action: `[ + Text ]` (instantly inserts Text+ title at playhead).
  - Batch Undo: `[ ↶ ]`.
- **Convert Captions Drawer (Slide-down modal):**
  - Subtitle track selector with cue count (`Subtitle 1 · X cues`).
  - Style preset picker.
  - Punctuation removal toggle (`Remove punctuation`).
  - Action trigger: `[ Convert · In/Out ]`.
- **Interactive Smartphone Canvas View (9:16):**
  - Neon pink center laser guideline (`#ff2a85`).
  - Interactive bounding box with draggable anchor corner handles.
  - Double-click inline text editing.
  - Alignment strip (`|←` Left, `÷` Center, `→|` Right, `⛶` Fit, `↺` Lower-Third Reset).
  - Floating canvas tool strip: Duplicate, Copy attributes, Crosshair, Scale, Color, Font.
  - Bottom zoom pill control.
- **Motion Effects Controller Panel (Bottom):**
  - **IN Animation:** Slide vs Bounce mode pills; 5-way D-Pad (▲, ◄, ●, ►, ▼).
  - **OUT Animation:** Slide vs Bounce mode pills; 5-way D-Pad (▲, ◄, ●, ►, ▼).
  - **Center 2×2 Effects Grid:** `∿ Shake`, `❐ Jitter`, `〰 Scribble`, `≡⚬ M. Blur`.
  - **Sub-Row Accents:** `Flicker`, `Shake`, `Blur`.
  - **AUTO Continuity Button:** Alternates entrance directions across consecutive timeline clips.

### 4.3 Titles Tab (Style Gallery & Composer)
- **Top Sub-Bar:** `[ Playhead ]` / `[ In/Out ]`, `[ + Add from timeline ]`, `[ Import... ]`.
- **Search & Filter Bar:** Search input field + Category combo box.
- **Presets Grid Area:**
  - 2-column scrollable grid with typography preview cards.
  - Each card shows: Name, Category, Live Typography Preview, Motion Badge (`⚡ bounce_up`), `[ Apply ]` button, and custom delete `[ × ]`.
- **Title Composer & Staging Drawer:**
  - Word staging text input.
  - Layout template triggers: `Template 1★`, `Template 2`, `Template 3`.
  - `2-Color 🎨` dual-accent toggle.
  - `★ Insert Title into Timeline` button with AUTO continuity motion.
  - `Edit in Auto ➔` navigation button.

### 4.4 Auto Tab (Batch Automation Engine)
- **Active Style Card:** Current style preview thumbnail, font metadata, and `[ Change ➔ ]` button.
- **Automation Settings:**
  - `Words per slide` slider (1 to 5 words) with dynamic label.
  - `Remove punctuation` checkbox.
  - `Layouts only (no anim)` checkbox.
  - `Motion Blur` checkbox.
  - `Shake IN` intensity slider (0-100%).
  - `Flicker` frequency slider (0-100%).
- **Timeline Group Plan Preview:**
  - `QTreeWidget` table: Index `#`, Frame Range `Start-End`, and `Caption Words`.
  - `[ ↻ Refresh Timeline ]` button to re-scan subtitle tracks.
  - Word shifting buttons: `[ ◄ Shift Left ]` and `[ Shift Right ► ]`.
- **Action Buttons:**
  - `[ Update Playhead Caption ]`: Updates title currently under playhead.
  - `[ ★ CREATE CAPTIONS ]`: Batch creates all titles on dedicated video track with undo snapshot.

---

## 5. Feature Inventory & Reverse-Engineering Analysis

| Feature | Observed Behavior | Inferred Implementation | Priority | Clean-Room Status |
|---|---|---|---|---|
| **Resolve Connection** | Opens inside/beside Resolve seamlessly | `DaVinciResolveScript` IPC via Python `scriptapp('Resolve')` | P0 | Verified & Live |
| **Playhead Targeting** | Edits title directly under playhead | `timeline.GetCurrentTimecode()`, query video tracks for overlapping clip | P0 | Implemented |
| **In/Out Targeting** | Batch edits all titles within In/Out marks | Parse `timeline.GetMarkInOut()`, filter clips inside frame range | P0 | Implemented |
| **Text+ Creation** | Inserts native Text+ title into timeline | `timeline.SetMarkInOut(s, e)`, `timeline.InsertFusionTitleIntoTimeline("Text+")` | P0 | Implemented |
| **Typography Styling** | Modifies Font, Style, Size, Spacing, Colors | Fusion tool `tool.SetInput("StyledText", ...)`, `Font`, `Style`, `Size`, `Red1`, `Green1`, `Blue1` | P0 | Implemented |
| **Stroke & Shading** | Adds black outlines or highlights | Fusion Shading elements: Element 2 (Stroke), Element 4 (Shadow), Element 5 (Box) | P0 | Implemented |
| **Damped Oscillator Bounce** | Dynamic bouncy spring entrance | Procedural keyframing using $S(t) = 1.0 - e^{-\zeta \omega t} \cos(\omega_d t)$ on `Center` or `Size` | P0 | Implemented |
| **Directional Slide** | Smooth slide from screen edges | Keyframing `Center` input with cubic ease-out curve | P0 | Implemented |
| **Continuous Shake** | Organic camera/text shake across clip | Keyframed high-frequency Perlin/harmonic oscillation on `Center` | P1 | Implemented |
| **AUTO Continuity** | Consecutive titles alternate bounce directions | State machine cycling through `[up, right, down, left]` stored across timeline insertions | P1 | Implemented |
| **Batch Subtitle Conversion** | Reads timeline subtitle track and builds titles | `timeline.GetItemListInTrack("subtitle", 1)`, chunk by word count with character-proportional frames | P0 | Implemented |
| **Word Shifting** | Move words between adjacent caption slides | Interactive plan array manipulation updating `from_cue.words` and `to_cue.words` before generation | P1 | Implemented |
| **Preset Save & Load** | Saves current styling as reusable presets | Inspect Fusion inputs, serialize to human-readable JSON files in `data/styles/` | P0 | Implemented |
| **Snapshot Undo** | Single-click reversal of batch operations | Save track & clip references in `ResolveBridge._undo_stack`, delete created items on undo | P0 | Implemented |
| **Mini Playback Mode** | Collapses panel into 50px floating bar | Toggle visibility of tabs, stack, and status bar, lock window height to 50px | P1 | Implemented |

---

## 6. Business Rules & Logic
1. **Scope Priority:**
   - In `Playhead` mode, only the topmost Text+ clip intersecting the current playhead frame is modified.
   - In `In/Out` mode, all Text+ clips on active video tracks overlapping `[mark_in, mark_out]` are batch modified.
2. **Timing Proportions:**
   - When splitting a subtitle cue into $N$ slides, each slide's duration is weighted by character count:
     $$D_i = \max\left(4, \text{round}\left(D_{\text{total}} \cdot \frac{\text{len}(W_i)}{\sum \text{len}(W)}\right)\right)$$
   - The final slide is clamped to the original subtitle's end frame to prevent desync.
3. **Safety & Non-Destruction:**
   - Batch caption creation always appends a new video track (`timeline.AddTrack("video")`) to never overwrite existing footage or B-roll.
   - Batch operations push an operation snapshot to the undo journal before executing.

---

## 7. Better-Version Architectural Opportunities
1. **Cross-Platform Path Resolution:** Automatic detection of macOS (`~/Library/Application Support/...`) and Windows (`%APPDATA%\\Blackmagic Design\\...`) scripting paths.
2. **Open JSON Presets:** Standard JSON format allows editors to easily backup, share, or edit presets in any text editor.
3. **True PyQt6 High-DPI Canvas:** Native QPainter canvas with sub-pixel rendering, corner drag handles, and smooth resizing compared to Resolve's static UIManager widgets.
4. **Resilient Error Recovery:** Automatic fallback between DaVinci Resolve Studio API and standalone preview mode when Resolve is not running.
