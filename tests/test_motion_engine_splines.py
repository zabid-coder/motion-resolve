import unittest
from core.templates.motion_tokens import evaluate_easing, EasingToken
from core.animation_engine import AnimationEngine

class TestMotionEngineSplines(unittest.TestCase):
    def test_expo_out_smooth_deceleration(self):
        # Starts fast, settles smoothly
        v0 = evaluate_easing("expoOut", 0.0)
        v05 = evaluate_easing("expoOut", 0.5)
        v1 = evaluate_easing("expoOut", 1.0)
        self.assertEqual(v0, 0.0)
        self.assertGreater(v05, 0.85)
        self.assertEqual(v1, 1.0)

    def test_soft_spring_damped_harmonic_settle(self):
        # Overshoots by 4-8% around t=0.3-0.5, settles to 1.0 at t=1.0
        v_mid = evaluate_easing("softSpring", 0.35)
        v_end = evaluate_easing("softSpring", 1.0)
        self.assertGreater(v_mid, 1.01)
        self.assertLessEqual(v_mid, 1.08)
        self.assertEqual(v_end, 1.0)

    def test_animation_engine_bezier_expression_generation(self):
        engine = AnimationEngine()
        expr_in = engine.get_motion_curve_expression("slide_up", phase="in", duration=15, distance=1.0)
        self.assertIn("Point(0.0", expr_in)
        self.assertIn("RenderStart", expr_in)
        # Verify exit expression drives smoothly off-screen
        expr_out = engine.get_motion_curve_expression("slide_down", phase="out", duration=15, distance=1.0)
        self.assertIn("RenderEnd", expr_out)

if __name__ == "__main__":
    unittest.main()
