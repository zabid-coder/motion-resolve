# Product Requirements Document (PRD)
## CaptionForge for Resolve (Motion Resolve)
**Version:** 2.0.0  
**Status:** Implemented & Verified  
**Target Environment:** macOS & Windows, DaVinci Resolve Studio 18 / 19 / 21+

---

## 1. Product Vision
To empower video creators and post-production editors with the most seamless, responsive, and visually intuitive animated subtitle and title creation engine directly inside DaVinci Resolve Studio. CaptionForge eliminates tedious Fusion keyframing and manual subtitle splitting, providing viral social typography, physics-based bounce animations, and batch timeline conversion in seconds.

---

## 2. Problem Statement
Editing social media captions inside DaVinci Resolve currently suffers from severe friction:
1. **Manual Subtitle Splitting:** Built-in DaVinci Resolve subtitles cannot be styled individually per word or animated with bounce/pop physics without turning them into individual Text+ clips.
2. **Complex Fusion Keyframing:** Creating high-retention bounce, pop, or shake animations on Text+ titles requires opening the Fusion page, adding transform nodes, and tweaking spline curves for every single phrase.
3. **Third-Party App Dependency:** Editors are frequently forced to export timelines to CapCut or Premiere Pro solely for animated captions, breaking color grading and timeline management.
4. **Lack of Word-Level Staging:** Traditional subtitle tools do not allow editors to shift words between slides or highlight hero words in real time.

---

## 3. Personas

### 3.1 Alex — Solo Short-Form Content Creator
- **Workflow:** Edits 3-5 YouTube Shorts and TikToks per day.
- **Pain Point:** Spends 45 minutes per video manually creating Text+ titles and adding keyframes.
- **Need:** One-click conversion from Resolve transcription to 2-word animated bounce captions with Hormozi or MrBeast styling.

### 3.2 Elena — Commercial Post-Production Editor
- **Workflow:** Edits client brand campaigns and corporate video interviews.
- **Pain Point:** Inconsistent subtitle branding across editors and clients.
- **Need:** Reusable, shareable JSON style presets with clean modern typography, custom brand colors, and non-destructive timeline generation.

---

## 4. MVP Scope & Parity Matrix

### In-Scope (Completed & Production Ready)
- [x] Cross-platform DaVinci Resolve Studio connection via `DaVinciResolveScript` with resilient reconnect.
- [x] Canonical PyQt6 implementation (`ui_qt/`) with 4-tab architecture: Workspace, Templates, Presets, Auto Captions.
- [x] Dual target scope: `Playhead` (single clip) and `In/Out` (batch range).
- [x] Native Text+ clip insertion and real-time Fusion tool manipulation.
- [x] Comprehensive typography controls: Font family, style, size, tracking, line spacing (normalized 1.00 = normal), fill color, outline stroke, drop shadow, and highlight box.
- [x] Interactive 9:16 smartphone preview canvas with laser center guide, TikTok/Reels Safe Zone overlay, and corner draggable handles with real-time viewport zoom/pan.
- [x] Dual 5-way D-Pads for directional Slide & Bounce animations.
- [x] Center 2×2 physics effects grid: Shake, Jitter, Scribble, Motion Blur.
- [x] Sub-row accents: Flicker (intensity-scaled), Shake, Blur.
- [x] AUTO continuity mode: Alternates motion directions across successive clips while preserving preset authored animations.
- [x] 48 Declarative Motion Graphic Templates across 8 categories (Podcast, SaaS, Minimal, Editorial, Social, Documentary, Cinematic, Kinetic) with dynamic reveal masks and short-clip exit timing clamping.
- [x] 33 Curated Typography Presets with Hero Word chip staging, 2-Color accent splitting, and Add From Timeline extraction (preserving fonts, styles, size multipliers, stroke, and shadow).
- [x] Subtitle parser: Timeline subtitle extraction, frame-rate accurate SRT import, cumulative character boundary clamping.
- [x] Interactive word shifting: Move words left or right between adjacent caption slides without boundary drift.
- [x] One-click `Convert Captions` drawer with subtitle track selection, style picker, punctuation removal, and In/Out filtering.
- [x] Resilient user storage: Loads built-in presets from `data/styles/` with fallback to `~/.motion_resolve/styles/` if repo is read-only.
- [x] Truthful redo and modify snapshots: `can_redo()` correctly reports capability based on operation type.
- [x] Floating Mini-Playback Bar toggle (`−`/`+`) for unobstructed playback.

### Post-MVP Scope
- Multi-track simultaneous batch conversion.
- Live audio waveform overlay in the preview canvas.
- Custom Bézier curve editor for personalized bounce damping.
- Cloud preset synchronization for team workspaces.
- Cloud preset synchronization for team workspaces.

### Explicit Non-Goals
- Proprietary Fusion macro encryption or DRM paywalls.
- Black-box rendered video overlays (captions must remain 100% native Text+).
- Requiring an external web connection or cloud account.

---

## 5. User Stories & Acceptance Criteria

### US-1: Automated Subtitle Conversion
**As an** editor with a transcribed subtitle track,  
**I want** to convert all subtitle cues into animated Text+ titles on a new track,  
**So that** my captions are dynamic and fully editable.  
- *Acceptance Criteria:*
  - Cues are extracted accurately from the selected subtitle track.
  - Subtitle phrases are chunked by the specified words-per-slide value (1 to 5).
  - Timing is character-weighted to match natural speech cadences.
  - Punctuation is stripped cleanly if the toggle is enabled.
  - A new video track is created so existing timeline video is untouched.

### US-2: Interactive Word Shifting
**As an** editor reviewing the caption plan,  
**I want** to shift words between adjacent slides before generating,  
**So that** line breaks and comic timing match the speaker's emphasis.  
- *Acceptance Criteria:*
  - Clicking `◄ Shift Left` transfers the first word of the selected slide to the previous slide.
  - Clicking `Shift Right ►` transfers the last word to the next slide.
  - Preview tree updates instantly.

### US-3: Reversible Timeline Operations
**As an** editor testing different motion styles,  
**I want** to immediately undo a batch caption generation,  
**So that** I don't clutter my timeline or lose prior work.  
- *Acceptance Criteria:*
  - Every batch operation records an undo snapshot with timeline clip UUIDs.
  - Clicking `Undo` or `⌘Z` deletes all generated clips and cleans up the track.

---

## 6. Non-Functional Requirements

| Metric | Target | Verification Method |
|---|---|---|
| **Launch Time** | < 1.0 second | Measured from Resolve script menu trigger |
| **Batch Generation Rate** | > 10 captions / second | Benchmark test on 30-second timeline |
| **Memory Footprint** | < 75 MB RAM | Monitored in Activity Monitor / Task Manager |
| **Safety** | Zero overwrite of user video | Dedicated track creation + snapshot journal |
| **Data Privacy** | 100% Local-First | All styles stored in local JSON; no network telemetry |
| **Compatibility** | macOS 12+ (Apple Silicon & Intel), Windows 10/11 | Clean-room cross-platform path resolver |

---

## 7. Risk Register & Mitigation Strategy

| Risk | Impact | Probability | Mitigation Strategy |
|---|---|---|---|
| **Fusion Playback Stutter** | High | Medium | Built-in Resolve Render Cache advisor advising Smart Cache and Half Proxy. |
| **Missing Fusion UIManager Webview** | High | High | Replaced legacy Fusion UIManager with native PyQt6 GUI architecture. |
| **Timeline Track Collisions** | Medium | Low | Always query track count and append a new top-level video track. |
| **User Font Not Installed** | Low | Low | Fallback system fonts (`Arial`, `Helvetica Neue`, `Impact`) with safe defaults. |

---

## 8. Release Plan
- **v2.0.0 (Current):** Full PyQt6 architecture, 100% feature parity with observed workflows, 6 built-in viral social presets, batch automation, and clean-room documentation.
