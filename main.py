from tkinter.filedialog import askopenfilename
from time import time
import configparser

from guiABLE import *

from active_track import ActiveTrack


""" An Image whose Labelable child scrolls horizontally when its text exceeds the available area. """
class Marquee(LinearAnimator, Image):
    def __init__(self, parent, skin=None, text="", **kwargs):
        super().__init__(parent, skin=skin, text=text, **kwargs)

        self._last_offset_x = 0
        self._marquee_after = None

    def animate(self, pixel_delta:int=16, fps:int=32, delay_ms:int=3000):
        self.stopAnimation()

        if self._marquee_after is not None:
            self.after_cancel(self._marquee_after)
            self._marquee_after = None

        if self._text_pos is None: self._text_pos = (0, 0)
        self._text_anchor = "w"
        self._last_offset_x = 0
        self._anchorLabel()

        req_width = self._label.width
        if self.width >= req_width: return

        self._marquee = [
            self._text_pos[0],
            self.width - req_width,
            pixel_delta,
            round(1000 / fps),
            delay_ms
        ]

        self._marquee_after = self.after(delay_ms, self._animateMarquee)

    def _animateMarquee(self):
        origin, destination, pixel_delta, framerate, delay_ms = self._marquee
        duration = round(abs(origin - destination) / pixel_delta * 1000)

        self._marquee[0], self._marquee[1] = destination, origin

        LinearAnimator.animate(
            self,
            origin,
            destination,
            duration,
            self._drawMarquee,
            framerate,
            self._pauseMarquee
        )

    def _drawMarquee(self, offset_x:float):
        offset_x = round(offset_x)
        if offset_x == self._last_offset_x: return

        self._text_pos = (offset_x, self._text_pos[1])
        self._anchorLabel()
        self._last_offset_x = offset_x

    def _pauseMarquee(self):
        self._marquee_after = self.after(self._marquee[4], self._animateMarquee)


""" Consolidate GUI functions - some of which provide an interface to ActiveTrack() - into a passable class object. """
class GuiManager():
    def __init__(self):
        self._progress_locked = False
        self._ga_closed_since = 0.0
        self._since_loaded = 0.0
        self._playlist_focus = False

        self.config = configparser.ConfigParser()
        try: self.config.read('config.ini')
        except:
            self.config.add_section('General')
            self.config.set('General', 'geometry', '100+100')

    def loadSettings(self):
        if "General" in self.config.sections():
            volume = self.config.getfloat('General', 'volume', fallback=1.0)
            track.setVolume(volume)
            self.setVolume(volume)
        else:
            self.config.add_section('General')
        if "Recent" in self.config.sections() and "0" in self.config["Recent"]:
            success = track.load(self.config.get("Recent", "0", fallback=""), False, False)
            if success:
                progress_bar.enable()
            else: self.config.remove_option("Recent", "0")

    def writeSettings(self):
        self.config.set('General', 'volume', str(track.volume))
        self.config.set('General', 'geometry', app._window.winfo_geometry().split('+', 1)[-1])
        with open('config.ini', 'w') as configfile: self.config.write(configfile)

    def storedAppPosition(self):
        return [int(x) for x in self.config.get('General', 'geometry', fallback="100+100").split('+')]

    def quit(self):
        self.writeSettings()
        app.quit()

    def playlistClose(self):
        playlist_win.visible(False)
        app.focus_force()

    def loadTrack(self):
        # Prevents a false click-through when double-clicking to open a file that is directly atop the load button.
        if self._since_loaded + 0.1 < time(): track.load(askopenfilename())
        self._since_loaded = time()

    def unloadTrack(self):
        progress_bar.setPercent(0.0)
        progress_bar.disable()
        self.setState()

    def registerTrack(self, path:str):
        if "Recent" not in self.config.sections():
            self.config.add_section("Recent")           # Create section
            self.config.set("Recent", "0", path)        # Add current track as only member of the list.
        else:
            tracks = list(self.config["Recent"].values())
            for track in tracks:                        # Purge any duplicates.
                if path == track: tracks.remove(track)
            tracks.insert(0, path)                      # Insert the current track at the top of the list.
            if len(tracks) > 5: tracks.pop()            # Limit the length of the list to 5 tracks.

            self.config.remove_section("Recent")        # Empty the existing 'Recent' list entirely.
            self.config.add_section("Recent")
            for i, track in enumerate(tracks):          # Repopulate 'Recent' with the new stack.
                self.config.set("Recent", str(i), track)

    @staticmethod
    def setVolume(volume:float, lock:bool = False):
        if lock:
            volume_slider.disable()
        else: volume_slider.enable()

        volume_slider.setPercent(volume)

    @staticmethod
    def setState():
        if track.status() == "Playing": display_state.changeImage(1)    # Change state-icon here
        elif track.status() == "Stopped": display_state.changeImage(2)
        elif track.status() == "Paused": display_state.changeImage(3)
        elif track.status() == "Unloaded": display_state.changeImage(0)

    def setStatics(self):
        track_lbl.setText("  " + track.info + "  ")

        kbps = str(round(track.kbps))
        khz = str(round(track.khz * .001))
        if kbps == "0": kbps = "-- "
        if khz == "0": khz = "-- "
        kbps_box.setText(kbps[:len(kbps)-3] + "k" if kbps and len(kbps) > 3 else kbps)
        khz_box.setText(khz)

        channels.setState(0 if track.channels < 2 else 1)
        self.setDuration(self.getTime(track.duration))

        track_lbl.animate()

    # Weird little bodge to prevent dozens/hundreds of progress threads from being made.
    def unlockProgress(self):
        self._progress_locked = False
        self.updateProgress()

    def updateProgress(self, bypass_lock=False):
        # Set the time display
        dragging = progress_bar.isHeld()
        if dragging:
            self.setTime(self.getTime(progress_bar.getPercent() * track.duration))
        elif not track.isPaused():
            self.setTime(self.getTime(track.getSeconds()))

        # Update the progress bar
        if not self._progress_locked or bypass_lock:
            if not track.isPaused():
                if track.isPlaying():
                    if not progress_bar.enabled: progress_bar.enable()

                    progress_ms = 500
                    if not progress_bar.isHeld():
                        target = min(1.0, track.getPercent() + (progress_ms / 1000) / track.duration)
                        progress_bar.slideTo(target, progress_ms)

                    progress_bar.after(progress_ms, self.unlockProgress)
                    self._progress_locked = True
                elif not dragging:
                    if track.status() != "Stopped": track.stop()
                    progress_bar.slideTo(0.0, 0)

    @staticmethod
    def getTime(secs:float) -> str: return f"{int(secs // 60):02d}:{round(secs % 60):02d}"

    @staticmethod
    def setTime(min_sec_str:str):
        mins, secs = min_sec_str.strip().split(":")
        m_index = len(mins) - 1
        progress_min100.changeImage(int(mins[m_index-2])) if m_index > 1 else progress_min100.changeImage(10)
        progress_min10.changeImage(int(mins[m_index-1]))
        progress_min1.changeImage(int(mins[m_index]))
        progress_sec10.changeImage(int(secs[0]))
        progress_sec1.changeImage(int(secs[1]))

    @staticmethod
    def setDuration(min_sec_str:str):
        mins, secs = min_sec_str.strip().split(":")
        m_index = len(mins) - 1
        duration_min1000.changeImage(int(mins[m_index-3])) if m_index > 2 else duration_min1000.changeImage(10)
        duration_min100.changeImage(int(mins[m_index-2])) if m_index > 1 else duration_min100.changeImage(10)
        duration_min10.changeImage(int(mins[m_index-1]))
        duration_min1.changeImage(int(mins[m_index]))
        duration_sec10.changeImage(int(secs[0]))
        duration_sec1.changeImage(int(secs[1]))

    def loseFocus(self, event=None):
        drag_handle.changeImage(0)
        python_logo.changeImage(0)

    def getFocus(self, event=None):
        if not self._playlist_focus:
            drag_handle.changeImage(1)
            python_logo.changeImage(1)
        else: drag_handle.changeImage(0)

    def showGAWin(self):
        if ga_win.visible() == False and self._ga_closed_since + 0.1 < time():
            ga_win.visible(True)
            ga_bg.focus_set()

    def hideGAWin(self, event=None):
        self._ga_closed_since = time()
        ga_win.visible(False)

    def playlistGetFocus(self, event=None):
        self._playlist_focus = True
        playlist_top_bar.changeImage(1)

    def playlistLoseFocus(self, event=None):
        self._playlist_focus = False
        playlist_top_bar.changeImage(0)


""" Define the main PY_AMP GUI in around 100 lines of code. ;) """
# Spawn Window
gui_manager = GuiManager()
app = Window(*gui_manager.storedAppPosition(), width=432, height=192, title="Py_Amp")
bg_skin = Skin("GUI/bg_432x192.png")
app.setSkin(bg_skin)

# Initialize Audio Engine
track = ActiveTrack(gui_manager=gui_manager, tk_after=app)

# Fonts
ui_font = FontPack("Arial", 12, "normal", "#22ee22")

# Top
top_bar = Collection(app).place(0,0)
python_logo = Image(top_bar, Skin.fromSpriteSheet("GUI/python_logo_14x14.png", 14)).place(8, 8)
drag_handle = Image(top_bar, Skin.fromSpriteSheet("GUI/top_bar_363x28.png", 363)).place(27, 2)
app.bind_all("<FocusOut>", gui_manager.loseFocus)
app.bind_all("<FocusIn>", gui_manager.getFocus)

exit_skin = Skin.fromSpriteSheet("GUI/exit_14x14.png", 14)
min_b = Button(top_bar, Skin.fromSpriteSheet("GUI/minimize_14x14.png", 14), app.minimize).place(396 ,8)
exi_b = Button(top_bar, exit_skin, gui_manager.quit).place(414, 8)
app.bindDrag(drag_handle)       # Drag the main window by dragging top_bar.

# Display
display = Image(app, "GUI/display_143x78.png",).place(19, 32)
display_state = Image(display, (UImage(), *UImage("GUI/playback_state_icons_22x22.png").getSprites(22))).place(10, 44)

digit_skin = Skin(*UImage("GUI/segmented_digits_20x32.png").getSprites(20), UImage())
display_progress = Collection(display).place(21, 5)
progress_min100 = Image(display_progress, digit_skin, 10).place(0, 0)
progress_min10 = Image(display_progress, digit_skin).place(21, 0)
progress_min1 = Image(display_progress, digit_skin).place(42, 0)
progress_sec10 = Image(display_progress, digit_skin).place(72, 0)
progress_sec1 = Image(display_progress, digit_skin).place(93, 0)

small_digit_skin = Skin(*UImage("GUI/segmented_digits_10x16.png").getSprites(10), UImage())
display_duration = Collection(display).place(62, 45)
duration_min1000 = Image(display_duration, small_digit_skin, 10).place(0, 0)
duration_min100 = Image(display_duration, small_digit_skin, 10).place(11, 0)
duration_min10 = Image(display_duration, small_digit_skin).place(22, 0)
duration_min1 = Image(display_duration, small_digit_skin).place(33, 0)
duration_sec10 = Image(display_duration, small_digit_skin).place(50, 0)
duration_sec1 = Image(display_duration, small_digit_skin).place(61, 0)

# Track Listing
track_box = Image(app, "GUI/track_bar_242x27.png").place(169, 34)
track_lbl = Marquee(track_box, Skin.fromColors(238, 24, "black"), "No track loaded.", font_pack=ui_font, ).place(2, 1)

# Mid
kbps_box = Image(app, "GUI/kbps_81x23.png", font_pack=ui_font, font_size=11, anchor="e", text_pos=(-44,0)).place(169, 66)
khz_box = Image(app, "GUI/khz_66x23.png", font_pack=ui_font, font_size=11, anchor="e", text_pos=(-36,0)).place(259, 66)
volume_slider = DynamicSlider(app, "GUI/volume_trough_129x22.png", "GUI/volume_handle_24x22.png",
                lambda: track.setVolume(volume_slider.getPercent()),slide_duration=120).place(169, 93)
channels = Image(app, Skin.fromSpriteSheet("GUI/stereo_48x20.png", 48)).place(368, 67)
progress_bar = AnimatedSlider(app, "GUI/progress_trough_399x20.png", "GUI/progress_handle_58x20.png",
                      gui_manager.updateProgress, lambda:track.setProgress(progress_bar.getPercent())).place(21, 116)
progress_bar.disable()      # Until a track has been loaded.

# Fade Buttons
fade_buttons = Collection(app).place(346, 89)
fi = UImage("GUI/fade_in_22x24.png").getSprites(22)
fo = UImage("GUI/fade_out_22x24.png").getSprites(22)
fu = UImage("GUI/fade_under_22x24.png").getSprites(22)
fade_in = Button(fade_buttons, (fi[0],fi[0],fi[1]), lambda:track.fadeVolume(1.0, 1.25)).place(0, 0)
fade_out = Button(fade_buttons, (fo[0],fo[0],fo[1]), lambda:track.fadeVolume(0.0, 7.0)).place(22, 0)
fade_under = Button(fade_buttons, (fu[0],fu[0],fu[1]), lambda:track.fadeVolume(.25, 1.25)).place(44, 0)

# Multimedia Buttons
track_buttons = Collection(app).place(21, 144)
prev_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/prev_44x36.png", 44)).place(0, 0)
play_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/play_44x36.png", 44), track.play).place(44, 0)
pause_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/pause_44x36.png", 44), track.pause).place(88,0)
stop_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/stop_44x36.png", 44), track.stop).place(132, 0)
next_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/next_44x36.png", 44)).place(176, 0)
eject_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/eject_44x36.png", 44),gui_manager.loadTrack).place(230, 0)

# Loop Button
loop_images = UImage("GUI/loop_44x24.png").getSprites(44)
loop_images.extend([None, None, loop_images[2], loop_images[0]])
loop_images[1] = loop_images[0]
loop_but = Checkbox(app, loop_images, lambda:track.setLoop(loop_but.isTrue())).place(305, 149)

#guiABLE Popup Window
gui_manager.loadSettings()
ga_size = (333, 278)
win_geom = app.windowGeometry()
app_size, app_location = win_geom[2:], win_geom[:2]
ga_location = (int(app_location[0] + (app_size[0] * 0.5) - ga_size[0] * 0.5),
               int(app_location[1] + (app_size[1] * 0.5) - ga_size[1] * 0.5) )
ga_win = ChildWindow(app, ga_location, width=ga_size[0], height=ga_size[1])
ga_bg = Background(ga_win, "GUI/ga_win_333x278.png").place(0,0)
ga_bg.bind("<FocusOut>", gui_manager.hideGAWin)
ga_bg.bind("<Escape>", gui_manager.hideGAWin)
ga_closed = time()      # Prevents instantly reopening ga_win if ga_instant is clicked while exiting the window.

# guiABLE Button
ga_img = UImage("GUI/gA_30x26.png").getSprites(30)
ga_img.append(ga_img[1])
ga_instant = InstantButton(app, ga_img, gui_manager.showGAWin).place(380, 148)

""" Define the Playlists Window """
playlist_geom = list(app.windowGeometry())
playlist_win = ChildWindow(app, (0, playlist_geom[3]), width=playlist_geom[2], height=playlist_geom[3])
playlist_bg = Background(playlist_win, "GUI/playlist_bg_432x192.png").place(0, 0)
playlist_win.visible(False)

playlist_win.bind("<FocusIn>", gui_manager.playlistGetFocus)
playlist_win.bind("<FocusOut>", gui_manager.playlistLoseFocus)

playlist_top_bar = Image(playlist_bg, Skin.fromSpriteSheet("GUI/playlist_top_bar_396x28.png", 399)).place(11, 0)
playlist_exit = Button(playlist_bg, exit_skin, gui_manager.playlistClose).place(414, 6)

playlist_box = Image(playlist_bg, "GUI/playlist_box_376x133.png").place(17, 31)
collection_tray = Label(playlist_box, "← Collection Tray →", ui_font, color="#a3a0bd").place(121, 108)
scroll_trough = Image(playlist_bg, "GUI/scroll_trough_20x109.png").place(398, 31)

playlist_duration = Image(playlist_bg, "GUI/playlist_duration_189x23.png",
                            text="00:00 / 00:00", text_pos=(-3,0), font_pack=ui_font, anchor="e").place(203, 164)

app.mainloop()
