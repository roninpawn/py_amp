from guiABLE import *
from just_playback import Playback
from tkinter.filedialog import askopenfilename

class ActiveTrack():
    def __init__(self, path:str = "", volume:float=1.0):
        self._path = ""
        self._track = Playback()
        self._duration, self._progress = 0.0, 0.0
        self._volume = volume
        self._loop = False

        self.load(path)

    def isLoaded(self): return bool(self._path)
    def isPlaying(self): return self._track.playing
    def isPaused(self): return self._track.paused
    def loops(self): return self._loop

    @property
    def volume(self): return self._volume

    def load(self, path:str):
        if path:
            try:
                self._track.load_file(path)
                self._duration = self._track.duration
                self._path = path
                self.play()
            except:
                self._path = ""
        return self.isLoaded()

    def play(self):
        if self.isLoaded():
            if not self._track.paused:
                self._track.play()
                self._track.seek(self._progress * self._duration)
            else: self._track.resume()


            self._track.set_volume(self._volume)
            self._track.loop_at_end(self._loop)
            updateProgress()

    def pause(self):
        if self.isLoaded():
            if self._track.paused:
                self.play()
            else: self._track.pause()

    def stop(self):
        if self.isLoaded() and self._track.active:
            self._track.stop()
            updateProgress()

    def setVolume(self, volume:float):
        self._volume = volume
        if self.isLoaded(): self._track.set_volume(volume)

    def setProgress(self, percent:float) -> float:
        print(percent)
        self._progress = percent
        if self.isLoaded():
            self._track.seek(self._progress * self._duration)
            return self.getProgress()
        return 0.0

    def getProgress(self) -> float:
        if self.isLoaded(): return self._track.curr_pos / self._duration
        return 0.0

    def setLoop(self, will_loop:bool):
        self._loop = will_loop
        if self.isLoaded(): self._track.loop_at_end(will_loop)


def updateProgress():
    if not progress_bar.isHeld(): progress_bar.setPercent(track.getProgress())
    if not track.isPaused():
        if track.isPlaying():
            if not progress_bar.enabled: progress_bar.enable()
            progress_bar.after(500, updateProgress)
        else:
            progress_bar.setPercent(0.0)
            track.setProgress(0.0)


# Audio Init
track = ActiveTrack()

app = Window(540, 240, 450, 200, title="Py_Amp")
app.setSkin(Skin("GUI/bg_540x240.png"))

# Fonts
digital_font = FontPack("DS-Digital", 36, "normal", "#22ee22", "#000000", anchor="ne")
ui_font = FontPack("Nirmala UI", 12, "normal", "#22ee22", "#000000", (4,0))

# Top
top_bar = Hover(app, ("GUI/top_bar_unfocused_479x14.png", "GUI/top_bar_focused_479x14.png")).place(10, 10)
min_b = Button(app, Skin.fromSpriteSheet("GUI/minimize_14x14.png", 14), app.minimize).place(496 ,10)
exi_b = Button(app, Skin.fromSpriteSheet("GUI/exit_14x14.png", 14), app.quit).place(518, 10)

# Top-Mid
display = Image(app, "GUI/display_187x99.png").place(24, 42)
timer_text = Label(display, None, "00:04", digital_font).place(72, 0)
track_lbl = Label(app, "GUI/title_bar_303x28.png", "4. Track 3 (5:04)", ui_font, font_size=14,
                                                                                    text_pos=(6,0)).place(220, 42)
# Mid-mid
kbps_box = Label(app, "GUI/kpbs_41x23.png", "192", ui_font, drop_color=None, anchor="ne").place(220, 86)
kbps = Label(app, None, "kbps", ui_font, weight="bold", color="#cbdae7").place(260, 86)
khz_box = Label(app, "GUI/khz_33x23.png", "44", ui_font, drop_color=None, anchor="ne").place(310, 86)
khz = Label(app, None, "khz", ui_font, weight="bold", color="#cbdae7").place(343, 86)

# Low-mid
volume_slider = Slider(app, "GUI/volume_trough_129x22.png", "GUI/volume_handle_24x22.png",
                                   lambda:track.setVolume(volume_slider.getPercent()),
                                   start_percent=1.0).place(222, 122)
channels = Button(app, Skin.fromSpriteSheet("GUI/mono_stereo_96x20.png", 96)).place(424, 90)
progress_bar = Slider(app, "GUI/progress_trough_487x20.png", "GUI/progress_handle_58x20.png",
                                                lambda:track.setProgress(progress_bar.getPercent())).place(28, 152)
progress_bar.active = False
progress_bar.disable()

# Buttons
track_buttons = Collection(app).place(28, 188)
prev_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/prev_44x36.png", 44)).place(0, 0)
play_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/play_44x36.png", 44), track.play).place(44, 0)
pause_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/pause_44x36.png", 44), track.pause).place(88,0)
stop_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/stop_44x36.png", 44), track.stop).place(132, 0)
next_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/next_44x36.png", 44)).place(176, 0)
eject_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/eject_44x36.png", 44),
                                                        lambda:track.load(askopenfilename())).place(232, 0)

# Half Buttons
loop_images = UImage("GUI/loop_44x24.png").getSprites(44)
loop_images.extend([None, loop_images[2], loop_images[1], loop_images[0]])
loop_but = Checkbox(app, loop_images, lambda:track.setLoop(loop_but.isTrue())).place(420, 194)

# guiABLE Logo
ga_instant = InstantButton(app, Skin.fromSpriteSheet("GUI/gA_30x26.png", 30)).place(486, 194)

# Bindings
app.bindDrag(top_bar)

app.mainloop()
