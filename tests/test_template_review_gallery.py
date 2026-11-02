import unittest
import sys
from PyQt6.QtWidgets import QApplication
from ui_qt.tabs.templates_tab import TemplatesTab, get_template_pill_category_key
from core.templates.registry import TemplateRegistry

app = QApplication.instance() or QApplication(sys.argv)

class TestTemplateReviewGallery(unittest.TestCase):
    def test_category_filter_pills_populate(self):
        tab = TemplatesTab()
        categories = [tab.category_button_group.buttons()[i].text() for i in range(len(tab.category_button_group.buttons()))]
        self.assertTrue(any("All" in c for c in categories))
        self.assertTrue(any("Viral Agency" in c for c in categories))
        self.assertTrue(any("SaaS & Tech" in c for c in categories))
        self.assertTrue(any("Cinematic Documentary" in c for c in categories))
        self.assertTrue(any("Minimal Luxury" in c for c in categories))
        self.assertTrue(any("Modern Creator" in c for c in categories))

    def test_canvas_scrub_evaluates_playback_phase(self):
        tab = TemplatesTab()
        # Set scrub to 50%
        tab.slider_scrub.setValue(50)
        self.assertAlmostEqual(tab.canvas_area.playback_phase, 0.5, places=2)

        # Set scrub to 0% and 100%
        tab.slider_scrub.setValue(0)
        self.assertAlmostEqual(tab.canvas_area.playback_phase, 0.0, places=2)
        tab.slider_scrub.setValue(100)
        self.assertAlmostEqual(tab.canvas_area.playback_phase, 1.0, places=2)

    def test_search_filters_template_cards(self):
        tab = TemplatesTab()
        total_cards = len(tab.cards)
        self.assertGreater(total_cards, 0)

        # Filter by keyword
        tab.search_input.setText("slate")
        visible_cards = [card for t, card in tab.cards if not card.isHidden()]
        self.assertGreater(len(visible_cards), 0)
        self.assertLess(len(visible_cards), total_cards)

        # Clear search filter
        tab.search_input.clear()
        visible_after_clear = [card for t, card in tab.cards if not card.isHidden()]
        self.assertEqual(len(visible_after_clear), total_cards)

    def test_category_pill_selection_filters_cards(self):
        tab = TemplatesTab()
        total_cards = len(tab.cards)

        # Click "Viral Agency" pill
        btn_viral = tab.pill_buttons.get("viral_agency")
        self.assertIsNotNone(btn_viral)
        btn_viral.click()

        visible_cards = [card for t, card in tab.cards if not card.isHidden()]
        self.assertGreater(len(visible_cards), 0)
        self.assertLess(len(visible_cards), total_cards)

        # Ensure all visible cards are viral agency
        for t, card in tab.cards:
            if not card.isHidden():
                self.assertEqual(get_template_pill_category_key(t.category), "viral_agency")

    def test_playback_controls_toggle_and_timer(self):
        tab = TemplatesTab()
        self.assertFalse(tab.is_playing)
        self.assertEqual(tab.btn_play.text(), "▶")

        # Toggle play
        tab._toggle_playback()
        self.assertTrue(tab.is_playing)
        self.assertEqual(tab.btn_play.text(), "❚❚")
        self.assertTrue(tab.playback_timer.isActive())

        # Toggle pause
        tab._toggle_playback()
        self.assertFalse(tab.is_playing)
        self.assertEqual(tab.btn_play.text(), "▶")
        self.assertFalse(tab.playback_timer.isActive())

    def test_card_pro_badges_and_quick_apply(self):
        tab = TemplatesTab()
        tpl, card = tab.cards[0]

        # Verify badges and font pairing
        self.assertTrue(hasattr(card, "lbl_font"))
        self.assertTrue(card.lbl_font.text().startswith("Aa "))
        self.assertTrue(hasattr(card, "btn_quick_apply"))

        # Verify quick apply signal
        quick_applied = []
        card.quick_apply.connect(lambda t: quick_applied.append(t))
        card.btn_quick_apply.click()
        self.assertEqual(len(quick_applied), 1)
        self.assertEqual(quick_applied[0].id, tpl.id)

if __name__ == "__main__":
    unittest.main()
