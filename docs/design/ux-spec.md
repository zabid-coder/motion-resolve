# UX / UI Specification: CaptionForge for Resolve

**Product Name:** CaptionForge for Resolve (Motion Resolve)  
**Design System:** Obsidian Neon (Dark Purple Charcoal + Neon Orange + Laser Pink)  
**Window Footprint:** 440px width × 890px height (Optimal for 1440p / 4K dual monitor Resolve setups)

---

## 1. Design Philosophy & Aesthetic Identity
CaptionForge is engineered specifically for video editors who demand high speed, zero clutter, and instantaneous visual feedback. Rather than adopting generic OS dialog boxes, CaptionForge features a bespoke **cyber-dark gaming/studio aesthetic**:
- Deep obsidian and charcoal violet backgrounds (`#0d0b14`, `#151124`) to eliminate eye fatigue in color-grading environments.
- Vibrant high-contrast neon-orange accents (`#ff5500`) for active states, focal triggers, and interactive handles.
- Precision laser-pink guidelines (`#ff2a85`) referencing viral mobile video safe zones.
- Tactile physical control pads (D-Pads) providing immediate muscle-memory animation selection.

---

## 2. Color Palette & Design Tokens

| Token Name | Hex Code | Purpose |
|---|---|---|
| `COLOR_BG` | `#0d0b14` | Window background & deepest panels |
| `COLOR_CARD` | `#151124` | Elevated cards, containers, composer frame |
| `COLOR_CANVAS` | `#000000` | Smartphone 9:16 video simulation viewport |
| `COLOR_BORDER` | `#251f38` | Structural dividing borders |
| `COLOR_BORDER_LIGHT` | `#382e54` | Hover borders and subtle separators |
| `COLOR_ORANGE` | `#ff5500` | Primary action buttons, active pills, slider progress |
| `COLOR_ORANGE_HOVER`| `#ff6a1a` | Mouse hover feedback for primary controls |
| `COLOR_ORANGE_MUTED`| `#331508` | Background for toggled secondary actions |
| `COLOR_TEXT` | `#ffffff` | Primary readable typography |
| `COLOR_MUTED` | `#88829d` | Secondary metadata labels, inactive badges |
| `COLOR_PINK` | `#ff2a85` | Vertical center guideline laser |

---

## 3. Structural Layout & Information Architecture

```
┌─────────────────────────────────────────────────────────┐
│ [captionforge]             [CC Convert Captions] [-] [···]│  <- Header (38px)
├─────────────────────────────────────────────────────────┤
│ [   Workspace   ]  [    Titles    ]  [      Auto      ] │  <- Nav Tab Bar (32px)
├─────────────────────────────────────────────────────────┤
│                                                         │
│                      STACKED VIEWS                      │
│                                                         │
│  [Workspace Tab]          [Titles Tab]      [Auto Tab]  │
│  - Playhead / In/Out      - Search & Cat    - Style Card│
│  - T1 / T2 / T3           - Preset Grid     - WPS Slider│
│  - +Text / Undo           - Typography Card - Punct / FX│
│  - 9:16 Phone Canvas      - Composer &      - Plan Tree │
│  - Motion D-Pads          - Hero Accent     - Shift ◄ ► │
│  - 2x2 Effects Grid       - Insert Title    - Create ★  │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ SAMPLE · 1080×1920 · 0 captions at playhead        ⌘Z   │  <- Status Bar (24px)
└─────────────────────────────────────────────────────────┘
```

---

## 4. Component Specifications

### 4.1 Sub-Toolbar (Workspace & Titles Tabs)
- **Target Mode Pills:**
  - Active: Filled neon orange (`#ff5500`), white text, bold.
  - Inactive: Dark slate purple (`#1a152b`), muted text (`#88829d`), 1px border (`#28213e`).
- **Template Pills (`T1★`, `T2`, `T3`):**
  - Compact rounded buttons (`6px` border-radius) providing instant line-break formatting.
- **`+ Text` Quick Button:**
  - Distinctive orange outline button (`border: 1.5px solid #ff5500`).

### 4.2 Interactive 9:16 Phone Canvas View
- **Simulated Aspect Ratio:** Fixed 9:16 mobile smartphone frame with curved bezel corners (`18px` border radius).
- **Center Laser Guideline:** 1px dashed laser line rendered in `#ff2a85` indicating the horizontal and vertical center of the frame.
- **Bounding Box & Transform Handles:**
  - 1.5px solid orange bounding box enclosing the text block.
  - 4 circular corner anchor handles (diameter 8px, `#ffffff` with `#ff5500` border) that highlight on hover and allow drag repositioning.
- **Alignment Controls Bar:**
  - Left (`|←`), Center (`÷`), Right (`→|`), Fit (`⛶`), and Reset (`↺`).
- **Floating Tool Strip:**
  - Duplicate (`❐`), Copy Attributes (`📋`), Crosshair (`⌖`), Scale (`⤢`), Color (`🎨`), Font (`Aa`).

### 4.3 Motion Effects Controller (Bottom Grid)
- **Dual D-Pads:**
  - Left pad controls entrance (`IN`) direction; right pad controls exit (`OUT`) direction.
  - Buttons (`▲`, `◄`, `●`, `►`, `▼`) illuminate in solid neon orange when active.
- **Center 2×2 Effects Grid:**
  - `∿ Shake`, `❐ Jitter`, `〰 Scribble`, `≡⚬ M. Blur`.
  - Toggle buttons with persistent active states.
- **AUTO Continuity Button:**
  - Full-width prominent bottom bar cycling dynamic motion directions across timeline cuts.

### 4.4 Convert Captions Drawer
- **Modal Behavior:** Smoothly animates / toggles directly below the sub-toolbar.
- **Border:** 1.5px solid `#ff5500` with subtle glow.
- **Inputs:** Subtitle track dropdown with cue counter, style selection, and punctuation removal checkbox.

### 4.5 Collapsible Mini Playback Mode
- Triggered via the `−` button in the top header.
- The window collapses into a compact 50px floating bar containing only the logo, status feedback, and `+` expand button.
- Allows editors to verify 60fps full-screen playback on their Resolve viewer without moving or closing the panel.

---

## 5. Interaction & Feedback Rules
1. **Immediate Visual Confirmation:** Every button click produces immediate visual feedback (color inversion or status message).
2. **Non-Blocking Operation:** Batch timeline generation runs with progress updates so the user is never left wondering if the app is frozen.
3. **Always-Available Undo:** The bottom status bar always displays `⌘Z undoes` as a reminder that any batch modification is completely reversible.
