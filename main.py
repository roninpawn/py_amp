from tkinter.filedialog import askopenfilename
from time import time
import configparser

from guiABLE import *
from active_track import ActiveTrack


""" Extend guiABLE's Label() to create a self-animating Marquee, for when track metadata exceeds the given area. """
class Marquee(Label):
    def animate(self, pixel_delta:int = 16, fps:int = 32, delay_ms:int = 3000):
        # End any animation that is already in progress.
        try:
            self.after_cancel(self._animate[7])
        except: pass

        # Reset text to origin  position.
        if self._img_text: self.delete(self._img_text)
        if self._img_text_shadow: self.delete(self._img_text_shadow)
        self._img_text, self._img_text_shadow = None, None
        self.redraw()

        # Measure whether animation is needed.
        text_bbox = self.bbox(self._img_text)
        req_width = text_bbox[0] + text_bbox[2]
        self._last_offset_x = 0

        # Only animate if the text extends beyond the given area.
        if self.width < req_width:
            origin = 0
            destination = self.width - req_width
            duration = abs(origin - destination) / pixel_delta
            animation_id = self.after_idle(self._animationStep)
            framerate = round(1000 / fps)

            # Initiate on a forced inverse-completion, triggering a delay and origin/destination flip.
            self._animate = [time() - duration, destination, 1.0, origin, duration, framerate, delay_ms, animation_id]

    def _animationStep(self):
        self._animate[2] = min(1.0, (time() - self._animate[0]) / self._animate[4])

        if self._animate[2] < 1.0:
            # Interpolate new offset.
            offset_x = round(self._animate[1] + (self._animate[3] - self._animate[1]) * self._animate[2])

            # Only redraw text if the pixel position has changed.
            if offset_x != self._last_offset_x:
                # Remove old text.
                if self._img_text: self.delete(self._img_text)
                if self._img_text_shadow: self.delete(self._img_text_shadow)
                self._img_text, self._img_text_shadow = None, None
                # Create text in new position.
                self.drawText(offset_x)
                self._last_offset_x = offset_x

            self._animate[7] = self.after(self._animate[5], self._animationStep)    # Schedule next step.
        else:
            # Flip origin with destination and set a new start time.
            new_origin = self._animate[3]
            self._animate[3] = self._animate[1]
            self._animate[1] = new_origin
            self._animate[0] = time() + (self._animate[6] / 1000)
            self._animate[7] = self.after(self._animate[6], self._animationStep)


""" Consolidate GUI functions - some of which provide an interface to ActiveTrack() - into a passable class object. """
class GuiManager():
    def __init__(self):
        self._progress_locked = False
        self._ga_closed_since = 0.0
        self._since_loaded = 0.0

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
            track.load(self.config.get("Recent", "0", fallback=""), False)

    def writeSettings(self):
        self.config.set('General', 'volume', str(track.volume))
        self.config.set('General', 'geometry', app._window.winfo_geometry().split('+', 1)[-1])
        with open('config.ini', 'w') as configfile: self.config.write(configfile)

    def storedAppPosition(self):
        return [int(x) for x in self.config.get('General', 'geometry', fallback="100+100").split('+')]

    def quit(self):
        self.writeSettings()
        app.quit()

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
        track_lbl.setText(track.info)

        kbps = str(round(track.kbps))
        khz = str(round(track.khz * .001))
        if kbps == "0": kbps = "-- "
        if khz == "0": khz = "-- "
        kbps_box.setText(kbps[:len(kbps)-3] + "k" if kbps and len(kbps) > 3 else kbps)
        khz_box.setText(khz)

        channels.setState(track.channels if track.channels < 3 else 2)
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
                    if not progress_bar.isHeld(): progress_bar.setPercent(track.getPercent())
                    progress_bar.after(500, self.unlockProgress)
                    self._progress_locked = True
                elif not dragging:
                    if track.status() != "Stopped": track.stop()
                    progress_bar.setPercent(0.0)

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
        drag_handle.changeImage(1)
        python_logo.changeImage(1)

    def showGAWin(self):
        if ga_win.visible() == False and self._ga_closed_since + 0.1 < time():
            ga_win.visible(True)
            ga_bg.focus_set()

    def hideGAWin(self, event=None):
        self._ga_closed_since = time()
        ga_win.visible(False)


""" Define the main PY_AMP GUI in less than 100 lines of code. ;) """
# Spawn Window
gui_manager = GuiManager()
app = Window(540, 240, *gui_manager.storedAppPosition(), title="Py_Amp")
app.setSkin(Skin("GUI/bg_540x240.png"))

# Initialize Audio Engine
track = ActiveTrack(gui_manager=gui_manager, tk_after=app)

# Fonts
ui_font = FontPack("Arial", 12, "normal", "#22ee22")

# Top
top_bar = Collection(app).place(0,0)
python_logo = Image(top_bar, Skin.fromSpriteSheet("GUI/python_logo_14x14.png", 14)).place(10, 10)
drag_handle = Image(top_bar, Skin.fromSpriteSheet("GUI/top_bar_456x28.png", 456)).place(31, 3)
app.bind_all("<FocusOut>", gui_manager.loseFocus)
app.bind_all("<FocusIn>", gui_manager.getFocus)

min_b = Button(top_bar, Skin.fromSpriteSheet("GUI/minimize_14x14.png", 14), app.minimize).place(496 ,10)
exi_b = Button(top_bar, Skin.fromSpriteSheet("GUI/exit_14x14.png", 14), gui_manager.quit).place(518, 10)
app.bindDrag(drag_handle)       # Drag the main window by dragging top_bar.

# Display
display = Image(app, "GUI/display_187x99.png",).place(24, 39)
display_state = Image(display, (UImage(), *UImage("GUI/playback_state_icons_22x22.png").getSprites(22))).place(16, 11)

digit_skin = Skin(*UImage("GUI/segmented_digits_20x32.png").getSprites(20), UImage())
display_progress = Collection(display).place(54, 6)
progress_min100 = Image(display_progress, digit_skin, 10).place(0, 0)
progress_min10 = Image(display_progress, digit_skin).place(24, 0)
progress_min1 = Image(display_progress, digit_skin).place(48, 0)
progress_sec10 = Image(display_progress, digit_skin).place(82, 0)
progress_sec1 = Image(display_progress, digit_skin).place(106, 0)

small_digit_skin = Skin(*UImage("GUI/segmented_digits_8x13.png").getSprites(8), UImage())
display_duration = Collection(display).place(121, 43)
duration_min1000 = Image(display_duration, small_digit_skin, 10).place(0, 0)
duration_min100 = Image(display_duration, small_digit_skin, 10).place(9, 0)
duration_min10 = Image(display_duration, small_digit_skin).place(18, 0)
duration_min1 = Image(display_duration, small_digit_skin).place(27, 0)
duration_sec10 = Image(display_duration, small_digit_skin).place(41, 0)
duration_sec1 = Image(display_duration, small_digit_skin).place(50, 0)

# Track Listing
track_bg = Image(app, "GUI/title_bar_303x28.png").place(220, 42)
track_lbl = Marquee(track_bg, None, "No track loaded.", ui_font, text_pos=(6,3), width=299).place(2, 0)

# Mid
kbps_box = Label(app, "GUI/kbps_81x23.png", "-- ", ui_font, anchor="ne", text_pos=(46, 2)).place(220, 86)
khz_box = Label(app, "GUI/khz_66x23.png", "-- ", ui_font, anchor="ne", text_pos=(38, 2)).place(312, 86)
volume_slider = Slider(app, "GUI/volume_trough_129x22.png", "GUI/volume_handle_24x22.png",
                                   lambda:track.setVolume(volume_slider.getPercent()),
                                   start_percent=1.0).place(222, 122)
channels = Image(app, Skin.fromSpriteSheet("GUI/mono_stereo_96x20.png", 96)).place(424, 90)
progress_bar = Slider(app, "GUI/progress_trough_487x20.png", "GUI/progress_handle_58x20.png",
                      gui_manager.updateProgress, lambda:track.setProgress(progress_bar.getPercent())).place(28, 152)
progress_bar.disable()      # Until a track has been loaded.

# Fade Buttons
fade_buttons = Collection(app).place(438, 119)
fi = UImage("GUI/fade_in_22x24.png").getSprites(22)
fo = UImage("GUI/fade_out_22x24.png").getSprites(22)
fu = UImage("GUI/fade_under_22x24.png").getSprites(22)
fade_in = Button(fade_buttons, (fi[0],fi[0],fi[1]), lambda:track.fadeVolume(1.0, 1.25)).place(0, 0)
fade_out = Button(fade_buttons, (fo[0],fo[0],fo[1]), lambda:track.fadeVolume(0.0, 7.0)).place(22, 0)
fade_under = Button(fade_buttons, (fu[0],fu[0],fu[1]), lambda:track.fadeVolume(.2, 1.25)).place(44, 0)

# Multimedia Buttons
track_buttons = Collection(app).place(28, 188)
prev_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/prev_44x36.png", 44)).place(0, 0)
play_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/play_44x36.png", 44), track.play).place(44, 0)
pause_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/pause_44x36.png", 44), track.pause).place(88,0)
stop_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/stop_44x36.png", 44), track.stop).place(132, 0)
next_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/next_44x36.png", 44)).place(176, 0)
eject_but = Button(track_buttons, Skin.fromSpriteSheet("GUI/eject_44x36.png", 44),gui_manager.loadTrack).place(232, 0)

# Loop Button
loop_images = UImage("GUI/loop_44x24.png").getSprites(44)
loop_images.extend([None, None, loop_images[2], loop_images[0]])
loop_images[1] = loop_images[0]
loop_but = Checkbox(app, loop_images, lambda:track.setLoop(loop_but.isTrue())).place(420, 194)

#guiABLE Popup Window
gui_manager.loadSettings()
ga_size = (333, 278)
app_size, app_location = app._window.geometry().split("+",1)
app_size = [int(x) for x in app_size.split("x")]
app_location = [int(x) for x in app_location.split("+")]
print(app_location, app_size)
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
ga_instant = InstantButton(app, ga_img, gui_manager.showGAWin).place(486, 194)

app.mainloop()
