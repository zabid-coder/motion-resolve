"""
CaptionForge for Resolve - DaVinci Resolve Scripting API Wrapper
Provides robust, safe timeline operations, Playhead vs In/Out range handling,
batch snapshot & undo journal, and Text+ title insertion.
"""

import sys
import os
import tempfile
import atexit
from core.paths import ensure_sys_path

ensure_sys_path()

_RESOLVE_INSTANCE = None
_FUSION_INSTANCE = None

def get_resolve():
    """Obtain or retrieve the active DaVinci Resolve instance."""
    global _RESOLVE_INSTANCE
    if _RESOLVE_INSTANCE is not None:
        return _RESOLVE_INSTANCE

    if "resolve" in globals() and globals()["resolve"] is not None:
        _RESOLVE_INSTANCE = globals()["resolve"]
        return _RESOLVE_INSTANCE

    try:
        import DaVinciResolveScript as dvr
        _RESOLVE_INSTANCE = dvr.scriptapp("Resolve")
        if _RESOLVE_INSTANCE is not None:
            return _RESOLVE_INSTANCE
    except Exception:
        pass

    try:
        import fusionscript as fs
        _RESOLVE_INSTANCE = fs.scriptapp("Resolve")
        if _RESOLVE_INSTANCE is not None:
            return _RESOLVE_INSTANCE
    except Exception:
        pass

    try:
        import bmd
        _RESOLVE_INSTANCE = bmd.scriptapp("Resolve")
        if _RESOLVE_INSTANCE is not None:
            return _RESOLVE_INSTANCE
    except Exception:
        pass

    return None

def get_fusion():
    """Obtain or retrieve the Fusion instance."""
    global _FUSION_INSTANCE
    if _FUSION_INSTANCE is not None:
        return _FUSION_INSTANCE

    if "fusion" in globals() and globals()["fusion"] is not None:
        _FUSION_INSTANCE = globals()["fusion"]
        return _FUSION_INSTANCE

    res = get_resolve()
    if res:
        try:
            _FUSION_INSTANCE = res.Fusion()
            if _FUSION_INSTANCE:
                return _FUSION_INSTANCE
        except Exception:
            pass

    try:
        import DaVinciResolveScript as dvr
        _FUSION_INSTANCE = dvr.scriptapp("Fusion")
        if _FUSION_INSTANCE:
            return _FUSION_INSTANCE
    except Exception:
        pass

    return None

class ResolveBridge:
    """High-level abstraction for timeline operations, caption insertion, and range queries."""

    def __init__(self):
        self.resolve = get_resolve()
        self.fusion = get_fusion()
        self._undo_history = []  # List of snapshots for batch undo
        self._redo_history = []  # List of snapshots for redo
        atexit.register(self._cleanup_snapshot_files)

    def is_connected(self):
        return self.resolve is not None

    def get_project_manager(self):
        if not self.resolve:
            return None
        return self.resolve.GetProjectManager()

    def get_current_project(self):
        pm = self.get_project_manager()
        if not pm:
            return None
        return pm.GetCurrentProject()

    def get_current_timeline(self):
        proj = self.get_current_project()
        if not proj:
            return None
        return proj.GetCurrentTimeline()

    def get_media_pool(self):
        proj = self.get_current_project()
        if not proj:
            return None
        return proj.GetMediaPool()

    def get_timeline_fps(self):
        """Get timeline framerate as float."""
        tl = self.get_current_timeline()
        if not tl:
            return 30.0
        try:
            settings = tl.GetSettings()
            fps_val = settings.get("timelineFrameRate", "30")
            if isinstance(fps_val, (int, float)):
                return float(fps_val)
            clean_fps = str(fps_val).replace("DF", "").strip()
            return float(clean_fps)
        except Exception:
            return 30.0

    def get_timeline_resolution(self):
        """Returns (width, height) tuple."""
        tl = self.get_current_timeline()
        if not tl:
            return (1080, 1920)
        try:
            settings = tl.GetSettings()
            w = int(settings.get("timelineResolutionWidth", 1080))
            h = int(settings.get("timelineResolutionHeight", 1920))
            return (w, h)
        except Exception:
            return (1080, 1920)

    def get_playhead_frame(self):
        """Return the current playhead frame relative to timeline start."""
        tl = self.get_current_timeline()
        if not tl:
            return 0
        try:
            tc = tl.GetCurrentTimecode()
            start_tc = tl.GetStartTimecode()
            fps = self.get_timeline_fps()
            curr_frames = self.timecode_to_frames(tc, fps)
            start_frames = self.timecode_to_frames(start_tc, fps)
            return max(0, curr_frames - start_frames)
        except Exception:
            return 0

    def set_playhead_frame(self, frame_offset):
        """Set playhead position by frame offset from timeline start."""
        tl = self.get_current_timeline()
        if not tl:
            return False
        try:
            start_tc = tl.GetStartTimecode()
            fps = self.get_timeline_fps()
            start_frames = self.timecode_to_frames(start_tc, fps)
            target_frames = start_frames + frame_offset
            target_tc = self.frames_to_timecode(target_frames, fps)
            return tl.SetCurrentTimecode(target_tc)
        except Exception:
            return False

    def get_in_out_range(self):
        """
        Returns (in_frame, out_frame) relative to timeline start if set, else None.
        """
        tl = self.get_current_timeline()
        if not tl:
            return None
        try:
            marks = tl.GetMarkInOut()
            if marks and "video" in marks:
                v = marks["video"]
                return (v.get("in", 0), v.get("out", 0))
            elif marks and "in" in marks:
                return (marks.get("in", 0), marks.get("out", 0))
        except Exception:
            pass
        return None

    def get_selected_video_items(self):
        """Return list of selected TimelineItem objects in the active timeline."""
        tl = self.get_current_timeline()
        if not tl:
            return []
        try:
            return tl.GetSelectedClips() or []
        except Exception:
            return []

    @staticmethod
    def is_text_plus_item(item):
        """Check if a TimelineItem is a Text+ title or contains a Text+ tool."""
        if not item:
            return False
        try:
            if item.GetFusionCompCount() == 0:
                return False
            comp = item.GetFusionCompByIndex(1)
            if not comp:
                return False
            if comp.FindTool("Template"):
                return True
            for t in comp.GetToolList().values():
                if t.GetAttrs().get("TOOLS_RegID") == "TextPlus":
                    return True
        except Exception:
            pass
        return False

    def get_target_clips(self, mode="playhead", text_only=True):
        """
        Returns the list of target clips based on mode:
        - "playhead": Text+ title directly under current playhead (topmost video track)
        - "inout": all clips intersecting the In/Out marks
        - "selected" / "selection": currently highlighted clips
        - "all": all clips in the timeline
        If text_only is True, filters to only return Text+ titles.
        """
        tl = self.get_current_timeline()
        if not tl:
            return []

        clean_mode = str(mode).lower().strip()

        # 1. In/Out Range mode: strictly within marked in/out
        if clean_mode in ("inout", "in_out"):
            in_out = self.get_in_out_range()
            if in_out and in_out[1] > in_out[0]:
                in_f, out_f = in_out
                matching = []
                for track_idx in range(1, tl.GetTrackCount("video") + 1):
                    for item in tl.GetItemListInTrack("video", track_idx):
                        if item.GetStart() <= out_f and item.GetEnd() >= in_f:
                            if not text_only or self.is_text_plus_item(item):
                                matching.append(item)
                return matching
            return []

        # 2. Selected mode: strictly selected clips
        if clean_mode in ("selected", "selection"):
            selected = self.get_selected_video_items()
            if selected:
                if text_only:
                    return [it for it in selected if self.is_text_plus_item(it)]
                return selected
            return []

        # 3. All mode: all clips across all video tracks
        if clean_mode == "all":
            all_items = []
            for track_idx in range(1, tl.GetTrackCount("video") + 1):
                for item in tl.GetItemListInTrack("video", track_idx):
                    if not text_only or self.is_text_plus_item(item):
                        all_items.append(item)
            return all_items

        # 4. Playhead mode: strictly title under current playhead on topmost track
        # Never let off-playhead selected clips hijack playhead mode
        playhead = self.get_playhead_frame()
        for track_idx in range(tl.GetTrackCount("video"), 0, -1):
            for item in tl.GetItemListInTrack("video", track_idx):
                if item.GetStart() <= playhead <= item.GetEnd():
                    if not text_only or self.is_text_plus_item(item):
                        return [item]

        return []

    def get_active_caption_metadata(self):
        """
        Scans from topmost video track down to find the active Text+ title
        currently under the playhead, and extracts its live properties for canvas sync.
        """
        tl = self.get_current_timeline()
        if not tl:
            return None

        tc = tl.GetCurrentTimecode()
        start_tc = tl.GetStartTimecode()
        fps = self.get_timeline_fps()
        curr_f = self.timecode_to_frames(tc, fps)
        start_f = self.timecode_to_frames(start_tc, fps)
        rel_f = max(0, curr_f - start_f)

        # 1. Check if a selected clip is currently under the playhead
        selected = self.get_selected_video_items()
        text_item = None
        active_track = 1

        for it in selected:
            if (it.GetStart() <= rel_f < it.GetEnd()) or (it.GetStart() <= curr_f < it.GetEnd()):
                if self.is_text_plus_item(it):
                    text_item = it
                    break

        # 2. Otherwise scan topmost video track down under current playhead
        if not text_item:
            track_count = tl.GetTrackCount("video")
            for tr in range(track_count, 0, -1):
                items = tl.GetItemListInTrack("video", tr) or []
                for it in items:
                    if (it.GetStart() <= rel_f < it.GetEnd()) or (it.GetStart() <= curr_f < it.GetEnd()):
                        if self.is_text_plus_item(it):
                            text_item = it
                            active_track = tr
                            break
                if text_item:
                    break

        # 3. Fallback: If no clip directly under playhead, use any selected Text+ clip
        if not text_item and selected:
            for it in selected:
                if self.is_text_plus_item(it):
                    text_item = it
                    break

        if not text_item:
            return None

        try:
            comp = text_item.GetFusionCompByIndex(1)
            tpl = comp.FindTool("Template") if comp else None
            if not tpl and comp:
                for t in comp.GetToolList().values():
                    if t.GetAttrs().get("TOOLS_RegID") == "TextPlus":
                        tpl = t
                        break
            if not tpl:
                return None

            styled_text = str(tpl.GetInput("StyledText") or "")
            hero_line_index = None
            hero_color = None
            hero_tool = comp.FindTool("HeroText")
            if hero_tool:
                base_lines = styled_text.split("\n")
                hero_lines = str(hero_tool.GetInput("StyledText") or "").split("\n")
                line_count = max(len(base_lines), len(hero_lines))
                merged_lines = []
                for line_index in range(line_count):
                    base_line = base_lines[line_index] if line_index < len(base_lines) else ""
                    hero_line = hero_lines[line_index] if line_index < len(hero_lines) else ""
                    if hero_line.strip():
                        hero_line_index = line_index
                        merged_lines.append(hero_line)
                    else:
                        merged_lines.append(base_line)
                styled_text = "\n".join(merged_lines)
                try:
                    hero_color = [
                        float(hero_tool.GetInput("Red1") if hero_tool.GetInput("Red1") is not None else 1.0),
                        float(hero_tool.GetInput("Green1") if hero_tool.GetInput("Green1") is not None else 1.0),
                        float(hero_tool.GetInput("Blue1") if hero_tool.GetInput("Blue1") is not None else 1.0),
                    ]
                except Exception:
                    hero_color = None
            font_family = str(tpl.GetInput("Font") or "Arial")
            font_size = float(tpl.GetInput("Size") or 0.08)
            center = tpl.GetInput("Center") or [0.5, 0.28]
            if isinstance(center, dict):
                cx = float(center.get(1, center.get("1", center.get(0, 0.5))))
                cy = float(center.get(2, center.get("2", center.get(1, 0.28))))
            elif isinstance(center, (list, tuple)):
                cx = float(center[0]) if len(center) > 0 else 0.5
                cy = float(center[1]) if len(center) > 1 else 0.28
            else:
                cx, cy = 0.5, 0.28

            r = float(tpl.GetInput("Red1") if tpl.GetInput("Red1") is not None else 1.0)
            g = float(tpl.GetInput("Green1") if tpl.GetInput("Green1") is not None else 1.0)
            b = float(tpl.GetInput("Blue1") if tpl.GetInput("Blue1") is not None else 1.0)
            a = float(tpl.GetInput("Alpha1") if tpl.GetInput("Alpha1") is not None else 1.0)

            en4 = tpl.GetInput("Enabled4")
            box_enabled = bool(en4 and float(en4) > 0.0)
            box_color = [1.0, 0.88, 0.0, 0.95]
            if box_enabled:
                br = float(tpl.GetInput("Red4") if tpl.GetInput("Red4") is not None else 1.0)
                bg = float(tpl.GetInput("Green4") if tpl.GetInput("Green4") is not None else 0.88)
                bb = float(tpl.GetInput("Blue4") if tpl.GetInput("Blue4") is not None else 0.0)
                box_color = [br, bg, bb, 0.95]

            h_anchor = float(tpl.GetInput("HorizontalLeftCenterRight") if tpl.GetInput("HorizontalLeftCenterRight") is not None else 0.0)
            h_just = float(tpl.GetInput("HorizontalJustificationNew") if tpl.GetInput("HorizontalJustificationNew") is not None else 1.0)
            alignment = "center"
            if h_anchor <= -0.5 or h_just == 0.0:
                alignment = "left"
            elif h_anchor >= 0.5 or h_just == 2.0:
                alignment = "right"

            return {
                "item": text_item,
                "text": styled_text,
                "hero_line_index": hero_line_index,
                "hero_color": hero_color,
                "font": font_family,
                "size": font_size,
                "center_x": cx,
                "center_y": cy,
                "alignment": alignment,
                "color": [r, g, b, a],
                "box_enabled": box_enabled,
                "box_color": box_color,
                "track": active_track,
                "start": text_item.GetStart(),
                "end": text_item.GetEnd()
            }
        except Exception as e:
            return None

    def get_first_selected_text_plus(self):
        """Return the first selected clip that is a Text+ title, or None."""
        selected = self.get_selected_video_items()
        for item in selected:
            if item.GetFusionCompCount() > 0:
                comp = item.GetFusionCompByIndex(1)
                if comp and comp.FindTool("Template"):
                    return item
        return None

    def insert_text_plus_title(self, start_frame=None, end_frame=None, snap_to_footage=False):
        """
        Insert a Text+ Fusion Title into the active timeline with collision avoidance.
        If snap_to_footage is True, snaps duration to the underlying Track 1 clip.
        """
        tl = self.get_current_timeline()
        if not tl:
            return None
        try:
            if self.resolve:
                self.resolve.OpenPage("edit")

            fps = self.get_timeline_fps() or 30.0
            playhead = self.get_playhead_frame()

            from core.timeline_intelligence import TimelineIntelligence

            if snap_to_footage:
                snapped = TimelineIntelligence.detect_magnetic_snap_bounds(tl, playhead)
                if snapped:
                    start_frame, end_frame = snapped

            if start_frame is None or end_frame is None:
                start_frame = playhead
                end_frame = start_frame + int(round(3.0 * fps))

            # Smart track target to ensure track exists and avoid collision (Never touch Track 1 footage)
            target_track = TimelineIntelligence.find_best_title_track(tl, start_frame, end_frame)
            if target_track < 2:
                target_track = 2

            curr_tracks = tl.GetTrackCount("video") if hasattr(tl, "GetTrackCount") else 1
            while curr_tracks < target_track and hasattr(tl, "AddTrack"):
                tl.AddTrack("video")
                curr_tracks = tl.GetTrackCount("video")

            try:
                tl.SetMarkInOut(int(start_frame), int(end_frame))
                item = tl.InsertFusionTitleIntoTimeline("Text+")
                tl.ClearMarkInOut()

                if item:
                    track_info = item.GetTrackTypeAndIndex() if hasattr(item, "GetTrackTypeAndIndex") else None
                    actual_track = track_info[1] if track_info and len(track_info) > 1 else None
                    if actual_track != target_track and hasattr(tl, "MoveItems"):
                        try:
                            tl.MoveItems([item], {"trackIndex": int(target_track), "startFrame": float(start_frame)})
                        except Exception as move_err:
                            print(f"[ResolveAPI] Note on moving item to Track V{target_track}: {move_err}")
            except Exception as insert_err:
                print(f"[ResolveAPI] Insert error: {insert_err}")
                item = None

            return item
        except Exception as e:
            print(f"[ResolveAPI] Error inserting title: {e}")
            return None

    def push_undo_snapshot(self, created_items, operation_name="Batch Operation", track_index=None, recreate_data=None):
        """Record an operation snapshot for one-click undo."""
        self._undo_history.append({
            "type": "create",
            "name": operation_name,
            "items": created_items,
            "track_index": track_index,
            "recreate_data": recreate_data
        })
        self._clear_fusion_snapshots(self._redo_history)
        self._redo_history.clear()

    def push_modify_snapshot(self, records, operation_name="Modify Title"):
        """
        Record a style/text modification snapshot for undo/redo.
        records: list of dicts with keys 'item', 'prev_style', 'new_style'.
        """
        self._undo_history.append({
            "type": "modify",
            "name": operation_name,
            "records": records
        })
        self._clear_fusion_snapshots(self._redo_history)
        self._redo_history.clear()

    def capture_fusion_comp_snapshot(self, timeline_item, comp_index=1):
        """Export one Fusion comp to a temporary .comp file for safe undo."""
        if not timeline_item or not hasattr(timeline_item, "ExportFusionComp"):
            return None
        try:
            comp_names = timeline_item.GetFusionCompNameList() or []
            if comp_index < 1 or comp_index > len(comp_names):
                return None
            folder = tempfile.mkdtemp(prefix="motion-resolve-undo-")
            path = os.path.join(folder, f"fusion-{comp_index}.comp")
            if not timeline_item.ExportFusionComp(path, comp_index):
                self._remove_snapshot_path(path)
                return None
            return {"path": path, "comp_name": comp_names[comp_index - 1], "comp_index": comp_index}
        except Exception as exc:
            print(f"[ResolveAPI] Could not export Fusion undo snapshot: {exc}")
            return None

    def restore_fusion_comp_snapshot(self, timeline_item, snapshot):
        """Restore a saved Fusion comp while leaving other comp slots intact."""
        if not timeline_item or not snapshot or not os.path.isfile(snapshot.get("path", "")):
            return False
        required = ("ImportFusionComp", "GetFusionCompNameList", "DeleteFusionCompByName",
                    "LoadFusionCompByName", "RenameFusionCompByName")
        if not all(hasattr(timeline_item, name) for name in required):
            return False

        original_name = snapshot.get("comp_name")
        try:
            names_before = list(timeline_item.GetFusionCompNameList() or [])
            if original_name not in names_before:
                return False
            imported = timeline_item.ImportFusionComp(snapshot["path"])
            if not imported:
                return False
            names_after = list(timeline_item.GetFusionCompNameList() or [])
            added_names = [name for name in names_after if name not in names_before]
            imported_name = added_names[-1] if added_names else None
            if not imported_name or not timeline_item.LoadFusionCompByName(imported_name):
                if imported_name:
                    timeline_item.DeleteFusionCompByName(imported_name)
                return False

            if not timeline_item.DeleteFusionCompByName(original_name):
                timeline_item.LoadFusionCompByName(original_name)
                timeline_item.DeleteFusionCompByName(imported_name)
                return False

            final_name = original_name
            if not timeline_item.RenameFusionCompByName(imported_name, original_name):
                final_name = imported_name
            timeline_item.LoadFusionCompByName(final_name)
            return True
        except Exception as exc:
            print(f"[ResolveAPI] Could not restore Fusion comp snapshot: {exc}")
            return False

    @staticmethod
    def _remove_snapshot_path(snapshot_path):
        if not snapshot_path:
            return
        folder = os.path.dirname(snapshot_path)
        try:
            if os.path.isfile(snapshot_path):
                os.remove(snapshot_path)
            if folder and os.path.isdir(folder) and not os.listdir(folder):
                os.rmdir(folder)
        except OSError:
            pass

    @classmethod
    def discard_fusion_comp_snapshot(cls, snapshot):
        if snapshot:
            cls._remove_snapshot_path(snapshot.get("path"))

    @classmethod
    def _clear_fusion_snapshots(cls, history):
        for operation in history or []:
            for record in operation.get("records", []):
                for key in ("before", "after"):
                    snapshot = record.get(key) or {}
                    cls._remove_snapshot_path(snapshot.get("path"))

    def _cleanup_snapshot_files(self):
        self._clear_fusion_snapshots(self._undo_history)
        self._clear_fusion_snapshots(self._redo_history)

    def push_fusion_snapshot(self, records, operation_name="Apply Template"):
        """Record full before/after Fusion exports for template apply undo/redo."""
        self._clear_fusion_snapshots(self._redo_history)
        self._redo_history.clear()
        self._undo_history.append({"type": "fusion", "name": operation_name, "records": records})

    def can_undo(self) -> bool:
        return len(self._undo_history) > 0

    def can_redo(self) -> bool:
        if not self._redo_history:
            return False
        # Redo is truthful: only enabled if the undone operation can actually be recreated/restored
        return self._redo_history[-1].get("type") in ("modify", "fusion")

    def undo_last_batch(self):
        """Undo the most recent create or modify batch operation."""
        if not self._undo_history:
            return False, "No operations in undo history."

        last_op = self._undo_history[-1]
        op_type = last_op.get("type", "create")

        if op_type == "fusion":
            restored = []
            for rec in last_op.get("records", []):
                if self.restore_fusion_comp_snapshot(rec.get("item"), rec.get("before")):
                    restored.append(rec)
                else:
                    for applied in reversed(restored):
                        self.restore_fusion_comp_snapshot(applied.get("item"), applied.get("after"))
                    return False, f"Could not restore every Fusion comp for {last_op.get('name')}; the operation remains in undo history."
            self._undo_history.pop()
            self._redo_history.append(last_op)
            return True, f"Undid {last_op.get('name')}: restored {len(restored)} Fusion composition(s)."

        if op_type == "modify":
            records = last_op.get("records", [])
            from core.text_plus_builder import TextPlusBuilder
            builder = TextPlusBuilder()
            restored = 0
            for rec in records:
                item = rec.get("item")
                prev_style = rec.get("prev_style")
                if item and prev_style:
                    try:
                        builder.apply_style(item, prev_style, text_override=prev_style.get("text"))
                        restored += 1
                    except Exception as e:
                        print(f"[ResolveAPI] Error restoring style on undo: {e}")
            self._undo_history.pop()
            self._redo_history.append(last_op)
            return True, f"Undid {last_op.get('name')}: restored previous style for {restored} titles."

        items = last_op.get("items", [])
        track_idx = last_op.get("track_index")
        tl = self.get_current_timeline()
        if tl and items:
            try:
                if not tl.DeleteClips(items):
                    return False, f"Resolve could not undo {last_op.get('name', 'operation')}."
                track_deleted = False
                if track_idx is not None:
                    try:
                        num_tracks = tl.GetTrackCount("video")
                        if track_idx <= num_tracks:
                            remaining = tl.GetItemListInTrack("video", track_idx) or []
                            if len(remaining) == 0:
                                tl.DeleteTrack("video", track_idx)
                                track_deleted = True
                    except Exception:
                        pass

                self._undo_history.pop()
                self._redo_history.append(last_op)

                msg = f"Undid {last_op.get('name')}: removed {len(items)} clips"
                if track_deleted:
                    msg += f" and empty video track {track_idx}."
                else:
                    msg += "."
                return True, msg
            except Exception as e:
                return False, f"Failed to undo: {e}"
        return False, "No clips to undo."

    def redo_last_batch(self):
        """Redo the most recent undone modification."""
        if not self._redo_history:
            return False, "No operations in redo history."

        last_op = self._redo_history[-1]
        op_type = last_op.get("type", "create")

        if op_type == "fusion":
            restored = []
            for rec in last_op.get("records", []):
                if self.restore_fusion_comp_snapshot(rec.get("item"), rec.get("after")):
                    restored.append(rec)
                else:
                    for applied in reversed(restored):
                        self.restore_fusion_comp_snapshot(applied.get("item"), applied.get("before"))
                    return False, f"Could not restore every Fusion comp for {last_op.get('name')}; the operation remains in redo history."
            self._redo_history.pop()
            self._undo_history.append(last_op)
            return True, f"Redid {last_op.get('name')}: restored {len(restored)} Fusion composition(s)."

        if op_type == "modify":
            records = last_op.get("records", [])
            from core.text_plus_builder import TextPlusBuilder
            builder = TextPlusBuilder()
            reapplied = 0
            for rec in records:
                item = rec.get("item")
                new_style = rec.get("new_style")
                if item and new_style:
                    try:
                        builder.apply_style(item, new_style, text_override=new_style.get("text"))
                        reapplied += 1
                    except Exception as e:
                        print(f"[ResolveAPI] Error reapplying style on redo: {e}")
            self._redo_history.pop()
            self._undo_history.append(last_op)
            return True, f"Redid {last_op.get('name')}: reapplied style for {reapplied} titles."

        return False, "Redo is unavailable for clip creations: Resolve scripting cannot recreate deleted timeline clips."

    @staticmethod
    def timecode_to_frames(timecode_str, fps=30.0):
        try:
            fps_val = float(fps) if fps else 30.0
            parts = [int(p) for p in str(timecode_str).replace(";", ":").split(":")]
            if len(parts) == 4:
                h, m, s, f = parts
                total_sec = h * 3600 + m * 60 + s
                return int(round(total_sec * round(fps_val))) + f
            elif len(parts) == 3:
                h, m, s = parts
                total_sec = h * 3600 + m * 60 + s
                return int(round(total_sec * round(fps_val)))
        except Exception:
            pass
        return 0

    @staticmethod
    def frames_to_timecode(total_frames, fps=30.0):
        try:
            total_frames = max(0, int(total_frames))
            f = int(total_frames % round(fps))
            total_seconds = int(total_frames // round(fps))
            s = total_seconds % 60
            m = (total_seconds // 60) % 60
            h = total_seconds // 3600
            return f"{h:02d}:{m:02d}:{s:02d}:{f:02d}"
        except Exception:
            return "01:00:00:00"
