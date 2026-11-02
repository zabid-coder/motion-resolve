# Motion Resolve for DaVinci Resolve Studio

**Motion Resolve** is an advanced companion application for DaVinci Resolve Studio dedicated to animated viral captions, declarative typography motion templates, and procedural physics animations.

Engineered with a modern **PyQt6** interface (`ui_qt/`), Motion Resolve delivers native **Text+** editability in DaVinci Resolve, real-time two-way timeline sync, open JSON styling presets, an interactive TikTok/Reels Safe Zone canvas, 48 declarative motion graphic templates, and 33 viral typography presets.

---

## 📱 Architecture & Workflow Breakdown

Motion Resolve features a 4-tab workflow tailored for short-form creators, commercial editors, and motion designers:

### 1. Workspace Tab (Interactive Canvas & Live Motion Controller)
- **Real-Time Two-Way Timeline Sync**: Motion Resolve syncs the phone canvas text, typography, size, position, colors, and background boxes with whatever Text+ clip is active under your playhead in DaVinci Resolve. Edits apply directly to the timeline.
- **Viewer-Adjacent Mobile Ratio (440×890)**: Sits beside the Resolve reference viewer without obstructing the timeline or inspector.
- **Target Scopes**:
  - **`Playhead` Mode**: Targets the Text+ clip directly under the playhead.
  - **`In/Out` Mode**: Targets all Text+ clips within the timeline In/Out range for batch positioning, motion styling, or template application.
- **Interactive 9:16 Preview Canvas**:
  - **TikTok / Reels Safe Zone Overlay (`🛡 Safe Zone`)**: Translucent boundary marks preventing subtitles from being obscured by platform UI overlays (profile handle, caption box, audio disc, right-side action buttons).
  - **Magnetic Snapping**: Precision snapping to horizontal center (`0.50`) and lower-third baseline (`0.28` / `0.65`).
  - **Neon Guideline**: Dashed indicator while dragging, solid neon pink laser when centered.
  - Interactive bounding box and handles with real-time viewport zoom/pan.
  - Alignment shortcuts: Left (`|←`), Center (`÷`), Right (`→|`), Fit (`⛶`), and Baseline Reset (`↺`).
- **Motion Effects Controller**:
  - **Top Mode Toggles**: Dedicated IN and OUT motion selectors (`Slide`, `Bounce`).
  - **Dual D-Pads**: Left D-Pad for IN direction (`▲`, `◄`, `●`, `►`, `▼`), Right D-Pad for OUT direction.
  - **Physics Effects Grid**: `∿ Shake` (continuous vibration), `❐ Jitter` (micro-jitter), `〰 Scribble` (hand-drawn jitter), `≡⚬ M. Blur` (directional motion blur).
  - **Accent Sub-Row**: Flicker intensity scaling, Shake magnitude, and Blur controls.
  - **`AUTO` Button**: Alternates motion directions between successive clips for visual cadence.
- **Convert Captions Drawer**:
  - Expandable drawer in the header to convert built-in Resolve Subtitle tracks into editable Text+ clips.
  - Features source subtitle track selection, style preset dropdown, punctuation removal toggle, and `Convert · In/Out` or `Convert Entire Track` options.

---

### 2. Templates Tab (48 Declarative Motion Graphic Templates)
- **48 Curated Declarative Templates** spanning 8 categories:
  1. **Podcast**: Two-speaker badges, episode tags, timestamps, and lower thirds.
  2. **SaaS / Tech**: Product feature pills, metric highlights, callouts, and step indicators.
  3. **Minimal**: Elegant clean titles, modern quotes, and micro-branding tags.
  4. **Editorial**: High-contrast editorial headlines, magazine pull quotes, and chapter cards.
  5. **Social / Viral**: Retention hooks, alert badges, emoji pill callouts, and comment overlays.
  6. **Documentary / Vox**: Map locators, stat counters, archival lower thirds, and evidence cards.
  7. **Cinematic**: Letterbox titles, cinematic billing blocks, and credits.
  8. **Kinetic**: Dynamic scale-punch titles, staggered word reveals, and bounce stacks.
- **Unified Multi-Node Fusion Architecture**:
  - Compiles templates as clean, single-track multi-node Fusion compositions on the edit timeline.
  - Individual text layers (Primary, Subtitle, Tag), background cards, dynamic reveal masks, and transform modifiers remain fully isolated and editable via the Inspector.
- **Dynamic Reveal Masks & Safe Clamping**:
  - Dynamic rectangular reveal masks computed from actual layer bounding boxes.
  - Strict timing clamping ensures exit animations always complete within short subtitle clips (e.g. 18-frame cuts).
- **Theme Color & Token Engine**:
  - Live color palette switching across Default Neon, Midnight Amber, Cyber Emerald, Solar Crimson, and Nordic Frost.
- **Live Preview Canvas & Template Import/Export**:
  - Interactive render canvas simulating the exact motion layout before applying to the timeline.
  - Full JSON template export and import with collision-safe naming.

---

### 3. Presets Tab (33 Studio-Grade Typography Presets)
- **33 Curated Presets** inspired by top content creators and broadcast standards:
  - *Alex Cooper Magenta*, *Ali Abdaal Clean*, *Hormozi Bold Yellow*, *MrBeast Explosive*, *Iman Gadzhi Luxury*, *Vox Highlighter*, *Cyber Glitch*, *FinTech Emerald*, *Bengali Viral Vlogger*, *Retro Synthwave*, and 23 additional styles.
- **Title Composer & Hero Word Chips**:
  - Enter custom copy into the composer bar.
  - Word chips automatically generate below the composer: click any word chip to designate it as the **Hero Word**.
  - **2-Color Accent Engine**: Automatically splits text into base and hero layers, applying distinct fonts, colors, stroke outlines, drop shadows, and scale multipliers.
- **Normalized Line Spacing**:
  - Intuitive `1.00 = normal` spinbox mapping seamlessly translated to TextPlus baseline offsets (`0.00`).
- **`＋ Add From Timeline`**:
  - Extracts full typography, styling, and two-color HeroText attributes from any selected Text+ timeline clip and saves it into your reusable catalog.
- **Resilient User Storage**:
  - Automatically loads built-in presets from `data/styles/` while saving user-created styles to `~/.motion_resolve/styles/` if the working directory is read-only.

---

### 4. Auto Captions Tab (Batch Engine with Word Shifting)
- **Automatic Subtitle Track Detection**: Instantly detects and parses subtitles from `Subtitle 1`, `Subtitle 2`, etc.
- **Direct SRT File Import**: Frame-rate accurate SRT parsing aligned with current timeline frame rates (23.976, 24, 25, 29.97, 30, 59.94, 60 fps).
- **Words-Per-Slide (WPS) Chunking**: Partition captions into 1, 2, 3, 4, or 5 words per slide with cumulative character boundary safety.
- **Interactive Timeline Group Plan**:
  - Previews start/end frames, slide indices, and word layouts.
  - Double-click any cell to adjust words directly in the table.
  - **Word Shifting**: Click `◄ Shift Left` or `Shift Right ►` to adjust word cadence between adjacent slides without altering timecode boundaries.
- **Sample Preview Isolation**:
  - Isolated preview cues prevent dummy sample text from accidentally populating the live timeline.
- **Dedicated Track Safety**:
  - Automatically detects top track occupancy and creates a dedicated video track with automatic track locking during generation to prevent accidental overwrites.

---

### 5. Multi-Aspect Ratio Responsive Intelligence (9:16 Vertical, 1:1 Square, 16:9 Landscape)
- **Automatic Timeline Resolution Detection**: Dynamically inspects DaVinci Resolve timeline resolution and aspect ratio via `ResolveBridge.get_timeline_resolution()`.
- **Dynamic Font & Geometry Scaling**:
  - **Vertical 9:16 (1080x1920)**: Automatically scales typography and backing plates by `(1080 / frame_h) * 1.15` for maximum mobile readability on TikTok, Instagram Reels, and YouTube Shorts.
  - **Square 1:1 (1080x1080)**: Automatically scales by `(1080 / frame_h) * 0.90` with proportional card padding.
  - **Landscape 16:9 (1920x1080)**: Standard broadcast 1.0x layout with cinematic margins.
- **Mobile Safe Zone Enforcer**:
  - Automatically shifts lower thirds and badges into the broadcast-safe region (`pos_y >= 0.32` on vertical) to prevent overlapping with TikTok/Reels UI buttons, captions, and account handles.
- **Dynamic Card & Plate Padding**:
  - Backing plates and cards dynamically compute their bounding height (`min_needed_h`) to maintain generous 15-20% internal padding around multi-line text stacks and divider lines across all screen formats.
- **Optical Multi-Line Stack Centering**:
  - Multi-line badges, lower-third slates, and two-color presets automatically center their text hierarchy inside backing plates without border clipping.
- **Non-Destructive Track 1 Footage Safety**:
  - Protects user camera footage on Track 1. All title and template insertions automatically target Track 2 or higher (`tl.MoveItems` to Track 2+).

---

## 🚀 Running Motion Resolve

### Installation
Run the automated installer to link native Python and Lua launchers into DaVinci Resolve Studio:
```bash
py -3.12 install.py
```
This automatically registers native launchers in:
- **macOS**: `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Comp/` and `Edit/`
- **Windows User**: `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Comp\` and `Edit\`
- **Windows System-Wide**: `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Utility\`
- **Desktop Shortcut**: Creates `Launch Motion Resolve.bat` on your Desktop for 1-click startup.

### Launching in DaVinci Resolve Studio
1. Open **DaVinci Resolve Studio 18, 19, or 21+**.
2. Top menu: **`Workspace > Scripts > Motion Resolve`**.
3. The companion panel launches immediately beside your reference viewer as an independent, non-blocking process.

### Running Standalone
```bash
py -3.12 main.py
```

### Running Test Suite
```bash
py -3.12 -m unittest discover tests
```
All **103 automated unit tests** verify animation math, spline interpolation, responsive aspect ratios, template compilation, subtitle clamping, redo history, and typography normalization.
