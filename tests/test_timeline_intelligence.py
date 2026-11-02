import unittest
from unittest.mock import MagicMock
from core.timeline_intelligence import TimelineIntelligence
from core.resolve_api import ResolveBridge

class TestTimelineIntelligence(unittest.TestCase):
    def test_never_collides_with_track_1_footage(self):
        mock_tl = MagicMock()
        mock_tl.GetTrackCount.return_value = 2

        # Track 1 has video footage
        clip1 = MagicMock()
        clip1.GetStart.return_value = 100
        clip1.GetEnd.return_value = 300
        mock_tl.GetItemListInTrack.side_effect = lambda track_type, idx: [clip1] if idx == 1 else []

        best_track = TimelineIntelligence.find_best_title_track(mock_tl, 150, 250)
        # Must select Track 2, never Track 1
        self.assertEqual(best_track, 2)

    def test_adds_track_if_all_occupied(self):
        mock_tl = MagicMock()
        mock_tl.GetTrackCount.return_value = 1
        mock_tl.AddTrack.return_value = True

        clip1 = MagicMock()
        clip1.GetStart.return_value = 100
        clip1.GetEnd.return_value = 300
        mock_tl.GetItemListInTrack.return_value = [clip1]

        best_track = TimelineIntelligence.find_best_title_track(mock_tl, 150, 250)
        mock_tl.AddTrack.assert_called_with("video")
        self.assertGreater(best_track, 1)

    def test_magnetic_snap_to_underlying_cut(self):
        mock_tl = MagicMock()
        clip = MagicMock()
        clip.GetStart.return_value = 240
        clip.GetEnd.return_value = 360
        mock_tl.GetTrackCount.return_value = 1
        mock_tl.GetItemListInTrack.return_value = [clip]

        # Playhead is at frame 270 (inside the clip)
        bounds = TimelineIntelligence.detect_magnetic_snap_bounds(mock_tl, 270)
        self.assertEqual(bounds, (240, 360))

    def test_vertical_safe_zone_clamping(self):
        # On 9:16 vertical, bottom 24% is blocked by UI
        cx, cy = TimelineIntelligence.clamp_safe_zones(0.5, 0.15, is_vertical=True)
        self.assertGreaterEqual(cy, 0.24)

    def test_prioritizes_named_title_tracks(self):
        mock_tl = MagicMock()
        mock_tl.GetTrackCount.return_value = 3

        # Track 1 has footage
        clip1 = MagicMock()
        clip1.GetStart.return_value = 100
        clip1.GetEnd.return_value = 300
        mock_tl.GetItemListInTrack.side_effect = lambda track_type, idx: [clip1] if idx == 1 else []
        mock_tl.GetTrackName.side_effect = lambda track_type, idx: "Captions" if idx == 3 else "Video " + str(idx)

        best_track = TimelineIntelligence.find_best_title_track(mock_tl, 150, 250)
        self.assertEqual(best_track, 3)

    def test_resolve_bridge_insert_text_plus_title_magnetic_snap(self):
        bridge = ResolveBridge()
        mock_tl = MagicMock()
        mock_tl.GetTrackCount.return_value = 2

        clip = MagicMock()
        clip.GetStart.return_value = 200
        clip.GetEnd.return_value = 400
        mock_tl.GetItemListInTrack.side_effect = lambda track_type, idx: [clip] if idx == 1 else []

        bridge.get_current_timeline = MagicMock(return_value=mock_tl)
        bridge.get_playhead_frame = MagicMock(return_value=250)
        bridge.get_timeline_fps = MagicMock(return_value=30.0)

        inserted_mock = MagicMock()
        mock_tl.InsertFusionTitleIntoTimeline.return_value = inserted_mock

        result = bridge.insert_text_plus_title(snap_to_footage=True)
        self.assertEqual(result, inserted_mock)
        mock_tl.SetMarkInOut.assert_called_with(200, 400)
        mock_tl.ClearMarkInOut.assert_called_once()

if __name__ == "__main__":
    unittest.main()
