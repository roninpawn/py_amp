from guiABLE import *

app = Window(540, 240, 450, 200, title="Py_Amp")
app.setSkin(Skin("GUI/bg_540x240.png"))

# Fonts
digital_font = FontPack("DS-Digital", 36, "normal", "#22ee22", "#000000", anchor="ne")
ui_font = FontPack("Nirmala UI", color="#22ee22", drop_color="#000000", text_pos=(4,0))

# Top
top_bar = Hover(app, Skin("GUI/top_bar_unfocused_479x14.png", "GUI/top_bar_focused_479x14.png")).place(10, 10)
min_b = Button(app, Skin.fromSpriteSheet("GUI/minimize_14x14.png", 14), app.minimize).place(496 ,10)
exi_b = Button(app, Skin.fromSpriteSheet("GUI/exit_14x14.png", 14), app.quit).place(518, 10)

# Top-Mid
display = Image(app, Skin("GUI/display_187x99.png")).place(24, 42)
timer_text = Label(display, None, "00:04", digital_font).place(72, 0)
track = Label(app, Skin("GUI/title_bar_303x28.png"), "4. Track 3 (5:04)", ui_font,
                                                                    font_size=14, text_pos=(6,0)).place(220, 42)
# Mid-mid
kbps_box = Label(app, Skin("GUI/kpbs_41x23.png"), "192", ui_font, drop_color=None, anchor="ne").place(220, 86)
kbps = Label(app, None, "kbps", ui_font, weight="bold", color="#cbdae7", width=40, height=23).place(260, 86)
khz_box = Label(app, Skin("GUI/khz_33x23.png"), "44", ui_font, drop_color=None, anchor="ne").place(310, 86)
khz = Label(app, None, "khz", ui_font, weight="bold", color="#cbdae7", width=30, height=23).place(343, 86)
# Low-mid
volume_slider = Slider(app, Skin("GUI/volume_trough_129x22.png"), Skin("GUI/volume_handle_24x22.png"),
                                                                                start_percent=1).place(222, 122)
channels = Button(app, Skin.fromSpriteSheet("GUI/mono_stereo_96x20.png", 96)).place(424, 90)
progress_bar = Image(app, Skin("GUI/progress_trough_487x20.png")).place(28, 152)
progress_handle = Drag(progress_bar, Skin("GUI/progress_handle_58x20.png")).place(0, 0)

# Buttons
prev_but = Button(app, Skin.fromSpriteSheet("GUI/prev_44x36.png", 44)).place(28, 188)
play_but = Button(app, Skin.fromSpriteSheet("GUI/play_44x36.png", 44)).place(72, 188)
pause_but = Button(app, Skin.fromSpriteSheet("GUI/pause_44x36.png", 44)).place(116, 188)
stop_but = Button(app, Skin.fromSpriteSheet("GUI/stop_44x36.png", 44)).place(160, 188)
next_but = Button(app, Skin.fromSpriteSheet("GUI/next_44x36.png", 44)).place(204, 188)
eject_but = Button(app, Skin.fromSpriteSheet("GUI/eject_44x36.png", 44)).place(260, 188)

# Half Buttons
loop_but = Button(app, Skin.fromSpriteSheet("GUI/loop_44x24.png", 44)).place(420, 194)

# guiABLE Logo
ga_instant = InstantButton(app, Skin.fromSpriteSheet("GUI/gA_30x26.png", 30)).place(486, 194)


app.bindDrag(top_bar)

app.mainloop()