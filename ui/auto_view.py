"""
CaptionForge for Resolve - Auto Captions Tab View
Automated captioning engine with Words-per-slide slider, Punctuation toggle,
Layouts-only vs Animated titles, Timeline Group Plan Preview (with word shifting),
live 'Update Caption', and Animation Customizer with Shake/Flicker intensity sliders.
"""

from core.subtitle_parser import SubtitleParser, SubtitleCue
from core.auto_generator import AutoGenerator

class AutoView:
    """Auto Tab matching Jamie Fenn's tutorial workflow."""

    def __init__(self, ui, bridge, style_manager, auto_generator):
        self.ui = ui
        self.bridge = bridge
        self.style_manager = style_manager
        self.generator = auto_generator
        self.active_style = None
        self.plan_cues = []
        self.selected_group_idx = 0

        presets = self.style_manager.get_presets()
        if presets:
            self.active_style = presets[0]

    def set_active_style(self, style_preset):
        self.active_style = style_preset
        if hasattr(self, "win") and self.win:
            self.win.Find("lbl_active_style_name").Text = f"Active Style: {style_preset.get('name', 'Default')}"

    def get_ui(self):
        ui = self.ui

        # 1. Style Selection Banner
        style_banner = ui.HGroup({"Weight": 0, "Spacing": 6, "Margin": 4}, [
            ui.Label({
                "ID": "lbl_active_style_name",
                "Text": f"Active Style: {self.active_style.get('name', 'Hormozi Bold Yellow') if self.active_style else 'Default'}",
                "Font": ui.Font({"PixelSize": 11, "Bold": True}),
                "Weight": 0.7
            }),
            ui.Button({"ID": "btn_change_style", "Text": "Change ➔", "Weight": 0.3})
        ])

        # 2. Controls Row
        controls_group = ui.VGroup({"Weight": 0, "Spacing": 4, "Margin": 4}, [
            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "Words per slide:", "Weight": 0.32}),
                ui.Slider({"ID": "slider_words_per_slide", "Minimum": 1, "Maximum": 6, "Value": 2, "Weight": 0.48}),
                ui.Label({"ID": "lbl_words_per_slide", "Text": "2 Words", "Weight": 0.20})
            ]),
            ui.HGroup({"Weight": 0}, [
                ui.CheckBox({"ID": "chk_remove_punct", "Text": "Remove Punctuation", "Checked": True, "Weight": 0.5}),
                ui.CheckBox({"ID": "chk_layouts_only", "Text": "Layouts Only (No Anim)", "Checked": False, "Weight": 0.5}),
            ])
        ])

        # 3. Timeline Group Preview Box (Allows previewing & editing words before generation)
        plan_preview_box = ui.VGroup({
            "ID": "card_plan_preview",
            "Weight": 0.55,
            "Spacing": 4,
            "Margin": 6,
            "StyleSheet": "background-color: #171326; border: 1px solid #28213f; border-radius: 10px;"
        }, [
            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "TIMELINE GROUP PLAN PREVIEW", "Font": ui.Font({"PixelSize": 10, "Bold": True}), "Weight": 0.7}),
                ui.Button({"ID": "btn_refresh_plan", "Text": "Sync Subtitles ↻", "Weight": 0.3})
            ]),
            ui.Tree({
                "ID": "tree_plan_groups",
                "Weight": 0.65,
                "ColumnCount": 3,
                "HeaderLabels": ["Group #", "Timing", "Caption Words"]
            }),
            # Word reordering row
            ui.HGroup({"Weight": 0, "Spacing": 4}, [
                ui.Button({"ID": "btn_move_left", "Text": "◄ Shift Left", "Weight": 0.5}),
                ui.Button({"ID": "btn_move_right", "Text": "Shift Right ►", "Weight": 0.5})
            ])
        ])

        # 4. Animation Customization Drawer (Sliders for Shake & Flicker intensity)
        anim_custom_drawer = ui.VGroup({
            "ID": "card_anim_custom",
            "Weight": 0,
            "Spacing": 4,
            "Margin": 4,
            "StyleSheet": "background-color: #151122; border: 1px solid #27213d; border-radius: 8px;"
        }, [
            ui.Label({"Text": "CUSTOMIZE ANIMATIONS (SHAKE & FLICKER)", "Font": ui.Font({"PixelSize": 10, "Bold": True}), "Weight": 0}),
            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "Shake:", "Weight": 0.25}),
                ui.Slider({"ID": "slider_anim_shake", "Minimum": 0, "Maximum": 100, "Value": 0, "Weight": 0.55}),
                ui.Label({"ID": "lbl_anim_shake", "Text": "Off", "Weight": 0.2})
            ]),
            ui.HGroup({"Weight": 0}, [
                ui.Label({"Text": "Flicker:", "Weight": 0.25}),
                ui.Slider({"ID": "slider_anim_flicker", "Minimum": 0, "Maximum": 100, "Value": 0, "Weight": 0.55}),
                ui.Label({"ID": "lbl_anim_flicker", "Text": "Off", "Weight": 0.2})
            ])
        ])

        # 5. Bottom Primary Actions
        action_bar = ui.HGroup({"Weight": 0, "Spacing": 6, "Margin": 6}, [
            ui.Button({"ID": "btn_update_caption", "Text": "Update Caption", "Weight": 0.4}),
            ui.Button({
                "ID": "btn_create_captions",
                "Text": "★ Create Captions",
                "Weight": 0.6,
                "StyleSheet": "background-color: #ff5500; color: #ffffff; border-radius: 8px; font-weight: bold; padding: 7px;"
            })
        ])

        return ui.VGroup({"Weight": 1.0, "Spacing": 4, "Margin": 4}, [
            style_banner,
            controls_group,
            plan_preview_box,
            anim_custom_drawer,
            action_bar
        ])

    def connect_handlers(self, win, switch_to_titles_callback=None, status_callback=None):
        self.win = win
        self.switch_to_titles_cb = switch_to_titles_callback
        self.status_cb = status_callback

        win.On["slider_words_per_slide"].ValueChanged = self.on_words_slider_changed
        win.On["btn_change_style"].Clicked = lambda ev: self.on_change_style_clicked()
        win.On["btn_refresh_plan"].Clicked = lambda ev: self.refresh_plan_preview()
        win.On["btn_create_captions"].Clicked = self.on_create_captions_clicked
        win.On["btn_update_caption"].Clicked = self.on_update_caption_clicked

        # Word shifting
        win.On["btn_move_left"].Clicked = lambda ev: self.shift_word(-1)
        win.On["btn_move_right"].Clicked = lambda ev: self.shift_word(1)

        # Shake & Flicker sliders
        win.On["slider_anim_shake"].ValueChanged = self.on_shake_slider_changed
        win.On["slider_anim_flicker"].ValueChanged = self.on_flicker_slider_changed

        self.refresh_plan_preview()

    def on_words_slider_changed(self, ev):
        val = self.win.Find("slider_words_per_slide").Value
        label = "Full Line" if val >= 6 else f"{val} Words"
        self.win.Find("lbl_words_per_slide").Text = label
        self.refresh_plan_preview()

    def on_shake_slider_changed(self, ev):
        val = self.win.Find("slider_anim_shake").Value
        txt = "Off" if val == 0 else f"{val}%"
        self.win.Find("lbl_anim_shake").Text = txt

    def on_flicker_slider_changed(self, ev):
        val = self.win.Find("slider_anim_flicker").Value
        txt = "Off" if val == 0 else f"{val}%"
        self.win.Find("lbl_anim_flicker").Text = txt

    def on_change_style_clicked(self):
        if self.switch_to_titles_cb:
            self.switch_to_titles_cb()

    def refresh_plan_preview(self):
        tl = self.bridge.get_current_timeline()
        if not tl:
            return

        raw_cues = SubtitleParser.extract_from_timeline(tl, track_index=1)
        words_slider = self.win.Find("slider_words_per_slide").Value
        wps = 0 if words_slider >= 6 else words_slider
        rem_punct = self.win.Find("chk_remove_punct").Checked

        self.plan_cues = SubtitleParser.chunk_cues(raw_cues, words_per_slide=wps, remove_punctuation=rem_punct)

        tree = self.win.Find("tree_plan_groups")
        tree.Clear()

        for idx, cue in enumerate(self.plan_cues[:30]):
            item = tree.NewItem()
            item.Text[0] = f"#{idx + 1}"
            item.Text[1] = f"{cue.start_frame}-{cue.end_frame}"
            item.Text[2] = cue.text
            item.Data = str(idx)
            tree.AddTopLevelItem(item)

    def shift_word(self, direction):
        # Shifts the last word of current group to adjacent group
        tree = self.win.Find("tree_plan_groups")
        current_item = tree.CurrentItem()
        if not current_item or not self.plan_cues:
            return

        try:
            curr_idx = int(current_item.Data)
            target_idx = curr_idx + direction
            if 0 <= target_idx < len(self.plan_cues):
                src_cue = self.plan_cues[curr_idx]
                dst_cue = self.plan_cues[target_idx]
                if src_cue.words:
                    w = src_cue.words.pop(-1 if direction > 0 else 0)
                    if direction > 0:
                        dst_cue.words.insert(0, w)
                    else:
                        dst_cue.words.append(w)
                    src_cue.text = " ".join(src_cue.words)
                    dst_cue.text = " ".join(dst_cue.words)
                    self.refresh_plan_preview()
                    if self.status_cb:
                        self.status_cb(f"Shifted word '{w}' between groups #{curr_idx+1} and #{target_idx+1}")
        except Exception:
            pass

    def get_animation_options(self):
        shake_val = self.win.Find("slider_anim_shake").Value
        flicker_val = self.win.Find("slider_anim_flicker").Value

        return {
            "in": self.active_style.get("animation_in", "bounce_up") if self.active_style else "bounce_up",
            "out": self.active_style.get("animation_out", "slide_down") if self.active_style else "slide_down",
            "shake": shake_val > 0,
            "flicker": flicker_val > 0,
            "motion_blur": True
        }

    def on_create_captions_clicked(self, ev):
        if not self.plan_cues:
            self.refresh_plan_preview()

        if not self.plan_cues:
            if self.status_cb:
                self.status_cb("No subtitles found. Transcribe audio first in Resolve!")
            return

        anim_opts = self.get_animation_options()
        layouts_only = self.win.Find("chk_layouts_only").Checked

        def prog(curr, total, msg):
            if self.status_cb:
                self.status_cb(msg)

        created = self.generator.generate_captions(
            self.plan_cues,
            self.active_style or {},
            animation_options=anim_opts,
            layouts_only=layouts_only,
            progress_callback=prog
        )

        if self.status_cb:
            self.status_cb(f"★ Generated {len(created)} captions on timeline! Tip: Use Playback > Render Cache > Smart if heavy.")

    def on_update_caption_clicked(self, ev):
        tree = self.win.Find("tree_plan_groups")
        current_item = tree.CurrentItem()
        new_text = current_item.Text[2] if current_item else "UPDATED CAPTION"

        anim_opts = self.get_animation_options()
        ok, msg = self.generator.update_active_caption(
            new_text,
            style_dict=self.active_style,
            anim_opts=anim_opts
        )
        if self.status_cb:
            self.status_cb(msg)
