"""
Motion Resolve - Convert Subtitles Dialog
Modal/window for batch converting native DaVinci Resolve subtitles into animated Motion Resolve titles.
"""

from core.subtitle_parser import SubtitleParser

class ConvertDialog:
    """Provides the Subtitle Conversion UI."""

    def __init__(self, ui, bridge, style_manager, auto_generator):
        self.ui = ui
        self.bridge = bridge
        self.style_manager = style_manager
        self.generator = auto_generator

    def get_ui(self):
        ui = self.ui

        presets = self.style_manager.get_presets()
        combo_styles = ui.ComboBox({"ID": "combo_convert_style", "Weight": 0.7})
        for p in presets:
            combo_styles.AddItem(p.get("name", "Untitled"))

        return ui.VGroup({"Weight": 1.0, "Spacing": 8, "Margin": 12}, [
            ui.Label({"Text": "CONVERT SUBTITLES TO MOTION TITLES", "Font": ui.Font({"PixelSize": 13, "Bold": True}), "Weight": 0}),
            ui.Label({"Text": "Converts all cues on the subtitle track into animated Text+ titles.", "Weight": 0}),

            ui.VGap(6),
            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "Style Preset:", "Weight": 0.3}),
                combo_styles
            ]),

            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "Words per slide:", "Weight": 0.3}),
                ui.Slider({"ID": "slider_convert_wps", "Minimum": 1, "Maximum": 5, "Value": 2, "Weight": 0.5}),
                ui.Label({"ID": "lbl_convert_wps", "Text": "2 Words", "Weight": 0.2})
            ]),

            ui.HGroup({"Weight": 0}, [
                ui.CheckBox({"ID": "chk_convert_punct", "Text": "Remove Punctuation", "Checked": True, "Weight": 1.0})
            ]),

            ui.VGap(8),
            ui.Label({"ID": "lbl_convert_progress", "Text": "Ready to convert.", "Weight": 0}),
            ui.VGap(4),

            ui.HGroup({"Weight": 0, "Spacing": 8}, [
                ui.Button({"ID": "btn_convert_execute", "Text": "Convert Now", "Weight": 0.5}),
                ui.Button({"ID": "btn_convert_close", "Text": "Close", "Weight": 0.5})
            ]),
            ui.VGap(0, 1.0)
        ])

    def connect_handlers(self, win, on_complete_callback=None):
        self.win = win
        self.on_complete_cb = on_complete_callback

        win.On["slider_convert_wps"].ValueChanged = self.on_wps_changed
        win.On["btn_convert_execute"].Clicked = self.on_execute_clicked

    def on_wps_changed(self, ev):
        val = self.win.Find("slider_convert_wps").Value
        self.win.Find("lbl_convert_wps").Text = f"{val} Words"

    def on_execute_clicked(self, ev):
        presets = self.style_manager.get_presets()
        idx = self.win.Find("combo_convert_style").CurrentIndex
        chosen_style = presets[idx] if 0 <= idx < len(presets) else (presets[0] if presets else {})

        wps = self.win.Find("slider_convert_wps").Value
        rem_punct = self.win.Find("chk_convert_punct").Checked

        def prog(curr, total, msg):
            self.win.Find("lbl_convert_progress").Text = msg

        created = self.generator.convert_timeline_subtitles(
            chosen_style,
            track_index=1,
            words_per_slide=wps,
            remove_punctuation=rem_punct,
            progress_callback=prog
        )

        if created and self.on_complete_cb:
            self.on_complete_cb(f"Converted {len(created)} subtitles successfully!")
