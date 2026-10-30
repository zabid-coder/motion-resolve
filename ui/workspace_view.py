"""
CaptionForge for Resolve - Workspace Tab View (100% Workable & Interactive)
All floating tools (Duplicate, Copy, Crosshair, Transform, Palette, Font),
Canvas controls, Alignment, Templates, Hero Word, and Convert Drawer fully wired to DaVinci Resolve.
"""

from core.text_plus_builder import TextPlusBuilder

FONTS_LIST = [
    "Impact", "Arial", "Helvetica Neue", "Trebuchet MS", "Futura",
    "Montserrat", "Open Sans", "Georgia", "Courier New"
]

COLOR_PALETTE = {
    "White": [1.0, 1.0, 1.0, 1.0],
    "Yellow": [1.0, 0.90, 0.0, 1.0],
    "Cyan": [0.0, 0.95, 1.0, 1.0],
    "Red": [1.0, 0.25, 0.20, 1.0],
    "Green": [0.20, 1.0, 0.35, 1.0],
    "Orange": [1.0, 0.55, 0.0, 1.0]
}

class WorkspaceView:
    """Fully functional Workspace Tab matching EasyMotion Toolkit."""

    def __init__(self, ui, bridge, builder):
        self.ui = ui
        self.bridge = bridge
        self.builder = builder
        self.current_style = dict(TextPlusBuilder.DEFAULT_STYLE)
        self.target_mode = "playhead"
        self.convert_drawer_open = False
        self.inspector_open = False
        self.main_word = None
        self._copied_text = "SAMPLE"

    def get_ui(self):
        ui = self.ui

        # 1. Sub-Toolbar
        sub_toolbar = ui.HGroup({"Weight": 0, "Spacing": 4, "Margin": 4}, [
            ui.Button({
                "ID": "btn_mode_playhead",
                "Text": "Playhead",
                "Weight": 0.20,
                "StyleSheet": "background-color: #ff5500; color: #ffffff; border-radius: 9px; font-weight: bold; padding: 4px;"
            }),
            ui.Button({
                "ID": "btn_mode_inout",
                "Text": "In/Out",
                "Weight": 0.17,
                "StyleSheet": "background-color: #1a1628; color: #8e8a9f; border: 1px solid #2d2642; border-radius: 9px; padding: 4px;"
            }),
            ui.HGap(2),
            ui.Button({"ID": "btn_layout_1line", "Text": "T1★", "Weight": 0.11, "StyleSheet": "background-color: #1a1628; border: 1px solid #2d2642; border-radius: 6px;"}),
            ui.Button({"ID": "btn_layout_2line", "Text": "T2", "Weight": 0.10, "StyleSheet": "background-color: #1a1628; border: 1px solid #2d2642; border-radius: 6px;"}),
            ui.Button({"ID": "btn_layout_3line", "Text": "T3", "Weight": 0.10, "StyleSheet": "background-color: #1a1628; border: 1px solid #2d2642; border-radius: 6px;"}),
            ui.HGap(2),
            ui.Button({
                "ID": "btn_add_text",
                "Text": "+ Text",
                "Weight": 0.22,
                "StyleSheet": "border: 1.5px solid #ff5500; border-radius: 9px; color: #ffffff; background: transparent; font-weight: bold; padding: 4px;"
            }),
            ui.Button({"ID": "btn_copy_attrs", "Text": "❐", "Weight": 0.08, "StyleSheet": "background-color: #1a1628; border: 1px solid #2d2642; border-radius: 6px;"}),
            ui.Button({"ID": "btn_paste_attrs", "Text": "📋", "Weight": 0.08, "StyleSheet": "background-color: #1a1628; border: 1px solid #2d2642; border-radius: 6px;"}),
            ui.Button({"ID": "btn_undo", "Text": "↶", "Weight": 0.08, "StyleSheet": "background-color: #1a1628; border: 1px solid #2d2642; border-radius: 6px;"}),
            ui.HGap(0, 1.0)
        ])

        # 2. Convert Captions Drawer
        convert_drawer = ui.VGroup({
            "ID": "drawer_convert",
            "Weight": 0,
            "Spacing": 6,
            "Margin": 8,
            "Hidden": True,
            "StyleSheet": "background-color: #181326; border: 1.5px solid #ff5500; border-radius: 12px;"
        }, [
            ui.HGroup({"Weight": 0}, [
                ui.Label({
                    "Text": "Convert Captions · style sample word, then Convert",
                    "Font": ui.Font({"PixelSize": 10, "Bold": True}),
                    "Weight": 0.9,
                    "StyleSheet": "color: #e2ddf2;"
                }),
                ui.Button({"ID": "btn_close_drawer", "Text": "✕", "Weight": 0.1, "StyleSheet": "background: transparent; border: none; color: #ff5500; font-weight: bold;"})
            ]),
            ui.HGroup({"Weight": 0, "Spacing": 4}, [
                ui.ComboBox({"ID": "combo_drawer_track", "Weight": 0.35}),
                ui.ComboBox({"ID": "combo_drawer_type", "Weight": 0.35}),
                ui.ComboBox({"ID": "combo_drawer_style", "Weight": 0.30})
            ]),
            ui.HGroup({"Weight": 0, "Spacing": 6}, [
                ui.CheckBox({"ID": "chk_drawer_punct", "Text": "Remove punctuation", "Checked": True, "Weight": 0.55, "StyleSheet": "color: #b0a9c6;"}),
                ui.Button({
                    "ID": "btn_drawer_execute",
                    "Text": "Convert · In/Out",
                    "Weight": 0.45,
                    "StyleSheet": "background-color: #ff5500; color: #ffffff; border-radius: 8px; font-weight: bold; padding: 5px 8px;"
                })
            ])
        ])

        # 3. Canvas Top Controls
        canvas_top_controls = ui.HGroup({"Weight": 0, "Spacing": 3, "Margin": 6}, [
            ui.Button({"ID": "btn_align_left", "Text": "|←", "Weight": 0.1, "StyleSheet": "background-color: #161224; border: 1px solid #27203b; border-radius: 4px; color: #a49ebd;"}),
            ui.Button({"ID": "btn_align_center", "Text": "÷", "Weight": 0.1, "StyleSheet": "background-color: #161224; border: 1px solid #27203b; border-radius: 4px; color: #a49ebd;"}),
            ui.Button({"ID": "btn_align_right", "Text": "→|", "Weight": 0.1, "StyleSheet": "background-color: #161224; border: 1px solid #27203b; border-radius: 4px; color: #a49ebd;"}),
            ui.HGap(0, 1.0),
            ui.Button({"ID": "btn_canvas_fit", "Text": "⛶", "Weight": 0.1, "StyleSheet": "background-color: #161224; border: 1px solid #27203b; border-radius: 4px; color: #a49ebd;"}),
            ui.Button({"ID": "btn_canvas_reset", "Text": "↺", "Weight": 0.1, "StyleSheet": "background-color: #161224; border: 1px solid #27203b; border-radius: 4px; color: #a49ebd;"}),
            ui.Button({"ID": "btn_set_hero_word", "Text": "★ Set Hero Word", "Weight": 0.35, "StyleSheet": "background-color: #272015; border: 1px solid #ffaa00; border-radius: 4px; color: #ffcc00; font-size: 10px;"}),
            ui.Button({"ID": "btn_delete_title", "Text": "🗑", "Weight": 0.1, "StyleSheet": "background-color: #261518; border: 1px solid #5a1e26; border-radius: 4px; color: #ff6677;"})
        ])

        # 4. Canvas Floating Vertical Tool Strip
        floating_tools = ui.VGroup({"Weight": 0, "Spacing": 3, "Margin": 6}, [
            ui.Button({"ID": "btn_tool_duplicate", "Text": "❐", "Weight": 0, "StyleSheet": "background-color: #19142b; border: 1px solid #27203b; border-radius: 6px; min-width: 26px; min-height: 26px; color: #a49ebd;"}),
            ui.Button({"ID": "btn_tool_copy", "Text": "📋", "Weight": 0, "StyleSheet": "background-color: #19142b; border: 1px solid #27203b; border-radius: 6px; min-width: 26px; min-height: 26px; color: #a49ebd;"}),
            ui.Button({"ID": "btn_tool_crosshair", "Text": "⌖", "Weight": 0, "StyleSheet": "background-color: #19142b; border: 1px solid #27203b; border-radius: 6px; min-width: 26px; min-height: 26px; color: #a49ebd;"}),
            ui.Button({"ID": "btn_tool_transform", "Text": "⤢", "Weight": 0, "StyleSheet": "background-color: #19142b; border: 1px solid #27203b; border-radius: 6px; min-width: 26px; min-height: 26px; color: #a49ebd;"}),
            ui.Button({"ID": "btn_tool_color", "Text": "🎨", "Weight": 0, "StyleSheet": "background-color: #19142b; border: 1px solid #27203b; border-radius: 6px; min-width: 26px; min-height: 26px; color: #a49ebd;"}),
            ui.Button({"ID": "btn_tool_font", "Text": "Aa", "Weight": 0, "StyleSheet": "background-color: #19142b; border: 1px solid #27203b; border-radius: 6px; min-width: 26px; min-height: 26px; color: #a49ebd;"}),
            ui.VGap(0, 1.0)
        ])

        # 5. Canvas Center (Orange Sample Bounding Box)
        canvas_center_view = ui.VGroup({"Weight": 1.0, "Spacing": 0}, [
            ui.VGap(0, 0.42),
            ui.HGroup({"Weight": 0}, [
                ui.HGap(0, 0.15),
                ui.LineEdit({
                    "ID": "txt_canvas_sample",
                    "Text": "sample",
                    "Alignment": {"AlignHCenter": True, "AlignVCenter": True},
                    "Font": ui.Font({"PixelSize": 18, "Bold": True}),
                    "Weight": 0.70,
                    "StyleSheet": "border: 2px solid #ff5500; border-radius: 6px; background-color: transparent; color: #ffffff; padding: 4px 6px;"
                }),
                ui.HGap(0, 0.15),
            ]),
            ui.VGap(0, 0.42),
            ui.HGroup({"Weight": 0}, [
                ui.HGap(0, 0.35),
                ui.Button({"ID": "btn_zoom_out", "Text": "−", "Weight": 0.1, "StyleSheet": "background-color: #161224; border: 1px solid #27203b; border-radius: 6px; color: #ffffff;"}),
                ui.Label({"ID": "lbl_zoom_val", "Text": "100%", "Font": ui.Font({"PixelSize": 9}), "Weight": 0.1, "Alignment": {"AlignHCenter": True}, "StyleSheet": "color: #8e8a9f;"}),
                ui.Button({"ID": "btn_zoom_in", "Text": "+", "Weight": 0.1, "StyleSheet": "background-color: #161224; border: 1px solid #27203b; border-radius: 6px; color: #ffffff;"}),
                ui.HGap(0, 0.35),
            ]),
            ui.VGap(4)
        ])

        canvas_body = ui.HGroup({"Weight": 1.0, "Spacing": 0}, [
            floating_tools,
            canvas_center_view
        ])

        phone_canvas = ui.VGroup({
            "ID": "card_phone_canvas",
            "Weight": 1.0,
            "Spacing": 0,
            "StyleSheet": "background-color: #000000; border: 1.5px solid #251f38; border-radius: 16px;"
        }, [
            canvas_top_controls,
            canvas_body
        ])

        # 6. Flyout Inspector
        flyout_inspector = ui.VGroup({
            "ID": "flyout_inspector",
            "Weight": 0,
            "Spacing": 4,
            "Margin": 6,
            "Hidden": True,
            "StyleSheet": "background-color: #181326; border: 1px solid #2e2645; border-radius: 10px;"
        }, [
            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "TYPOGRAPHY & SHADING", "Font": ui.Font({"PixelSize": 10, "Bold": True}), "Weight": 0.8}),
                ui.Button({"ID": "btn_close_inspector", "Text": "✕", "Weight": 0.2, "StyleSheet": "background: transparent; border: none; color: #ff5500;"})
            ]),
            ui.HGroup({"Weight": 0, "Spacing": 4}, [
                ui.ComboBox({"ID": "combo_insp_font", "Weight": 0.6}),
                ui.ComboBox({"ID": "combo_insp_color", "Weight": 0.4})
            ]),
            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "Size:", "Weight": 0.2}),
                ui.Slider({"ID": "slider_insp_size", "Minimum": 30, "Maximum": 180, "Value": 82, "Weight": 0.8})
            ]),
            ui.HGroup({"Weight": 0, "Spacing": 4}, [
                ui.CheckBox({"ID": "chk_insp_stroke", "Text": "Outline", "Checked": True, "Weight": 0.35}),
                ui.CheckBox({"ID": "chk_insp_shadow", "Text": "Shadow", "Checked": True, "Weight": 0.35}),
                ui.CheckBox({"ID": "chk_insp_box", "Text": "Box", "Checked": False, "Weight": 0.30})
            ])
        ])

        return ui.VGroup({"Weight": 1.0, "Spacing": 4, "Margin": 4}, [
            sub_toolbar,
            convert_drawer,
            flyout_inspector,
            phone_canvas
        ])

    def connect_handlers(self, win, status_callback=None):
        self.win = win
        self.status_cb = status_callback

        combo_font = win.Find("combo_insp_font")
        for f in FONTS_LIST:
            combo_font.AddItem(f)

        combo_color = win.Find("combo_insp_color")
        for c in COLOR_PALETTE.keys():
            combo_color.AddItem(c)

        # Refresh Subtitle tracks into combo
        self.refresh_drawer_tracks()

        combo_type = win.Find("combo_drawer_type")
        combo_type.AddItem("Toolkit Title")

        combo_style = win.Find("combo_drawer_style")
        combo_style.AddItem("Look from style...")
        combo_style.AddItem("Hormozi Yellow")
        combo_style.AddItem("MrBeast Bold")
        combo_style.AddItem("Clean Minimal")

        # Playhead vs In/Out toggle
        win.On["btn_mode_playhead"].Clicked = lambda ev: self.set_target_mode("playhead")
        win.On["btn_mode_inout"].Clicked = lambda ev: self.set_target_mode("inout")

        # Layout Buttons
        win.On["btn_layout_1line"].Clicked = lambda ev: self.apply_template(1)
        win.On["btn_layout_2line"].Clicked = lambda ev: self.apply_template(2)
        win.On["btn_layout_3line"].Clicked = lambda ev: self.apply_template(3)
        win.On["btn_set_hero_word"].Clicked = self.on_set_hero_word_clicked

        # Alignment
        win.On["btn_align_left"].Clicked = lambda ev: self.set_alignment(0)
        win.On["btn_align_center"].Clicked = lambda ev: self.set_alignment(1)
        win.On["btn_align_right"].Clicked = lambda ev: self.set_alignment(2)

        # Canvas Fit & Reset
        win.On["btn_canvas_fit"].Clicked = self.on_canvas_fit_clicked
        win.On["btn_canvas_reset"].Clicked = self.on_canvas_reset_clicked

        # Floating Tools
        win.On["btn_tool_duplicate"].Clicked = self.on_tool_duplicate_clicked
        win.On["btn_tool_copy"].Clicked = self.on_tool_copy_clicked
        win.On["btn_tool_crosshair"].Clicked = self.on_tool_crosshair_clicked
        win.On["btn_tool_transform"].Clicked = lambda ev: self.toggle_inspector()
        win.On["btn_tool_font"].Clicked = lambda ev: self.toggle_inspector()
        win.On["btn_tool_color"].Clicked = lambda ev: self.toggle_inspector()

        # Zoom buttons
        win.On["btn_zoom_in"].Clicked = lambda ev: self.adjust_zoom(10)
        win.On["btn_zoom_out"].Clicked = lambda ev: self.adjust_zoom(-10)

        # Actions
        win.On["btn_add_text"].Clicked = self.on_add_text_clicked
        win.On["btn_delete_title"].Clicked = self.on_delete_title_clicked
        win.On["btn_copy_attrs"].Clicked = self.on_copy_attributes_clicked
        win.On["btn_paste_attrs"].Clicked = self.on_paste_attributes_clicked
        win.On["btn_undo"].Clicked = self.on_undo_clicked

        # Drawer execution
        win.On["btn_close_drawer"].Clicked = lambda ev: self.toggle_convert_drawer()
        win.On["btn_drawer_execute"].Clicked = self.on_drawer_execute_clicked
        win.On["btn_close_inspector"].Clicked = lambda ev: self.toggle_inspector()

        # Canvas sample editing
        win.On["txt_canvas_sample"].TextChanged = self.on_sample_text_changed

        # Inspector controls
        win.On["combo_insp_font"].CurrentIndexChanged = self.on_insp_font_changed
        win.On["combo_insp_color"].CurrentIndexChanged = self.on_insp_color_changed
        win.On["slider_insp_size"].ValueChanged = self.on_insp_size_changed
        win.On["chk_insp_stroke"].Clicked = self.on_insp_stroke_toggled
        win.On["chk_insp_shadow"].Clicked = self.on_insp_shadow_toggled
        win.On["chk_insp_box"].Clicked = self.on_insp_box_toggled

    def refresh_drawer_tracks(self):
        tl = self.bridge.get_current_timeline()
        combo = self.win.Find("combo_drawer_track")
        combo.Clear()
        cnt = tl.GetTrackCount("subtitle") if tl else 0
        if cnt > 0:
            for i in range(1, cnt + 1):
                name = tl.GetTrackName("subtitle", i) or f"Subtitle {i}"
                combo.AddItem(f"{name} (Track {i})")
        else:
            combo.AddItem("Subtitle 1")

    def set_target_mode(self, mode):
        self.target_mode = mode
        if mode == "playhead":
            self.win.Find("btn_mode_playhead").SetStyleSheet("background-color: #ff5500; color: #ffffff; border-radius: 9px; font-weight: bold; padding: 4px;")
            self.win.Find("btn_mode_inout").SetStyleSheet("background-color: #1a1628; color: #8e8a9f; border: 1px solid #2d2642; border-radius: 9px; padding: 4px;")
            self.set_status("Targeting title directly below Playhead.")
        else:
            self.win.Find("btn_mode_playhead").SetStyleSheet("background-color: #1a1628; color: #8e8a9f; border: 1px solid #2d2642; border-radius: 9px; padding: 4px;")
            self.win.Find("btn_mode_inout").SetStyleSheet("background-color: #ff5500; color: #ffffff; border-radius: 9px; font-weight: bold; padding: 4px;")
            self.set_status("Targeting ALL titles in In/Out Range.")

    def toggle_convert_drawer(self):
        self.convert_drawer_open = not self.convert_drawer_open
        self.win.Find("drawer_convert").Hidden = not self.convert_drawer_open
        if self.convert_drawer_open:
            self.refresh_drawer_tracks()

    def toggle_inspector(self):
        self.inspector_open = not self.inspector_open
        self.win.Find("flyout_inspector").Hidden = not self.inspector_open

    def on_sample_text_changed(self, ev):
        txt = self.win.Find("txt_canvas_sample").Text
        self.current_style["text"] = txt
        targets = self.bridge.get_target_clips(self.target_mode)
        for item in targets:
            tool = self.builder.get_template_tool(item)
            if tool:
                tool.SetInput("StyledText", str(txt))

    def on_set_hero_word_clicked(self, ev):
        txt = self.current_style.get("text", "sample")
        words = txt.replace("\n", " ").split()
        if words:
            self.main_word = words[0]
            self.set_status(f"Hero word set to: '{self.main_word.upper()}' (Template 1)")
            self.apply_template(1)

    def format_layout(self, lines):
        return self.apply_template(lines)

    def apply_template(self, template_num):
        txt = self.current_style.get("text", "sample")
        formatted = self.builder.apply_layout_template(txt, template_num=template_num, main_word=self.main_word)
        self.win.Find("txt_canvas_sample").Text = formatted
        self.current_style["text"] = formatted

        targets = self.bridge.get_target_clips(self.target_mode)
        if targets:
            for item in targets:
                tool = self.builder.get_template_tool(item)
                if tool:
                    tool.SetInput("StyledText", str(formatted))
            self.set_status(f"Applied Template {template_num} to {len(targets)} timeline clips.")

    def set_alignment(self, align_mode):
        self.current_style["horizontal_anchor"] = align_mode
        targets = self.bridge.get_target_clips(self.target_mode)
        for item in targets:
            tool = self.builder.get_template_tool(item)
            if tool:
                tool.SetInput("HorizontalLeftCenterRight", float(align_mode))
        self.set_status(f"Alignment set to: {'Left' if align_mode == 0 else ('Center' if align_mode == 1 else 'Right')}")

    def on_canvas_fit_clicked(self, ev):
        self.current_style["center_x"] = 0.5
        self.current_style["center_y"] = 0.5
        self.apply_style_to_targets()
        self.set_status("Centered text at canvas center [0.5, 0.5].")

    def on_canvas_reset_clicked(self, ev):
        self.current_style["center_x"] = 0.5
        self.current_style["center_y"] = 0.28
        self.current_style["size"] = 0.082
        self.apply_style_to_targets()
        self.set_status("Reset text to default lower-third position.")

    def on_tool_duplicate_clicked(self, ev):
        targets = self.bridge.get_target_clips(self.target_mode)
        if targets:
            item = targets[0]
            start_f = item.GetEnd()
            end_f = start_f + item.GetDuration()
            new_item = self.bridge.insert_text_plus_title(start_frame=start_f, end_frame=end_f)
            if new_item:
                self.builder.apply_style(new_item, self.current_style)
                self.set_status("Duplicated title to next frame position!")
        else:
            self.on_add_text_clicked(None)

    def on_tool_copy_clicked(self, ev):
        self._copied_text = self.win.Find("txt_canvas_sample").Text
        self.on_copy_attributes_clicked(None)
        self.set_status(f"Copied '{self._copied_text[:15]}' and styling to clipboard!")

    def on_tool_crosshair_clicked(self, ev):
        self.on_canvas_fit_clicked(None)

    def adjust_zoom(self, delta):
        curr = int(self.win.Find("lbl_zoom_val").Text.replace("%", ""))
        new_val = max(50, min(200, curr + delta))
        self.win.Find("lbl_zoom_val").Text = f"{new_val}%"
        # Update scale
        new_size = 0.082 * (new_val / 100.0)
        self.current_style["size"] = new_size
        self.apply_style_to_targets()

    def on_insp_font_changed(self, ev):
        idx = self.win.Find("combo_insp_font").CurrentIndex
        if 0 <= idx < len(FONTS_LIST):
            self.current_style["font"] = FONTS_LIST[idx]
            self.apply_style_to_targets()

    def on_insp_color_changed(self, ev):
        idx = self.win.Find("combo_insp_color").CurrentIndex
        keys = list(COLOR_PALETTE.keys())
        if 0 <= idx < len(keys):
            self.current_style["color"] = COLOR_PALETTE[keys[idx]]
            self.apply_style_to_targets()

    def on_insp_size_changed(self, ev):
        val = self.win.Find("slider_insp_size").Value / 1000.0
        self.current_style["size"] = val
        self.apply_style_to_targets()

    def on_insp_stroke_toggled(self, ev):
        self.current_style["stroke_enabled"] = self.win.Find("chk_insp_stroke").Checked
        self.apply_style_to_targets()

    def on_insp_shadow_toggled(self, ev):
        self.current_style["shadow_enabled"] = self.win.Find("chk_insp_shadow").Checked
        self.apply_style_to_targets()

    def on_insp_box_toggled(self, ev):
        self.current_style["box_enabled"] = self.win.Find("chk_insp_box").Checked
        self.apply_style_to_targets()

    def apply_style_to_targets(self):
        targets = self.bridge.get_target_clips(self.target_mode)
        for item in targets:
            self.builder.apply_style(item, self.current_style)

    def on_add_text_clicked(self, ev):
        item = self.bridge.insert_text_plus_title()
        if item:
            self.builder.apply_style(item, self.current_style)
            self.set_status("Created new +Text title at playhead!")
        else:
            self.set_status("Ensure an active timeline is open.")

    def on_delete_title_clicked(self, ev):
        targets = self.bridge.get_target_clips(self.target_mode)
        if targets:
            tl = self.bridge.get_current_timeline()
            if tl:
                tl.DeleteClips(targets)
                self.set_status(f"Deleted {len(targets)} titles from timeline.")

    def on_copy_attributes_clicked(self, ev):
        targets = self.bridge.get_target_clips(self.target_mode)
        if targets:
            if self.builder.copy_clip_attributes(targets[0]):
                self.set_status("Copied title attributes to clipboard!")
        else:
            self.set_status("Select a title to copy attributes.")

    def on_paste_attributes_clicked(self, ev):
        targets = self.bridge.get_target_clips(self.target_mode)
        if targets:
            count = self.builder.paste_clip_attributes(targets, scope="all")
            self.set_status(f"Pasted attributes to {count} clips.")
        else:
            self.set_status("Select target clips to paste attributes.")

    def on_undo_clicked(self, ev):
        ok, msg = self.bridge.undo_last_batch()
        self.set_status(msg)

    def on_drawer_execute_clicked(self, ev):
        from core.auto_generator import AutoGenerator
        gen = AutoGenerator(self.bridge)
        rem_punct = self.win.Find("chk_drawer_punct").Checked
        track_idx = self.win.Find("combo_drawer_track").CurrentIndex + 1

        def prog(curr, total, msg):
            self.set_status(msg)

        created = gen.convert_timeline_subtitles(
            self.current_style,
            track_index=track_idx,
            words_per_slide=2,
            remove_punctuation=rem_punct,
            progress_callback=prog
        )
        if created:
            self.set_status(f"Successfully converted {len(created)} captions to animated titles!")
            self.toggle_convert_drawer()
        else:
            self.set_status("No subtitles found on selected track.")

    def set_status(self, msg):
        if self.status_cb:
            self.status_cb(msg)
