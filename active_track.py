from just_playback import Playback
from tinytag import TinyTag

class ActiveTrack():
    def __init__(self, path:str = "", volume:float=1.0, gui_manager=None, tk_after=None):
        self._path = ""
        self._track = Playback()
        self._duration, self._progress = 0.0, 0.0
        self._volume = volume
        self._loop = False

        # Reference to be able to send events to the GUI
        self._gui = gui_manager

        # Enable volume fading support through TK. (no extra multithreading necessary)
        self._scheduler = tk_after   # Any TK reference from the UI that supports .after()
        self._fade_job = None
        self._fading = False

        self._meta = None
        self.kbps, self.khz, self.file_size, self.album_track, self.channels = 0.0, 0, 0, 0, 0
        self.title, self.artist, self.album = "", "", ""
        self._status = "Unloaded"

        self.load(path, False)

    def status(self) -> str: return self._status
    def isLoaded(self) -> bool: return bool(self._path)
    def isPlaying(self) -> bool: return self._track.playing
    def isPaused(self) -> bool: return self._track.paused
    def loops(self) -> bool: return self._loop

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

    def load(self, path:str, autoplay=True, display_error=True):
        if path:
            self._reset()
            try:
                self._track.load_file(path)
                self._duration = self._track.duration
                self._populateMeta(path)
                self._path = path
                self._gui.registerTrack(path)
                if autoplay: self.play()
                else: self.stop()
            except Exception as e:
                self._reset()
                if display_error:
                    try:                # Play error sound
                        self._track.set_volume(1.0)
                        self._track.load_file("GUI/551543__phiiraco__8-bit-denyerror-sound.wav")
                        self._track.play()
                    except Exception as e2: print("Failed to play error sound:\n", e2)

                    e = str(e)
                    self.title = f"CANNOT PLAY FILE: '{path.replace("\\", "/").split('/')[-1]}'" if e == "MA_ERROR" else e
                self._gui.unloadTrack()

            self._gui.setStatics()
        return self.isLoaded()

    def unload(self): self._reset()

    def play(self):
        if self.isLoaded():
            if not self._track.paused:
                if self.isPlaying(): self._progress = 0.0
                self._track.play()
                self._track.seek(self._progress * self._duration)
            else: self._track.resume()
            self._status = "Playing"

            self._track.set_volume(self._volume)
            self._track.loop_at_end(self._loop)
            self._gui.updateProgress()
            self._gui.setState()

    def pause(self):
        if self.isLoaded() and self._status != "Stopped":
            if not self._track.paused:
                self._track.pause()
                self._status = "Paused"
                self._gui.setState()
            else: self.play()

    def stop(self):
        if self.isLoaded():
            self._status = "Stopped"
            if self._track.active: self._track.stop()
            self._progress = 0.0
            self._gui.updateProgress(True)
            self._gui.setState()

    def setVolume(self, volume:float):
        self._volume = volume
        if self.isLoaded(): self._track.set_volume(volume)

    def fadeVolume(self, end:float, duration:float, start:float = None, steps_per_sec:int = 32):
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

        # Quadratic easing method.
        def _ease_out(t: float) -> float: return 1 - (1 - t)**2

        # A packable, recallable function that can be passed into Tk's .after() method.
        def _step(i=0, cur=start):
            if i >= total_steps:
                self.setVolume(end)
                self._gui.setVolume(cur, False)
                self._fading = False
                self._fade_job = None
                return

            t = (i + 1) / total_steps          # Normalized progress
            cur = start + (end - start) * _ease_out(t)

            self.setVolume(cur)
            self._gui.setVolume(cur, True)
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
        return 0.0

    def setLoop(self, will_loop:bool):
        self._loop = will_loop      # loop_at_end() will restart playback if at end and stopped so this is needed.
        if not will_loop or self.isPlaying(): self._track.loop_at_end(will_loop)

    def _reset(self):
        try: self._track.load_file("")
        except: pass

        self._path = ""
        self._duration, self._progress = 0.0, 0.0

        self._meta = None
        self.kbps, self.khz, self.file_size, self.album_track, self.channels = 0.0, 0, 0, 0, 0
        self.title, self.artist, self.album = "No track loaded.", "", ""
        self._status = "Unloaded"

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
