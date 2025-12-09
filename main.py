from guiABLE import *
from just_playback import Playback
from tinytag import TinyTag
from tkinter.filedialog import askopenfilename
import datetime

class ActiveTrack():
    def __init__(self, path:str = "", volume:float=1.0, tk_after=None):
        self._path = ""
        self._track = Playback()
        self._duration, self._progress = 0.0, 0.0
        self._volume = volume
        self._loop = False

        # Enable volume fading support through TK. (no extra multithreading necessary)
        self._scheduler = tk_after   # Any TK reference from the UI that supports .after()
        self._fade_job = None
        self._fading = False

        self._meta = None
        self.kbps, self.khz, self.file_size, self.album_track, self.channels = 0.0, 0, 0, 0, 0
        self.title, self.artist, self.album = "", "", ""

        self.load(path)

    def isLoaded(self): return bool(self._path)
    def isPlaying(self): return self._track.playing
    def isPaused(self): return self._track.paused
    def loops(self): return self._loop

    @property
    def duration(self): return self._duration
    @property
    def volume(self): return self._volume
    @property
    def meta(self): return self._meta
    @property
    def info(self):
        out = self.title
        if self.artist: out += f" - {self.artist}"
        if self.album: out += f" - {self.album}"
        if self.album_track: out += f" [Track #{self.album_track}]"
        return out.strip()

    def load(self, path:str):
        if path:
            self._reset()
            try:
                self._track.load_file(path)
                self._duration = self._track.duration
                self._populateMeta(path)
                setStatics()

                self._path = path
                self.play()
            except:
                self._path = ""
        return self.isLoaded()

    def play(self):
        if self.isLoaded():
            if not self._track.paused:
                if track.isPlaying(): self._progress = 0.0
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
        self._progress = 0.0
        updateProgress(True)

    def setVolume(self, volume:float):
        self._volume = volume
        if self.isLoaded(): self._track.set_volume(volume)

    def fadeVolume(self, end:float, duration:float, start:float = None, steps_per_sec:int = 30):
        if self._scheduler is None:     # Must have a scheduler (Tk root or widget)
            raise RuntimeError("ActiveTrack.fadeVolume() requires a Tk scheduler with .after()")

        # Cancel any existing fade
        if self._fade_job is not None:
            try: self._scheduler.after_cancel(self._fade_job)
            except Exception: pass
            self._fade_job = None

        self._fading = True

        # Collect/define the needed values for interpolation.
        start = max(0.0, start if start is not None else float(self._volume))
        end = max(0.0, float(end))
        total_steps = max(1, int(duration * steps_per_sec))
        step_time = int(1000 / steps_per_sec)
        delta = (end - start) / total_steps

        # A packable, recallable function that can be passed into Tk's .after() method.
        def _step(i=0, cur=start):
            if i >= total_steps:
                self.setVolume(end)
                setVolume(cur, False)
                self._fading = False
                self._fade_job = None
                return

            cur += delta
            self.setVolume(cur)
            setVolume(cur, True)
            self._fade_job = self._scheduler.after(step_time, lambda: _step(i+1, cur))

        _step()

    def setProgress(self, percent:float) -> float:
        self._progress = percent
        secs = self.getSeconds()
        if self.isLoaded():
            self._track.seek(self._progress * self._duration)
            return secs
        return 0.0

    def getSeconds(self) -> float:
        if self.isLoaded(): return self._track.curr_pos
        return 0.0

    def getPercent(self):
        if self.isLoaded(): return self._track.curr_pos / self._duration

    def setLoop(self, will_loop:bool):
        self._loop = will_loop      # loop_at_end() will restart playback if at end and stopped so this is needed.
        if not will_loop or self.isPlaying(): self._track.loop_at_end(will_loop)

    def _reset(self):
        self._track.stop()

        self._path = ""
        self._duration, self._progress = 0.0, 0.0

        self._meta = None
        self.kbps, self.khz, self.file_size, self.album_trac, self.channels = 0.0, 0, 0, 0, 0
        self.title, self.artist, self.album = "", "", ""

    def _populateMeta(self, path:str):
        self._meta = TinyTag.get(path)
        # Audio attributes
        self.kbps = self._meta.bitrate
        self.khz = self._meta.samplerate
        self.file_size = self._meta.filesize
        self.channels = self._meta.channels
        # Tag metadata
        self.title = self._meta.title or self._meta.filename.split("/")[-1].split("\\")[-1]     # Split for Win & Linux
        self.artist = self._meta.artist or ""
        self.album = self._meta.album or ""
        self.album_track = self._meta.track or ""
        print(self.kbps, self.khz, self.file_size, self.title, self.artist, self.album, self.album_track)


def setProgress(): track.setProgress(progress_bar.getPercent())

# Weird little bodge to prevent dozens/hundreds of progress threads from being made.
locked = False
def unlockProgress():
    global locked
    locked = False
    updateProgress()

def updateProgress(bypass_lock=False):
    global locked

    # Set the time display
    dragging = progress_bar.isHeld()
    if dragging:
        setTime(getTime(progress_bar.getPercent() * track.duration))
    elif not track.isPaused():
        setTime(getTime(track.getSeconds()))

    # Update the progress bar
    if not locked or bypass_lock:
        if not track.isPaused():
            if track.isPlaying():
                if not progress_bar.enabled: progress_bar.enable()
                if not progress_bar.isHeld(): progress_bar.setPercent(track.getPercent())
                progress_bar.after(500, unlockProgress)
                locked = True
            elif not dragging:
                track.setProgress(0.0)
                progress_bar.setPercent(0.0)

def setTime(time_str:str): display_progress.setText(time_str.strip())

def getTime(secs:float):
    out = datetime.timedelta(seconds=round(secs))
    if out.seconds < 3600: return str(out)[-5:]
    else: return str(out)[-7:]

def setVolume(volume:float, lock:bool = False):
    if lock:
        volume_slider.disable()
    else: volume_slider.enable()

    volume_slider.setPercent(volume)

def setStatics():
    track_lbl.setText(track.info)
    kbps = str(round(track.kbps))
    kbps_box.setText(kbps[:len(kbps)-3] + "k" if kbps and len(kbps) > 3 else kbps)
    khz_box.setText(str(round(track.khz * .001)))
    channels.setState(track.channels if track.channels < 3 else 2)
    display_duration.setText(getTime(track.duration))

# Spawn Window
app = Window(540, 240, 450, 200, title="Py_Amp")
app.setSkin(Skin("GUI/bg_540x240.png"))

# Audio Engine Init
track = ActiveTrack(tk_after=app)

# Fonts
digital_font = FontPack("DS-Digital", 36, "normal", "#22ee22", "#000000", anchor="ne")
ui_font = FontPack("Nirmala UI", 12, "normal", "#22ee22", "#000000", (4,0))

# Top
top_bar = Hover(app, ("GUI/top_bar_unfocused_479x14.png", "GUI/top_bar_focused_479x14.png")).place(10, 10)
min_b = Button(app, Skin.fromSpriteSheet("GUI/minimize_14x14.png", 14), app.minimize).place(496 ,10)
exi_b = Button(app, Skin.fromSpriteSheet("GUI/exit_14x14.png", 14), app.quit).place(518, 10)

# Top-Mid
display = Image(app, "GUI/display_187x99.png").place(24, 42)
display_progress = Label(display, None, "00:00", digital_font, width=110).place(72, 0)
display_duration = Label(display, None, "", digital_font, font_size=14, width=60).place(120, 42)
track_lbl = Label(app, "GUI/title_bar_303x28.png", "No track loaded.", ui_font, text_pos=(6,1)).place(220, 42)
# Mid-mid
kbps_box = Label(app, "GUI/kpbs_41x23.png", "-- ", ui_font, drop_color=None, anchor="ne").place(220, 86)
kbps = Label(app, None, "kbps", ui_font, weight="bold", color="#cbdae7").place(260, 86)
khz_box = Label(app, "GUI/khz_33x23.png", "-- ", ui_font, drop_color=None, anchor="ne").place(310, 86)
khz = Label(app, None, "khz", ui_font, weight="bold", color="#cbdae7").place(343, 86)

# Low-mid
volume_slider = Slider(app, "GUI/volume_trough_129x22.png", "GUI/volume_handle_24x22.png",
                                   lambda:track.setVolume(volume_slider.getPercent()),
                                   start_percent=1.0).place(222, 122)
channels = Image(app, Skin.fromSpriteSheet("GUI/mono_stereo_96x20.png", 96)).place(424, 90)
progress_bar = Slider(app, "GUI/progress_trough_487x20.png", "GUI/progress_handle_58x20.png",
                                    updateProgress, lambda:track.setProgress(progress_bar.getPercent())).place(28, 152)
progress_bar.disable()

# Fade Buttons
fade_buttons = Collection(app).place(438, 119)
fi = UImage("GUI/fade_in_22x24.png").getSprites(22)
fo = UImage("GUI/fade_out_22x24.png").getSprites(22)
fu = UImage("GUI/fade_under_22x24.png").getSprites(22)
fade_in = Button(fade_buttons, (fi[0],fi[0],fi[1]), lambda:track.fadeVolume(1.0, 1.25)).place(0, 0)
fade_out = Button(fade_buttons, (fo[0],fo[0],fo[1]), lambda:track.fadeVolume(0.0, 5.0)).place(22, 0)
fade_under = Button(fade_buttons, (fu[0],fu[0],fu[1]), lambda:track.fadeVolume(.2, 1.25)).place(44, 0)

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
