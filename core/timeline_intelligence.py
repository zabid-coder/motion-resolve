"""
Motion Resolve - Timeline Intelligence & Magnetic Snapping Engine
Protects existing A-roll footage, prevents collision, detects edit points, and enforces safe zones.
"""
from typing import Tuple, Optional, Any


class TimelineIntelligence:
    @staticmethod
    def find_best_title_track(timeline: Any, start_frame: int, end_frame: int) -> int:
        """
        Determines the optimal video track for inserting a title or caption.
        Guarantees:
        1. Never places title on Track 1 if Track 1 has video clips intersecting [start_frame, end_frame].
        2. Inspects tracks from Track 2 up for zero clip overlap.
        3. Prioritizes tracks named 'Captions' or 'Motion Titles' if they have space.
        4. If all existing tracks are occupied, calls timeline.AddTrack("video") and returns the new top track.
        """
        if not timeline:
            return 1

        num_tracks = 0
        if hasattr(timeline, "GetTrackCount"):
            try:
                num_tracks = timeline.GetTrackCount("video") or 0
            except Exception:
                num_tracks = 0

        if num_tracks <= 0:
            if hasattr(timeline, "AddTrack") and timeline.AddTrack("video"):
                return 1
            return 1

        st = int(start_frame)
        end = int(end_frame)
        if end <= st:
            end = st + 1

        # Check existing tracks from Track 2 up (Track 1 is reserved for footage)
        available_tracks = []
        prioritized_track = None

        for tr in range(2, num_tracks + 1):
            items = []
            if hasattr(timeline, "GetItemListInTrack"):
                try:
                    items = timeline.GetItemListInTrack("video", tr) or []
                except Exception:
                    items = []

            collision = False
            for it in items:
                try:
                    clip_start = it.GetStart()
                    clip_end = it.GetEnd()
                    if clip_start < end and clip_end > st:
                        collision = True
                        break
                except Exception:
                    continue

            if not collision:
                available_tracks.append(tr)
                # Check track name priority ("Captions" or "Motion Titles")
                if prioritized_track is None and hasattr(timeline, "GetTrackName"):
                    try:
                        tname = timeline.GetTrackName("video", tr)
                        if isinstance(tname, str) and tname.strip().lower() in ("captions", "motion titles"):
                            prioritized_track = tr
                    except Exception:
                        pass

        if prioritized_track is not None:
            return prioritized_track

        if available_tracks:
            return available_tracks[0]

        # Check Track 1 only if Track 1 itself has no footage in this range and is the only track
        items_1 = []
        if hasattr(timeline, "GetItemListInTrack"):
            try:
                items_1 = timeline.GetItemListInTrack("video", 1) or []
            except Exception:
                items_1 = []

        track_1_collision = False
        for it in items_1:
            try:
                clip_start = it.GetStart()
                clip_end = it.GetEnd()
                if clip_start < end and clip_end > st:
                    track_1_collision = True
                    break
            except Exception:
                continue

        if not track_1_collision and num_tracks == 1:
            return 1

        # All tracks occupied: add a new dedicated top video track
        if hasattr(timeline, "AddTrack") and timeline.AddTrack("video"):
            updated_count = None
            if hasattr(timeline, "GetTrackCount"):
                try:
                    updated_count = timeline.GetTrackCount("video")
                except Exception:
                    pass
            if updated_count and updated_count > num_tracks:
                return updated_count
            return num_tracks + 1

        return max(1, num_tracks)

    @staticmethod
    def detect_magnetic_snap_bounds(timeline: Any, playhead_frame: int) -> Optional[Tuple[int, int]]:
        """
        Inspects Track 1 clips to find the clip under playhead_frame and snaps to its cut boundaries.
        Returns (start_frame, end_frame) or None.
        """
        if not timeline:
            return None
        items = []
        if hasattr(timeline, "GetItemListInTrack"):
            try:
                items = timeline.GetItemListInTrack("video", 1) or []
            except Exception:
                items = []

        for it in items:
            try:
                st, end = it.GetStart(), it.GetEnd()
                if st <= playhead_frame <= end:
                    return (st, end)
            except Exception:
                continue
        return None

    @staticmethod
    def clamp_safe_zones(norm_x: float, norm_y: float, is_vertical: Any = True, aspect_ratio: Optional[str] = None) -> Tuple[float, float]:
        """
        Clamps normalized coordinates (0.0 to 1.0) into safe action zones:
        - X: [0.14, 0.86]
        - Y: [0.24, 0.88] for 9:16 vertical (protects against bottom 24% TikTok/Reels UI and top 12% header)
        - Y: [0.10, 0.90] for 16:9 horizontal
        """
        cx = max(0.14, min(0.86, float(norm_x)))
        vertical = True
        if isinstance(is_vertical, str):
            vertical = (is_vertical.strip().lower() in ("9:16", "vertical", "portrait", "shorts", "reels", "tiktok"))
        elif isinstance(is_vertical, bool):
            vertical = is_vertical
        elif aspect_ratio is not None:
            vertical = (str(aspect_ratio).strip().lower() in ("9:16", "vertical", "portrait", "shorts", "reels", "tiktok"))

        if vertical:
            cy = max(0.24, min(0.88, float(norm_y)))
        else:
            cy = max(0.10, min(0.90, float(norm_y)))
        return (cx, cy)
