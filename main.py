from guiABLE import *

app = Window(540, 240, 450, 200, title="PyAmp")
app.setSkin(SingleSkin("GUI/bg_540x240.png"))

no_skin = Skin().fromImages(UImage())

# Top
top_bar = Hover(app, Skin("GUI/top_bar_unfocused_479x14.png", "GUI/top_bar_focused_479x14.png"), width=479, height=14)
min_but = Button(app, Skin.fromSpriteSheet("GUI/minimize_14x14.png", 14), app.minimize, width=14, height=14)
exit_but = Button(app, Skin.fromSpriteSheet("GUI/exit_14x14.png", 14), app.quit, width=14, height=14)

# Mid
display = Poster(app, SingleSkin("GUI/display_187x99.png"), width=187, height=99)
timer_text = Label(display, no_skin, "00:04",
                   ("DS-Digital", 36), color="#22ee22", drop_color="#000000", width=187, height=64)
title_bar = Label(app, SingleSkin("GUI/title_bar_303x28.png"), "  4. Track 3 (5:04)",
                  ("Nirmala UI", 14), color="#22ee22", drop_color="#000000", width=303, height=28)
kbps_box = Label(app, SingleSkin("GUI/kpbs_41x23.png"), "  192",
                 ("Nirmala UI", 12), color="#22ee22", drop_color="#000000", width=41, height=23)
kbps = Label(app, no_skin, "kbps",
                 ("Nirmala UI", 12, "bold"), color="#cbdae7", drop_color=None, width=40, height=23)
khz_box = Label(app, SingleSkin("GUI/khz_33x23.png"), "  44",
                ("Nirmala UI", 12), color="#22ee22", drop_color=None, width=33, height=23)
khz = Label(app, no_skin, "khz",
                 ("Nirmala UI", 12, "bold"), color="#cbdae7", drop_color="#000000", width=30, height=23)
volume_bar = Poster(app, SingleSkin("GUI/volume_trough_129x22.png"), width=129, height=22)
volume_handle = Drag(volume_bar, SingleSkin("GUI/volume_handle_24x22.png"), width=24, height=22)
channels = Button(app, Skin.fromSpriteSheet("GUI/mono_stereo_96x20.png", 96), width=96, height=20)
progress_bar = Poster(app, Skin("GUI/progress_trough_487x20.png"), width=487, height=20)
print(progress_bar.skin.usesBgColors())
progress_handle = Drag(progress_bar, SingleSkin("GUI/progress_handle_58x20.png"), width=58, height=20)

# Buttons
prev_but = Button(app, Skin.fromSpriteSheet("GUI/prev_44x36.png", 44), width=44, height=36)
play_but = Button(app, Skin.fromSpriteSheet("GUI/play_44x36.png", 44), width=44, height=36)
pause_but = Button(app, Skin.fromSpriteSheet("GUI/pause_44x36.png", 44), width=44, height=36)
stop_but = Button(app, Skin.fromSpriteSheet("GUI/stop_44x36.png", 44), width=44, height=36)
next_but = Button(app, Skin.fromSpriteSheet("GUI/next_44x36.png", 44), width=44, height=36)
eject_but = Button(app, Skin.fromSpriteSheet("GUI/eject_44x36.png", 44), width=44, height=36)

# Half Buttons
loop_but = Button(app, Skin.fromSpriteSheet("GUI/loop_44x24.png", 44), width=44, height=24)

# guiABLE Logo
ga_instant = InstantButton(app, Skin.fromSpriteSheet("GUI/gA_30x26.png", 30), width=30, height=26)

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