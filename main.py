from guiABLE import *

app = Window(540, 240, 450, 200, title="Py_Amp")
app.setSkin(SingleSkin("GUI/bg_540x240.png"))

# Fonts
digital_font = FontPack("DS-Digital", 36, "normal", "#22ee22", "#000000")
ui_font = FontPack("Nirmala UI", color="#22ee22", drop_color="#000000")

# Top
top_bar = Hover(app, Skin("GUI/top_bar_unfocused_479x14.png", "GUI/top_bar_focused_479x14.png"))
min_but = Button(app, Skin.fromSpriteSheet("GUI/minimize_14x14.png", 14), app.minimize)
exit_but = Button(app, Skin.fromSpriteSheet("GUI/exit_14x14.png", 14), app.quit)

# Mid
display = Poster(app, SingleSkin("GUI/display_187x99.png"))
timer_text = Label(display, None, "00:04", digital_font)
title_bar = Label(app, SingleSkin("GUI/title_bar_303x28.png"), "4. Track 3 (5:04)", ui_font, font_size=14, text_pos=(6,0))
kbps_box = Label(app, SingleSkin("GUI/kpbs_41x23.png"), "192", ui_font, drop_color=None, text_pos=(36,0),anchor="ne")
kbps = Label(app, None, "kbps", ui_font, weight="bold", color="#cbdae7", drop_color=None, width=40, height=23)
khz_box = Label(app, SingleSkin("GUI/khz_33x23.png"), "44", ui_font, drop_color=None, text_pos=(28,0), anchor="ne")
khz = Label(app, None, "khz", ui_font, weight="bold", color="#cbdae7", width=30, height=23)
volume_bar = Poster(app, SingleSkin("GUI/volume_trough_129x22.png"))
volume_handle = Drag(volume_bar, SingleSkin("GUI/volume_handle_24x22.png"))
channels = Button(app, Skin.fromSpriteSheet("GUI/mono_stereo_96x20.png", 96))
progress_bar = Poster(app, SingleSkin("GUI/progress_trough_487x20.png"))
progress_handle = Drag(progress_bar, SingleSkin("GUI/progress_handle_58x20.png"))

# Buttons
prev_but = Button(app, Skin.fromSpriteSheet("GUI/prev_44x36.png", 44))
play_but = Button(app, Skin.fromSpriteSheet("GUI/play_44x36.png", 44))
pause_but = Button(app, Skin.fromSpriteSheet("GUI/pause_44x36.png", 44))
stop_but = Button(app, Skin.fromSpriteSheet("GUI/stop_44x36.png", 44))
next_but = Button(app, Skin.fromSpriteSheet("GUI/next_44x36.png", 44))
eject_but = Button(app, Skin.fromSpriteSheet("GUI/eject_44x36.png", 44))

# Half Buttons
loop_but = Button(app, Skin.fromSpriteSheet("GUI/loop_44x24.png", 44))

# guiABLE Logo
ga_instant = InstantButton(app, Skin.fromSpriteSheet("GUI/gA_30x26.png", 30))

top_bar.place(x=10, y=10)
exit_but.place(x=518, y=10)
min_but.place(x=496, y=10)

display.place(x=24, y=42)
timer_text.place(x=72, y=0)
title_bar.place(x=220, y=42)
kbps_box.place(x=220, y=86)
kbps.place(x=266, y=86)
khz_box.place(x=310, y=86)
khz.place(x=348, y=86)
volume_bar.place(x=222, y=122)
volume_handle.place(x=105, y=0)
channels.place(x=424, y=90)
progress_bar.place(x=28, y=152)
progress_handle.place(x=0, y=0)

prev_but.place(x=28, y=188)
play_but.place(x=72, y=188)
pause_but.place(x=116, y=188)
stop_but.place(x=160, y=188)
next_but.place(x=204, y=188)
eject_but.place(x=260, y=188)

loop_but.place(x=420, y=194)
ga_instant.place(x=486, y=194)

app.bindDrag(top_bar)

app.mainloop()