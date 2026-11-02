# Phase 1 & Phase 2 Bug Fixes & Refinements Implementation Plan

**Goal:** Fix all verified P1 (critical stability, data integrity, sync) and P2 (broken/ineffective controls, extraction precision, filter mismatches, track accumulation) issues in Motion Resolve.

## Tasks Overview

- [x] **Task 1: [P1] Missing `Any` import in `core/templates/registry.py`**
- [x] **Task 2: [P1] Prevent sample cues from generating into timeline in `ui_qt/tabs/auto_tab.py`**
- [x] **Task 3: [P1] Reconnect bridge synchronization across all 4 tabs in `ui_qt/main_window.py`**
- [x] **Task 4: [P1] Pass timeline FPS to SRT parser in `ui_qt/tabs/auto_tab.py`**
- [x] **Task 5: [P2] Shake & Flicker effect enable flags in `ui_qt/tabs/auto_tab.py`**
- [x] **Task 6: [P2] Disable unhandled Redo button with clear tooltip in `ui_qt/tabs/workspace_tab.py`**
- [x] **Task 7: [P2] Wire 2-Color button and implement hero word styling in `ui_qt/tabs/titles_tab.py` & `core/text_plus_builder.py`**
- [x] **Task 8: [P2] Fix In/Out mode precedence in `core/resolve_api.py:get_target_clips`**
- [x] **Task 9: [P2] Full style attribute extraction in `core/text_plus_builder.py:extract_style_from_clip`**
- [x] **Task 10: [P2] Fix category filters in `ui_qt/tabs/titles_tab.py`**
- [x] **Task 11: [P2/P3] Prevent blank track accumulation on caption generation & clean up on undo in `core/auto_generator.py` & `core/resolve_api.py`**
- [x] **Task 12: Run complete test suite and capture verification screenshots**
