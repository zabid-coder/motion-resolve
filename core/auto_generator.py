"""
CaptionForge for Resolve - Auto Caption Generator
Handles automated batch creation, single-caption updating, layouts-only vs animated mode,
and timeline snapshot/undo integration.
"""

from core.resolve_api import ResolveBridge
from core.text_plus_builder import TextPlusBuilder
from core.animation_engine import AnimationEngine
from core.subtitle_parser import SubtitleParser, SubtitleCue

class AutoGenerator:
    """Batch generation and live updating of animated caption clips."""

    def __init__(self, bridge=None):
        self.bridge = bridge or ResolveBridge()
        self.builder = TextPlusBuilder(self.bridge)
        self.animator = AnimationEngine()

    def generate_captions(self, cues, style_dict, animation_options=None, layouts_only=False, progress_callback=None, cancel_check=None):
        tl = self.bridge.get_current_timeline()
        if not tl or not cues:
            return []

        resolve = self.bridge.resolve
        if resolve:
            resolve.OpenPage("edit")

        try:
            from PyQt6.QtWidgets import QApplication
            q_app = QApplication.instance()
        except Exception:
            q_app = None

        anim_opts = animation_options or {}
        effect_in = anim_opts.get("in", style_dict.get("animation_in", "bounce_up"))
        effect_out = anim_opts.get("out", style_dict.get("animation_out", "slide_down"))

        # Identify or create dedicated track for captions
        target_track_idx = None
        orig_track_locks = {}
        total = len(cues)
        try:
            num_tracks = tl.GetTrackCount("video") or 0
            if num_tracks > 0:
                top_items = tl.GetItemListInTrack("video", num_tracks) or []
                if len(top_items) > 0:
                    if tl.AddTrack("video"):
                        target_track_idx = tl.GetTrackCount("video")
                    else:
                        print("[AutoGenerator] Error: Top track has existing clips and AddTrack failed.")
                        if progress_callback:
                            progress_callback(0, total, "Error: Could not add a new dedicated video track.")
                        return []
                else:
                    target_track_idx = num_tracks
            else:
                if tl.AddTrack("video"):
                    target_track_idx = 1
                else:
                    if progress_callback:
                        progress_callback(0, total, "Error: Could not create initial video track.")
                    return []

            # Lock other video tracks so Resolve's InsertFusionTitle strictly routes to target track
            if target_track_idx:
                for t in range(1, (tl.GetTrackCount("video") or 0) + 1):
                    if hasattr(tl, "GetIsTrackLocked"):
                        try:
                            orig_track_locks[t] = tl.GetIsTrackLocked("video", t)
                        except Exception:
                            orig_track_locks[t] = False
                    if t != target_track_idx and hasattr(tl, "SetTrackLock"):
                        try:
                            tl.SetTrackLock("video", t, True)
                        except Exception:
                            pass
                if hasattr(tl, "SetTrackLock"):
                    try:
                        tl.SetTrackLock("video", target_track_idx, False)
                    except Exception:
                        pass
        except Exception:
            pass

        if not target_track_idx:
            if progress_callback:
                progress_callback(0, total, "Could not establish a dedicated video track; no captions were inserted.")
            return []

        created_items = []
        placement_failures = 0
        placement_cleanup_failures = 0
        generation_failures = 0
        cancelled = False

        start_tc = tl.GetStartTimecode()
        fps = self.bridge.get_timeline_fps() or 24.0
        start_offset = self.bridge.timecode_to_frames(start_tc, fps)

        try:
            for idx, cue in enumerate(cues):
                if cancel_check and cancel_check():
                    cancelled = True
                    if progress_callback:
                        progress_callback(idx, total, f"Cancelled by user ({idx}/{total} created).")
                    break
                if q_app:
                    q_app.processEvents()

                try:
                    if progress_callback:
                        progress_callback(idx + 1, total, f"Creating title {idx + 1}/{total}: '{cue.text[:18]}...'")

                    start_frame = int(cue.start_frame)
                    end_frame = int(cue.end_frame)
                    if start_offset > 0 and start_frame < start_offset:
                        start_frame += start_offset
                        end_frame += start_offset

                    if end_frame <= start_frame:
                        end_frame = start_frame + 30

                    tl.SetMarkInOut(start_frame, end_frame)
                    item = tl.InsertFusionTitleIntoTimeline("Text+")
                    tl.ClearMarkInOut()

                    if item:
                        # Verify track placement if API supports it
                        try:
                            track_info = item.GetTrackTypeAndIndex()
                            if track_info and len(track_info) > 1 and target_track_idx:
                                actual_track = track_info[1]
                                if actual_track != target_track_idx:
                                    print(f"[AutoGenerator] Note: title placed on track {actual_track} (target was {target_track_idx})")
                                    # Do not style or report a caption on a
                                    # different track than the dedicated one.
                                    # This item was created by this operation,
                                    # so it is safe to remove it on mismatch.
                                    try:
                                        if not tl.DeleteClips([item]):
                                            placement_cleanup_failures += 1
                                    except Exception:
                                        placement_cleanup_failures += 1
                                    placement_failures += 1
                                    continue
                        except Exception:
                            pass

                        # Apply styling & text
                        if not self.builder.apply_style(item, style_dict, text_override=cue.text):
                            tl.DeleteClips([item])
                            generation_failures += 1
                            continue

                        # Apply animations unless layouts_only is True
                        if not layouts_only and (effect_in or effect_out):
                            eff_in_final = effect_in
                            if effect_in == "auto":
                                next_dir = self.animator.get_auto_next_direction(continuity=False)
                                eff_in_final = f"bounce_{next_dir}"

                            motion_ok = self.animator.apply_motion_preset(
                                item,
                                effect_in=eff_in_final if eff_in_final != "off" else None,
                                effect_out=effect_out if effect_out != "off" else None,
                                options=anim_opts
                            )
                            if not motion_ok:
                                tl.DeleteClips([item])
                                generation_failures += 1
                                continue

                        created_items.append(item)
                    else:
                        generation_failures += 1

                except Exception as e:
                    generation_failures += 1
                    print(f"[CaptionForge] Error creating caption #{idx}: {e}")
                    try:
                        tl.ClearMarkInOut()
                    except Exception:
                        pass
        finally:
            # Restore original track lock states
            if orig_track_locks and hasattr(tl, "SetTrackLock"):
                for t, locked in orig_track_locks.items():
                    try:
                        tl.SetTrackLock("video", t, locked)
                    except Exception:
                        pass

        # Save snapshot for undo
        if created_items:
            self.bridge.push_undo_snapshot(created_items, f"Create {len(created_items)} Captions", track_index=target_track_idx)

        if progress_callback:
            if placement_failures:
                cleanup_note = f" {placement_cleanup_failures} misplaced title(s) could not be removed; inspect the timeline." if placement_cleanup_failures else ""
                progress_callback(total, total, f"Stopped: {len(created_items)} captions created on the dedicated track; {placement_failures} title(s) were rejected because Resolve routed them elsewhere.{cleanup_note}")
            elif cancelled:
                progress_callback(total, total, f"Cancelled: {len(created_items)} of {total} captions created.")
            elif generation_failures:
                progress_callback(total, total, f"Finished with errors: {len(created_items)} of {total} captions created; {generation_failures} failed.")
            else:
                progress_callback(total, total, f"Completed: {len(created_items)} captions created on Track {target_track_idx or 1}.")

        return created_items

    def update_active_caption(self, new_text, style_dict=None, anim_opts=None):
        """Update the caption clip currently under the playhead."""
        targets = self.bridge.get_target_clips("playhead")
        if not targets:
            return False, "No caption found under playhead."

        clip = targets[0]
        if clip.GetFusionCompCount() == 0:
            return False, "Selected clip is not a Text+ title."

        if style_dict:
            self.builder.apply_style(clip, style_dict, text_override=new_text)
        else:
            tool = self.builder.get_template_tool(clip)
            if tool:
                tool.SetInput("StyledText", str(new_text))

        if anim_opts:
            eff_in = anim_opts.get("in")
            eff_out = anim_opts.get("out")
            self.animator.apply_motion_preset(clip, effect_in=eff_in, effect_out=eff_out, options=anim_opts)

        return True, "Caption updated successfully!"

    def convert_timeline_subtitles(self, style_dict, track_index=1, words_per_slide=2, remove_punctuation=False, anim_opts=None, layouts_only=False, progress_callback=None, filter_in_out=False):
        tl = self.bridge.get_current_timeline()
        if not tl:
            return []

        raw_cues = SubtitleParser.extract_from_timeline(tl, track_index=track_index)
        if not raw_cues:
            if progress_callback:
                progress_callback(0, 0, "No subtitles found on subtitle track.")
            return []

        # Filter by In/Out range if requested and marked
        if filter_in_out:
            in_out = self.bridge.get_in_out_range()
            if in_out and in_out[1] > in_out[0]:
                in_f, out_f = in_out
                raw_cues = [c for c in raw_cues if c.end_frame >= in_f and c.start_frame <= out_f]
                if not raw_cues:
                    if progress_callback:
                        progress_callback(0, 0, f"No subtitles found within In/Out marks ({in_f}-{out_f}).")
                    return []
            else:
                if progress_callback:
                    progress_callback(0, 0, "Set valid timeline In and Out marks before converting this range.")
                return []

        cues = SubtitleParser.chunk_cues(raw_cues, words_per_slide=words_per_slide, remove_punctuation=remove_punctuation)
        return self.generate_captions(cues, style_dict, animation_options=anim_opts, layouts_only=layouts_only, progress_callback=progress_callback)
