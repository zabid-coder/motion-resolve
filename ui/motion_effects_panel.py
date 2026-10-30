"""
CaptionForge for Resolve - Motion Effects Controller
Renders dual D-pads (IN & OUT), Center Effects grid (Shake, Jitter, Scribble, M. Blur),
sub-row accents, and the prominent AUTO button with active neon-orange visual feedback.
"""

STYLE_ACTIVE_ORANGE = "background-color: #ff5500; color: #ffffff; border: 1px solid #ff7722; font-weight: bold; border-radius: 6px;"
STYLE_INACTIVE = "background-color: #1b162b; color: #8e8a9f; border: 1px solid #27213d; border-radius: 6px;"
STYLE_PILL_ACTIVE = "background-color: #ff5500; color: #ffffff; border-radius: 9px; font-weight: bold; padding: 4px;"
STYLE_PILL_INACTIVE = "background-color: #1a1628; color: #8e8a9f; border: 1px solid #2d2642; border-radius: 9px; padding: 4px;"

class MotionEffectsPanel:
    """Bottom motion animation controller with real-time visual button feedback."""

    def __init__(self, ui, bridge, animator):
        self.ui = ui
        self.bridge = bridge
        self.animator = animator
        self.mode_in = "slide"       # "slide" or "bounce"
        self.mode_out = "slide"      # "slide" or "bounce"
        self.dir_in = "up"           # "up", "down", "left", "right", "pop"
        self.dir_out = "down"        # "up", "down", "left", "right"
        self.shake_enabled = False
        self.jitter_enabled = False
        self.scribble_enabled = False
        self.mblur_enabled = True
        self.flicker_enabled = False
        self.blur_enabled = False

    def get_ui(self):
        ui = self.ui

        # 1. Top Mode Toggles (Left: IN Mode | Right: OUT Mode)
        top_modes_row = ui.HGroup({"Weight": 0, "Spacing": 8, "Margin": 4}, [
            ui.HGroup({"Weight": 0.45, "Spacing": 4}, [
                ui.Button({"ID": "btn_in_mode_slide", "Text": "Slide", "Weight": 0.5, "StyleSheet": STYLE_PILL_ACTIVE}),
                ui.Button({"ID": "btn_in_mode_bounce", "Text": "Bounce", "Weight": 0.5, "StyleSheet": STYLE_PILL_INACTIVE})
            ]),
            ui.HGap(0, 0.1),
            ui.HGroup({"Weight": 0.45, "Spacing": 4}, [
                ui.Button({"ID": "btn_out_mode_slide", "Text": "Slide", "Weight": 0.5, "StyleSheet": STYLE_PILL_ACTIVE}),
                ui.Button({"ID": "btn_out_mode_bounce", "Text": "Bounce", "Weight": 0.5, "StyleSheet": STYLE_PILL_INACTIVE})
            ])
        ])

        # 2. Main Middle Row: Left D-Pad + Center Effects + Right D-Pad
        left_dpad = ui.VGroup({"Weight": 0.32, "Spacing": 2, "Alignment": {"AlignHCenter": True}}, [
            ui.Button({"ID": "btn_dpad_in_up", "Text": "▲", "Weight": 0, "StyleSheet": STYLE_ACTIVE_ORANGE}),
            ui.HGroup({"Weight": 0, "Spacing": 2}, [
                ui.Button({"ID": "btn_dpad_in_left", "Text": "◄", "Weight": 0.33, "StyleSheet": STYLE_INACTIVE}),
                ui.Button({"ID": "btn_dpad_in_center", "Text": "●", "Weight": 0.33, "StyleSheet": STYLE_INACTIVE}),
                ui.Button({"ID": "btn_dpad_in_right", "Text": "►", "Weight": 0.33, "StyleSheet": STYLE_INACTIVE}),
            ]),
            ui.Button({"ID": "btn_dpad_in_down", "Text": "▼", "Weight": 0, "StyleSheet": STYLE_INACTIVE})
        ])

        center_effects = ui.VGroup({"Weight": 0.36, "Spacing": 4}, [
            ui.HGroup({"Weight": 0.5, "Spacing": 4}, [
                ui.Button({"ID": "btn_eff_shake", "Text": "∿ Shake", "Weight": 0.5, "StyleSheet": STYLE_INACTIVE}),
                ui.Button({"ID": "btn_eff_jitter", "Text": "❐ Jitter", "Weight": 0.5, "StyleSheet": STYLE_INACTIVE})
            ]),
            ui.HGroup({"Weight": 0.5, "Spacing": 4}, [
                ui.Button({"ID": "btn_eff_scribble", "Text": "〰 Scribble", "Weight": 0.5, "StyleSheet": STYLE_INACTIVE}),
                ui.Button({"ID": "btn_eff_mblur", "Text": "≡⚬ M. Blur", "Weight": 0.5, "StyleSheet": STYLE_ACTIVE_ORANGE})
            ])
        ])

        right_dpad = ui.VGroup({"Weight": 0.32, "Spacing": 2, "Alignment": {"AlignHCenter": True}}, [
            ui.Button({"ID": "btn_dpad_out_up", "Text": "▲", "Weight": 0, "StyleSheet": STYLE_INACTIVE}),
            ui.HGroup({"Weight": 0, "Spacing": 2}, [
                ui.Button({"ID": "btn_dpad_out_left", "Text": "◄", "Weight": 0.33, "StyleSheet": STYLE_INACTIVE}),
                ui.Button({"ID": "btn_dpad_out_center", "Text": "●", "Weight": 0.33, "StyleSheet": STYLE_INACTIVE}),
                ui.Button({"ID": "btn_dpad_out_right", "Text": "►", "Weight": 0.33, "StyleSheet": STYLE_INACTIVE}),
            ]),
            ui.Button({"ID": "btn_dpad_out_down", "Text": "▼", "Weight": 0, "StyleSheet": STYLE_ACTIVE_ORANGE})
        ])

        middle_row = ui.HGroup({"Weight": 0, "Spacing": 6, "Margin": 4}, [
            left_dpad,
            center_effects,
            right_dpad
        ])

        # 3. Sub-row Accents
        sub_accents = ui.HGroup({"Weight": 0, "Spacing": 8, "Margin": 2}, [
            ui.HGroup({"Weight": 0.45, "Spacing": 3}, [
                ui.Button({"ID": "btn_sub_in_flicker", "Text": "Flicker", "Weight": 0.33, "StyleSheet": STYLE_INACTIVE}),
                ui.Button({"ID": "btn_sub_in_shake", "Text": "Shake", "Weight": 0.33, "StyleSheet": STYLE_INACTIVE}),
                ui.Button({"ID": "btn_sub_in_blur", "Text": "Blur", "Weight": 0.33, "StyleSheet": STYLE_INACTIVE}),
            ]),
            ui.HGap(0, 0.1),
            ui.HGroup({"Weight": 0.45, "Spacing": 3}, [
                ui.Button({"ID": "btn_sub_out_flicker", "Text": "Flicker", "Weight": 0.5, "StyleSheet": STYLE_INACTIVE}),
                ui.Button({"ID": "btn_sub_out_blur", "Text": "Blur", "Weight": 0.5, "StyleSheet": STYLE_INACTIVE}),
            ])
        ])

        # 4. Big AUTO Button
        auto_btn_row = ui.HGroup({"Weight": 0, "Margin": 6}, [
            ui.Button({
                "ID": "btn_big_auto",
                "Text": "AUTO",
                "Font": ui.Font({"PixelSize": 13, "Bold": True}),
                "Weight": 1.0,
                "StyleSheet": "background-color: #1a1426; color: #ffffff; border: 1.5px solid #ff5500; border-radius: 8px; padding: 7px; letter-spacing: 2px;"
            })
        ])

        return ui.VGroup({
            "ID": "card_motion_panel",
            "Weight": 0,
            "Spacing": 4,
            "Margin": 6,
            "StyleSheet": "background-color: #151122; border: 1px solid #251f38; border-radius: 14px;"
        }, [
            top_modes_row,
            middle_row,
            sub_accents,
            auto_btn_row
        ])

    def connect_handlers(self, win, status_callback=None):
        self.win = win
        self.status_cb = status_callback

        # IN Modes
        win.On["btn_in_mode_slide"].Clicked = lambda ev: self.set_in_mode("slide")
        win.On["btn_in_mode_bounce"].Clicked = lambda ev: self.set_in_mode("bounce")

        # OUT Modes
        win.On["btn_out_mode_slide"].Clicked = lambda ev: self.set_out_mode("slide")
        win.On["btn_out_mode_bounce"].Clicked = lambda ev: self.set_out_mode("bounce")

        # Left D-Pad
        win.On["btn_dpad_in_up"].Clicked = lambda ev: self.set_in_dir("up")
        win.On["btn_dpad_in_down"].Clicked = lambda ev: self.set_in_dir("down")
        win.On["btn_dpad_in_left"].Clicked = lambda ev: self.set_in_dir("left")
        win.On["btn_dpad_in_right"].Clicked = lambda ev: self.set_in_dir("right")
        win.On["btn_dpad_in_center"].Clicked = lambda ev: self.set_in_dir("pop")

        # Right D-Pad
        win.On["btn_dpad_out_up"].Clicked = lambda ev: self.set_out_dir("up")
        win.On["btn_dpad_out_down"].Clicked = lambda ev: self.set_out_dir("down")
        win.On["btn_dpad_out_left"].Clicked = lambda ev: self.set_out_dir("left")
        win.On["btn_dpad_out_right"].Clicked = lambda ev: self.set_out_dir("right")
        win.On["btn_dpad_out_center"].Clicked = lambda ev: self.set_out_dir("down")

        # Center Effects
        win.On["btn_eff_shake"].Clicked = lambda ev: self.toggle_center_eff("shake")
        win.On["btn_eff_jitter"].Clicked = lambda ev: self.toggle_center_eff("jitter")
        win.On["btn_eff_scribble"].Clicked = lambda ev: self.toggle_center_eff("scribble")
        win.On["btn_eff_mblur"].Clicked = lambda ev: self.toggle_center_eff("mblur")

        # Sub-accents
        win.On["btn_sub_in_flicker"].Clicked = lambda ev: self.toggle_sub("flicker")
        win.On["btn_sub_in_shake"].Clicked = lambda ev: self.toggle_sub("shake")
        win.On["btn_sub_in_blur"].Clicked = lambda ev: self.toggle_sub("blur")

        # AUTO
        win.On["btn_big_auto"].Clicked = lambda ev: self.apply_auto_motion()

        self.update_button_visuals()

    def update_button_visuals(self):
        if not hasattr(self, "win") or not self.win:
            return

        # IN Mode pills
        self.win.Find("btn_in_mode_slide").SetStyleSheet(STYLE_PILL_ACTIVE if self.mode_in == "slide" else STYLE_PILL_INACTIVE)
        self.win.Find("btn_in_mode_bounce").SetStyleSheet(STYLE_PILL_ACTIVE if self.mode_in == "bounce" else STYLE_PILL_INACTIVE)

        # OUT Mode pills
        self.win.Find("btn_out_mode_slide").SetStyleSheet(STYLE_PILL_ACTIVE if self.mode_out == "slide" else STYLE_PILL_INACTIVE)
        self.win.Find("btn_out_mode_bounce").SetStyleSheet(STYLE_PILL_ACTIVE if self.mode_out == "bounce" else STYLE_PILL_INACTIVE)

        # Left D-Pad
        dpad_in_map = {
            "up": "btn_dpad_in_up",
            "down": "btn_dpad_in_down",
            "left": "btn_dpad_in_left",
            "right": "btn_dpad_in_right",
            "pop": "btn_dpad_in_center"
        }
        for d, btn_id in dpad_in_map.items():
            self.win.Find(btn_id).SetStyleSheet(STYLE_ACTIVE_ORANGE if self.dir_in == d else STYLE_INACTIVE)

        # Right D-Pad
        dpad_out_map = {
            "up": "btn_dpad_out_up",
            "down": "btn_dpad_out_down",
            "left": "btn_dpad_out_left",
            "right": "btn_dpad_out_right"
        }
        for d, btn_id in dpad_out_map.items():
            self.win.Find(btn_id).SetStyleSheet(STYLE_ACTIVE_ORANGE if self.dir_out == d else STYLE_INACTIVE)

        # Center Effects
        self.win.Find("btn_eff_shake").SetStyleSheet(STYLE_ACTIVE_ORANGE if self.shake_enabled else STYLE_INACTIVE)
        self.win.Find("btn_eff_jitter").SetStyleSheet(STYLE_ACTIVE_ORANGE if self.jitter_enabled else STYLE_INACTIVE)
        self.win.Find("btn_eff_scribble").SetStyleSheet(STYLE_ACTIVE_ORANGE if self.scribble_enabled else STYLE_INACTIVE)
        self.win.Find("btn_eff_mblur").SetStyleSheet(STYLE_ACTIVE_ORANGE if self.mblur_enabled else STYLE_INACTIVE)

        # Sub-row
        self.win.Find("btn_sub_in_flicker").SetStyleSheet(STYLE_ACTIVE_ORANGE if self.flicker_enabled else STYLE_INACTIVE)
        self.win.Find("btn_sub_in_shake").SetStyleSheet(STYLE_ACTIVE_ORANGE if self.shake_enabled else STYLE_INACTIVE)
        self.win.Find("btn_sub_in_blur").SetStyleSheet(STYLE_ACTIVE_ORANGE if self.blur_enabled else STYLE_INACTIVE)

    def set_in_mode(self, mode):
        self.mode_in = mode
        self.update_button_visuals()
        self.apply_to_selected()

    def set_out_mode(self, mode):
        self.mode_out = mode
        self.update_button_visuals()
        self.apply_to_selected()

    def set_in_dir(self, direction):
        self.dir_in = direction
        self.update_button_visuals()
        self.apply_to_selected()

    def set_out_dir(self, direction):
        self.dir_out = direction
        self.update_button_visuals()
        self.apply_to_selected()

    def toggle_center_eff(self, name):
        if name == "shake":
            self.shake_enabled = not self.shake_enabled
        elif name == "jitter":
            self.jitter_enabled = not self.jitter_enabled
        elif name == "scribble":
            self.scribble_enabled = not self.scribble_enabled
        elif name == "mblur":
            self.mblur_enabled = not self.mblur_enabled
        self.update_button_visuals()
        self.apply_to_selected()

    def toggle_sub(self, name):
        if name == "flicker":
            self.flicker_enabled = not self.flicker_enabled
        elif name == "shake":
            self.shake_enabled = not self.shake_enabled
        elif name == "blur":
            self.blur_enabled = not self.blur_enabled
        self.update_button_visuals()
        self.apply_to_selected()

    def apply_to_selected(self):
        items = self.bridge.get_target_clips("playhead")
        if not items:
            items = self.bridge.get_selected_video_items()

        eff_in = "pop_in" if self.dir_in == "pop" else f"{self.mode_in}_{self.dir_in}"
        eff_out = f"{self.mode_out}_{self.dir_out}"

        opts = {
            "motion_blur": self.mblur_enabled,
            "flicker": self.flicker_enabled,
            "shake": self.shake_enabled,
            "blur_in": self.blur_enabled
        }

        count = 0
        for item in items:
            if item.GetFusionCompCount() > 0:
                if self.animator.apply_motion_preset(item, effect_in=eff_in, effect_out=eff_out, options=opts):
                    count += 1

        if self.status_cb:
            self.status_cb(f"Applied {eff_in} / {eff_out} to {count} clips.")

    def apply_auto_motion(self):
        items = self.bridge.get_target_clips("inout")
        if not items:
            items = self.bridge.get_selected_video_items()

        if not items:
            if self.status_cb:
                self.status_cb("Select clips or set In/Out range to apply AUTO motion.")
            return

        in_pool = ["bounce_up", "bounce_down", "pop_in", "slide_up"]
        for idx, item in enumerate(items):
            eff_in = in_pool[idx % len(in_pool)]
            opts = {
                "motion_blur": True,
                "shake": self.shake_enabled,
                "flicker": self.flicker_enabled
            }
            self.animator.apply_motion_preset(item, effect_in=eff_in, effect_out="slide_down", options=opts)

        if self.status_cb:
            self.status_cb(f"AUTO motion applied to {len(items)} clips!")
