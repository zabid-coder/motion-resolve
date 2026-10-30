"""
CaptionForge for Resolve - Titles Gallery & Creator Composer
Features visual preset cards, tags/search, '+Add from timeline',
and the Creator/Composer popup for reordering words, setting two-color emphasis,
choosing Template 1 Hero Word, and inserting to timeline.
"""

from core.text_plus_builder import TextPlusBuilder

class TitlesView:
    """Gallery browser and rapid title creator composer matching tutorial workflow."""

    def __init__(self, ui, bridge, style_manager, builder):
        self.ui = ui
        self.bridge = bridge
        self.style_manager = style_manager
        self.builder = builder
        self.selected_preset = None
        self.presets = self.style_manager.get_presets()
        if self.presets:
            self.selected_preset = self.presets[0]

    def get_ui(self):
        ui = self.ui

        top_bar = ui.HGroup({"Weight": 0, "Spacing": 6}, [
            ui.LineEdit({"ID": "txt_preset_search", "PlaceholderText": "Search presets or tags...", "Weight": 0.55}),
            ui.Button({"ID": "btn_add_from_timeline", "Text": "＋ Add From Timeline", "Weight": 0.35, "StyleSheet": "border: 1px solid #ff5500; border-radius: 8px; color: #ff5500;"}),
            ui.Button({"ID": "btn_refresh_presets", "Text": "↻", "Weight": 0.1})
        ])

        preset_list_group = ui.VGroup({"Weight": 0.55, "Spacing": 4}, [
            ui.Label({"Text": "SAVED TITLES LIBRARY", "Font": ui.Font({"PixelSize": 10, "Bold": True}), "Weight": 0}),
            ui.Tree({
                "ID": "tree_presets",
                "Weight": 1.0,
                "ColumnCount": 3,
                "HeaderLabels": ["Title Style", "Category", "Motion"]
            })
        ])

        composer_drawer = ui.VGroup({
            "ID": "card_composer",
            "Weight": 0.45,
            "Spacing": 4,
            "Margin": 6,
            "StyleSheet": "background-color: #171326; border: 1.5px solid #ff5500; border-radius: 12px;"
        }, [
            ui.HGroup({"Weight": 0}, [
                ui.Label({"ID": "lbl_composer_title", "Text": "CREATOR COMPOSER", "Font": ui.Font({"PixelSize": 11, "Bold": True}), "Weight": 0.7, "StyleSheet": "color: #ff5500;"}),
                ui.Button({"ID": "btn_composer_t1", "Text": "T1 (Hero)", "Weight": 0.15}),
                ui.Button({"ID": "btn_composer_t2", "Text": "T2 (2-Line)", "Weight": 0.15}),
            ]),
            ui.LineEdit({
                "ID": "txt_composer_words",
                "Text": "VIRAL ANIMATED TITLE",
                "Weight": 0,
                "StyleSheet": "border: 1px solid #ff5500; border-radius: 6px; padding: 4px; font-weight: bold;"
            }),
            ui.HGroup({"Weight": 0, "Spacing": 4}, [
                ui.Label({"Text": "Hero Word:", "Weight": 0.25}),
                ui.LineEdit({"ID": "txt_composer_hero", "Text": "VIRAL", "Weight": 0.45}),
                ui.Button({"ID": "btn_composer_swap_color", "Text": "2-Color 🎨", "Weight": 0.3})
            ]),
            ui.HGroup({"Weight": 0, "Spacing": 6}, [
                ui.Button({
                    "ID": "btn_composer_insert",
                    "Text": "★ Insert Title into Timeline",
                    "Weight": 0.65,
                    "StyleSheet": "background-color: #ff5500; color: #ffffff; border-radius: 8px; font-weight: bold; padding: 6px;"
                }),
                ui.Button({"ID": "btn_edit_in_auto", "Text": "Edit in Auto ➔", "Weight": 0.35})
            ])
        ])

        return ui.VGroup({"Weight": 1.0, "Spacing": 6, "Margin": 6}, [
            top_bar,
            preset_list_group,
            composer_drawer
        ])

    def connect_handlers(self, win, switch_to_auto_callback=None, status_callback=None):
        self.win = win
        self.switch_to_auto_cb = switch_to_auto_callback
        self.status_cb = status_callback

        self.populate_presets_tree()

        win.On["txt_preset_search"].TextChanged = self.on_search_changed
        win.On["btn_refresh_presets"].Clicked = lambda ev: self.refresh_presets()
        win.On["btn_add_from_timeline"].Clicked = self.on_add_from_timeline_clicked
        win.On["tree_presets"].ItemClicked = self.on_tree_item_clicked

        win.On["btn_composer_t1"].Clicked = lambda ev: self.set_composer_template(1)
        win.On["btn_composer_t2"].Clicked = lambda ev: self.set_composer_template(2)
        win.On["btn_composer_insert"].Clicked = self.on_composer_insert_clicked
        win.On["btn_composer_swap_color"].Clicked = self.on_composer_toggle_two_colors
        win.On["btn_edit_in_auto"].Clicked = self.on_edit_in_auto_clicked

        if self.selected_preset:
            self.load_preset_to_composer(self.selected_preset)

    def populate_presets_tree(self, filter_text=""):
        tree = self.win.Find("tree_presets")
        tree.Clear()

        self.presets = self.style_manager.get_presets()
        for p in self.presets:
            p_name = p.get("name", "Untitled")
            p_cat = p.get("category", "General")
            p_mot = p.get("animation_in", "Bounce")

            if filter_text:
                full_search = f"{p_name} {p_cat}".lower()
                if filter_text.lower() not in full_search:
                    continue

            item = tree.NewItem()
            item.Text[0] = p_name
            item.Text[1] = p_cat
            item.Text[2] = p_mot
            item.Data = p.get("id", "")
            tree.AddTopLevelItem(item)

        if self.presets and not self.selected_preset:
            self.selected_preset = self.presets[0]
            self.load_preset_to_composer(self.selected_preset)

    def load_preset_to_composer(self, preset):
        if not preset or not hasattr(self, "win") or not self.win:
            return
        name = preset.get("name", "Untitled")
        self.win.Find("lbl_composer_title").Text = f"COMPOSER: {name.upper()}"
        txt = preset.get("text", "VIRAL TITLE")
        self.win.Find("txt_composer_words").Text = txt
        words = txt.split()
        if words:
            self.win.Find("txt_composer_hero").Text = words[0]

    def on_tree_item_clicked(self, ev):
        tree = self.win.Find("tree_presets")
        current_item = tree.CurrentItem()
        if current_item:
            preset_id = current_item.Data
            p = self.style_manager.get_preset_by_id(preset_id)
            if p:
                self.selected_preset = p
                self.load_preset_to_composer(p)
                if self.status_cb:
                    self.status_cb(f"Loaded '{p.get('name')}' into Composer!")

    def on_search_changed(self, ev):
        query = self.win.Find("txt_preset_search").Text
        self.populate_presets_tree(filter_text=query)

    def refresh_presets(self):
        self.presets = self.style_manager.get_presets()
        self.populate_presets_tree()
        if self.status_cb:
            self.status_cb(f"Library refreshed ({len(self.presets)} styles available).")

    def set_composer_template(self, t_num):
        words = self.win.Find("txt_composer_words").Text
        hero = self.win.Find("txt_composer_hero").Text
        formatted = self.builder.apply_layout_template(words, template_num=t_num, main_word=hero)
        self.win.Find("txt_composer_words").Text = formatted

    def on_composer_toggle_two_colors(self, ev):
        if self.selected_preset:
            curr = self.selected_preset.get("color", [1.0, 1.0, 1.0, 1.0])
            new_color = [1.0, 0.9, 0.0, 1.0] if (curr[0] == 1.0 and curr[1] == 1.0 and curr[2] == 1.0) else [1.0, 1.0, 1.0, 1.0]
            self.selected_preset["color"] = new_color
            if self.status_cb:
                self.status_cb("Toggled secondary emphasis color!")

    def on_composer_insert_clicked(self, ev):
        txt = self.win.Find("txt_composer_words").Text
        style = dict(self.selected_preset or self.builder.DEFAULT_STYLE)
        style["text"] = txt

        item = self.bridge.insert_text_plus_title()
        if item:
            self.builder.apply_style(item, style)
            eff_in = style.get("animation_in", "bounce_up")
            eff_out = style.get("animation_out", "slide_down")

            # Apply motion continuity
            from core.animation_engine import AnimationEngine
            animator = AnimationEngine()
            animator.apply_motion_preset(item, effect_in=eff_in, effect_out=eff_out)

            if self.status_cb:
                self.status_cb(f"Inserted '{txt[:15]}...' to timeline with continuity animation!")
        else:
            if self.status_cb:
                self.status_cb("Could not insert title. Ensure an active timeline is open.")

    def on_add_from_timeline_clicked(self, ev):
        clip = self.bridge.get_first_selected_text_plus()
        if not clip:
            clips = self.bridge.get_selected_video_items()
            clip = clips[0] if clips else None

        if not clip:
            if self.status_cb:
                self.status_cb("Select a Text+ title on your timeline to save it.")
            return

        extracted = self.builder.extract_style_from_clip(clip)
        if not extracted:
            return

        count = len(self.presets) + 1
        p_id = f"user_preset_{count}"
        extracted["name"] = f"My Preset #{count}"
        extracted["category"] = "Custom Library"
        self.style_manager.save_preset(p_id, extracted)
        self.refresh_presets()
        self.selected_preset = extracted
        self.load_preset_to_composer(extracted)
        if self.status_cb:
            self.status_cb(f"Saved custom title: '{extracted['name']}' into library!")

    def on_edit_in_auto_clicked(self, ev):
        if not self.selected_preset and self.presets:
            self.selected_preset = self.presets[0]
        if self.switch_to_auto_cb and self.selected_preset:
            self.switch_to_auto_cb(self.selected_preset)
