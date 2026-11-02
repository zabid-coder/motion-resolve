# Motion Resolve — Audit Fixes & Quality Polish Implementation Plan

> **Goal**: Fix the 7 P1 bugs identified in code review, ensure 100% preview-to-timeline parity in Fusion templates, enforce strict target selection, fix AUTO APPLY motion controls, make Convert Drawer safe and intuitive, ensure dedicated track placement, and implement true undo/redo for existing titles.

---

## Proposed Changes

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Strict Target Selection Model (core/resolve_api.py)      │
│    - playhead: strictly target title at playhead position   │
│    - selected: strictly target selected clips               │
│    - inout: strictly target clips within In/Out range       │
│    - all: target all titles in timeline                     │
├─────────────────────────────────────────────────────────────┤
│ 2. AUTO APPLY Motion Controls Follower                      │
│    - motion_panel.py: expose get_motion_data()              │
│    - workspace_tab.py: read current mode, sliders & toggles │
│    - sequence directions with user's active tuning          │
├─────────────────────────────────────────────────────────────┤
│ 3. Convert Drawer Default & In/Out Fix                      │
│    - Add "Keep Default / Look from style..." as index 0     │
│    - Add convert scope: Marked In/Out vs Entire Track       │
│    - Graceful fallback when In/Out marks not set            │
├─────────────────────────────────────────────────────────────┤
│ 4. Dedicated Track Placement Enforcement                    │
│    - auto_generator.py: track locking & destination checks  │
│    - Verify item.GetTrackTypeAndIndex()                     │
├─────────────────────────────────────────────────────────────┤
│ 5. True Layer-Wise Motion in Fusion Compiler                │
│    - Compile per-layer motion tracks onto individual tools  │
│    - Each layer animates at its authored stagger timecode   │
├─────────────────────────────────────────────────────────────┤
│ 6. Dynamic Reveal Mask Sizing                               │
│    - Calculate mask bounds from layer heights and offsets   │
│    - Expand for tall stacks/cards without cropping          │
├─────────────────────────────────────────────────────────────┤
│ 7. Full Undo & Redo for Existing Titles & Batches           │
│    - push_modify_snapshot() storing pre-edit styling        │
│    - undo_last_batch() restores previous styling            │
│    - redo_last_batch() reapplies modification               │
│    - btn_redo dynamically enables in WorkspaceTab           │
└─────────────────────────────────────────────────────────────┘
```

---

## Execution Steps

### Step 1: Target Selection Model (`core/resolve_api.py`)
- Remove the premature `selected` clip check inside `mode == "playhead"`.
- When `mode == "playhead"`: Find the topmost title where `item.GetStart() <= playhead <= item.GetEnd()`.
- When `mode == "selected"`: Return `get_selected_video_items()` filtered by Text+.
- When `mode == "inout"`: Return items spanning the In/Out marks.
- When `mode == "all"`: Return all text items.

### Step 2: AUTO Motion Controls (`ui_qt/widgets/motion_panel.py` & `ui_qt/tabs/workspace_tab.py`)
- Add `get_motion_data()` to `MotionPanel`.
- Update `_on_auto_motion_clicked` in `WorkspaceTab` to use `active_motion = self.motion_panel.get_motion_data()`.
- Respect `mode_in`, `mode_out`, `shake`, `flicker`, `blur`, `distance`, etc.

### Step 3: Convert Drawer Defaults (`ui_qt/widgets/convert_drawer.py` & `ui_qt/tabs/workspace_tab.py`)
- In `populate_styles()`: Insert `"Look from style... (Default Look)"` at index 0.
- In `_on_convert_clicked()`: Only pass style if user chose a real preset.
- Add In/Out vs All Track handling with helpful status message.

### Step 4: Dedicated Track Placement (`core/auto_generator.py`)
- When creating dedicated track, lock non-target video tracks during insertion to prevent collision or misplacement.
- Unlock tracks after insertion and verify using `GetTrackTypeAndIndex()`.

### Step 5: True Layer-Wise Motion (`core/templates/fusion_compiler.py`)
- Implement `_compile_layer_motion()` for each layer tool in `_build_layers()`.
- Each layer tool (`Template`, `MR_Layer_Text2`, `MR_Layer_Text3`, `MR_Layer_LineMask`, `MR_Layer_PlateMask`) receives its authored motion tracks directly.

### Step 6: Dynamic Reveal Mask Sizing (`core/templates/fusion_compiler.py`)
- Calculate dynamic mask height and center Y from all layers' extents.
- Ensures no cropping on tall stacks or cards while preserving lower third framing.

### Step 7: Undo / Redo for Existing Titles (`core/resolve_api.py`, `ui_qt/tabs/titles_tab.py`, `ui_qt/tabs/workspace_tab.py`)
- Implement `push_modify_snapshot(items, prev_styles, new_styles, operation_name)`.
- Update `undo_last_batch()` to restore previous styles when operation type is `modify`.
- Update `redo_last_batch()` to re-apply new styles.
- Enable `btn_redo` when redo history is available.
