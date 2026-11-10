# Motion Resolve for DaVinci Resolve Studio

**Motion Resolve** is an advanced companion application for DaVinci Resolve Studio dedicated to animated viral captions, declarative typography motion templates, and procedural physics animations.

Engineered with a modern **PyQt6** interface (`ui_qt/`), Motion Resolve delivers native **Text+** editability in DaVinci Resolve, real-time two-way timeline sync, open JSON styling presets, an interactive TikTok/Reels Safe Zone canvas, **73 declarative motion graphic templates** (including the ★ Signature and Trend 2026 packs) and **45 typography presets**, every one verified by rendering in DaVinci Resolve Studio 21.

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

### ★ Signature Pack (premium, art-directed)
Eleven templates built for real broadcast / documentary / social work, each with its own motion language
(masked rises, hairline draws, tracking breathes, blur-ins, damped springs) and verified in DaVinci Resolve 21
on 16:9 and 9:16 timelines:
Editorial Name Plate · Documentary Locator · Cinematic Title · Viral Hook Punch · Glass Pull Quote ·
Impact Stat Reveal · Chapter Card · Live Update Bar · Live Speaker Pill · Follow End Card ·
বাংলা শিরোনাম (Bengali Headline). Regenerate with `python3 scripts/build_signature_pack.py`.

**How templates reach the timeline (engine notes):** every layer compiles to its own Fusion branch
(`Text+ → [Blur] → MR_XF_<id> Transform → MR_Merge_<id>`; shapes use `Background + RectangleMask`), and every
animated input is a real `BezierSpline`/`XYPath` with cubic-bezier handles from the easing token. Layer opacity is
`Merge.Blend`, so titles are fully transparent on the first and last frame of the clip, and exits always finish
on the last frame (choreography is compressed proportionally on short clips). The in-app preview draws from the
same scene resolver (`core/templates/scene.py`) and motion plan (`core/templates/motion_curves.py`) as the
compiler, so preview and timeline match. Designs are authored on a 1920×1080 frame and scaled uniformly
(up to 2.4× on 9:16) to fit other timeline formats.

**Motion upgrade (Nov 2026):**
- **Count-up numbers** — any number in a title (`87%`, `+$2,000.00`, `1,000,000`, Bengali `১৪`) can count up from 0
  with its exact format; templates get a *Count Up Number* switch and *Count Duration*, presets use `count_up`.
- **Per-letter motion** via the Text+ Follower: cascades, spring pops, blur reveals and typewriter, in templates
  (`"stagger"` layer prop) and presets (`char_cascade`, `char_pop`, `char_blur`, `write_on`). Never applied to
  Bengali text, so conjuncts stay intact.
- **Caption motion library** — `zoom_punch`, `slam_drop`, `slide_up_blur`, `scale_fade`, `fade_in_slow`, `scale_out`,
  `blur_out` and the per-letter motions; every preset now has its own entrance/exit, and **Insert Title uses it**.
- **Trend 2026 pack** (under ★ Signature): Two-Tone Stack, Name + Role Chip, AI Prompt Bar, Kinetic Stack +
  Underline, Glow Hero Word, Count-Up Stat Card, Typewriter + Hero, Per-Line Box Caption
  (`python3 scripts/build_trend_pack.py`). Older templates were re-choreographed by category
  (`python3 scripts/rechoreograph_templates.py`). Research notes: `docs/design/motion-trends-2026.md`;
  real-Resolve contact sheets: `docs/qa/`.

**Bundled fonts:** Playfair Display, DM Serif Display, Syne, JetBrains Mono, Pinyon Script, Barlow, Hind Siliguri
and Noto Sans Bengali ship in `resources/fonts` (SIL Open Font License, see `resources/fonts/licenses`). The app
and `install.py` copy any missing ones into your user font folder (no admin rights, never overwrites). Restart
DaVinci Resolve once afterwards so Text+ lists them. Windows-only Consolas / Bahnschrift were replaced by
JetBrains Mono / Barlow so presets look the same on Mac and PC.

### 2. Templates Tab (73 Declarative Motion Graphic Templates)
- **73 templates** in 11 categories: ★ Signature (11) and Trend 2026 (8) shown together under **★ Signature**,
  plus Podcast, SaaS / Tech, Minimal, Editorial, Social / Reels, Documentary / NGO, Cinematic, Kinetic and Agency.
- **One Fusion branch per layer** — every text and shape layer gets its own nodes
  (`Text+ → [Blur] → Transform → Merge`, shapes as `Background + RectangleMask`) and every animated input is a real
  BezierSpline / XYPath / PolyPath with cubic-bezier easing, fully editable in Fusion and the spline editor.
- **Clean edges on any clip length** — every layer is transparent on the first and last frame; entrances and exits
  are compressed proportionally on short clips, so exits always finish on the clip's last frame (even 18-frame cuts).
- **Per-letter motion** (Text+ Follower) for cascades, spring pops and blur reveals; never applied to Bengali text.
- **Count-up numbers** with a *Count Up Number* switch and *Count Duration* control.
- **Preview = timeline** — the in-app preview uses the same layout engine and motion plan as the compiler, and text is
  measured with the real installed font.
- **Theme palettes**, live parameter editing, and JSON template import/export with collision-safe naming.
- **Undo / Redo** of template applies via Fusion comp snapshots.

---

### 3. Presets Tab (45 Studio-Grade Typography Presets)
- **45 Curated Presets** inspired by top content creators and broadcast standards, each with its own entrance/exit motion (17 distinct entrances):
  - *Alex Cooper Magenta*, *Ali Abdaal Clean*, *Hormozi Bold Yellow*, *MrBeast Explosive*, *Iman Gadzhi Luxury*, *Vox Highlighter*, *Cyber Glitch*, *FinTech Emerald*, *Bengali Viral Vlogger*, *Retro Synthwave*, and 35 additional styles.
- **Title Composer & Hero Word Chips**:
  - Enter custom copy into the composer bar.
  - Word chips automatically generate below the composer: click any word chip to designate it as the **Hero Word**.
  - **2-Color Accent Engine**: Automatically splits text into base and hero layers, applying distinct fonts, colors, stroke outlines, drop shadows, and scale multipliers.
- **Line Spacing**: `1.00 = normal`, mapped to the Text+ LineSpacing multiplier.
- **Insert Title uses the preset's motion**, and numbers in the text can count up (`count_up`).
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
- **Uniform Design Scaling**: templates are authored on a 1920×1080 frame and scaled uniformly around their anchor
  for other formats, growing up to 2.4× on 9:16 and 1.5× on 1:1 until they meet the side margins. Caption presets
  use 1.35× on 9:16 and 1.12× on 1:1 (Text+ size is relative to frame *width*).
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

### Requirements
- **DaVinci Resolve Studio** 18, 19 or 21+ (external scripting is a Studio feature).
- Resolve → *Preferences → System → General → External scripting using: **Local***.
- Python 3.10+ with PyQt6 (`pip install PyQt6`).

### Installation
```bash
python3 install.py
```
On Windows use `py -3.12 install.py`. The installer registers native launchers in:
- **macOS**: `~/Library/Application Support/Blackmagic Design/DaVinci Resolve/Fusion/Scripts/Comp/` and `Edit/`
- **Windows User**: `%APPDATA%\Blackmagic Design\DaVinci Resolve\Support\Fusion\Scripts\Comp\` and `Edit\`
- **Windows System-Wide**: `%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Fusion\Scripts\Utility\`
- **Desktop Shortcut** (Windows): `Launch Motion Resolve.bat` for 1-click startup.

It also installs the bundled fonts into your user font folder (no admin rights). Restart Resolve once afterwards.

### Launching in DaVinci Resolve Studio
1. Open DaVinci Resolve Studio.
2. Top menu: **`Workspace > Scripts > Motion Resolve`**.
3. The companion panel opens beside your viewer as an independent, non-blocking process.

### Running Standalone
```bash
python3 main.py
```

### Running the Test Suite
```bash
python3 -m pytest -q
```
**127 tests** cover easing and spline handles, keyframe writing against a Fusion stand-in that reproduces Resolve 21
behaviour, short-clip timing, per-letter stagger, count-up formatting, layout, presets and the UI.

## 🛠 Troubleshooting

| Symptom | Fix |
|---|---|
| Badge shows **○ PREVIEW**, "Could not insert title" | Resolve must be **Studio** with *External scripting using: Local*. Motion Resolve reconnects by itself every few seconds; the status bar explains what is blocking. |
| Status bar says Resolve's scripting port is taken by another app (e.g. **Ollama**) | Quit and reopen that app so it picks another port; Motion Resolve reconnects automatically. |
| A preset or template font looks wrong | Restart Resolve once after first launch so it loads the bundled fonts. |
| Title text missing on the timeline | Fixed: styles are matched against Resolve's own font list (a style Resolve lacks renders nothing). |
