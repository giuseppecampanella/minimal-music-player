
import os
import tkinter as tk
from time import sleep
import vlc
import datetime

DIR_MUSIC = "./music"
PLAYING = 1
STOPPED = 0

class Player:
    def __init__(self, play, pause, stop, list_music, lab_len_song, lab_curr_time, slider_song):
        self.play = play
        self.play.bind("<Button-1>", lambda event: self.play_music_event(event))
        self.pause = pause
        self.pause.bind("<Button-1>", lambda event: self.pause_music_event(event))
        self.stop = stop
        self.stop.bind("<Button-1>", lambda event: self.stop_music_event(event))
        self.music = None
        self.list_music = list_music
        # abilito il doppio click
        self.list_music.bind("<Double-Button-1>", lambda event : self.double_click_event(event))
        self.length_song = datetime.datetime.now()
        self.time_song = None
        self.lab_len_song = lab_len_song
        self.lab_curr_time = lab_curr_time
        self.new_song = True
        self.slider_song = slider_song
        # callback per quando muovo lo slider della canzone
        self.slider_song.configure(command=self.slider_moving)
        self.slider_song.bind("<ButtonRelease-1>", lambda event : self.release_slider_song(event))
        self.slider_song.bind("<Button-1>", lambda event : self.press_slider_song(event))
        self.slider_song_is_pressed = False

    def slider_moving(self, event):
        position = self.slider_song.get()
        time = self.from_position_to_time(position)
        self.lab_curr_time.configure(text=time)

    def from_position_to_time(self, position):
        seconds = int((position)%60)
        minutes = int((position/(60))%60)
        time = self.length_song.replace(minute=minutes, second=seconds)
        return datetime.datetime.strftime(time, "%M:%S")

    def play_music_event(self, event):
        self.play_song(song=self.list_music.get("active"))

    def stop_music(self):
        if(self.music and self.music.is_playing()):
            self.music.stop()
            self.stop.configure(state="disabled")

    def stop_music_event(self, event):
        self.stop_music()

    def is_playing(self):
        return self.music.is_playing() == PLAYING

    def double_click_event(self, event):
        self.play_song(self.list_music.get("active"))

    def play_song(self, song):
        self.new_song = True
        # nell'eventualità che stia suonando qualcosa la stoppo
        self.stop_music()
        self.music = vlc.MediaPlayer(DIR_MUSIC + "/" + song)
        self.music.play()
        self.stop.configure(state="active")
        self.vlc_event_manager = self.music.event_manager()
        self.vlc_event_manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, lambda event : self.time_changed(event))
        self.time_song = datetime.datetime.now().replace(minute=0, second=0)

    def time_changed(self, event):
        self.lab_len_song.configure(text=self.get_length_song())
        self.slider_song.configure(to=self.get_length_song_seconds())
        # se sto premendo non aggiorno il valore
        if(not self.slider_song_is_pressed):
            self.lab_curr_time.configure(text=self.get_time_song())
            seconds = self.get_time_song_seconds()
            self.slider_song.set(seconds)

    def pause_music_event(self, event):
        if(self.is_playing()):
            self.pause.configure(text="RESUME")
            self.music.pause()
        else:
            self.pause.configure(text="PAUSE")
            self.music.play()

    def get_time_song(self):
        millis = self.music.get_time()
        seconds = int((millis/1000)%60)
        minutes = int((millis/(1000*60))%60)
        self.time_song = self.length_song.replace(minute=minutes, second=seconds)
        return datetime.datetime.strftime(self.time_song, "%M:%S")

    def get_length_song(self):
        if self.new_song == True:
            self.new_song = False
            sleep(0.1)
            millis = self.music.get_media().get_duration()
            seconds = int((millis/1000)%60)
            minutes = int((millis/(1000*60))%60)
            self.length_song = self.length_song.replace(minute=minutes, second=seconds)
        return datetime.datetime.strftime(self.length_song, "%M:%S")

    def release_slider_song(self, event):
        position = self.slider_song.get() / self.get_length_song_seconds()
        self.slider_song_is_pressed = False
        if(self.music):
            self.music.set_position(position)

    def press_slider_song(self, event):
        # divido la posizione rispetto all'intera grandezza dello slider per la
        # lunghezza effettiva dello slider e moltiplico per la lunghezza effettiva
        # in secondi della canzone per ottenere la posizione
        position = (event.x / self.slider_song.cget("length"))*(self.get_length_song_seconds())
        self.slider_song.set(position)
        self.slider_song_is_pressed = True

    def get_length_song_seconds(self):
        return self.length_song.minute*60 + self.length_song.second

    def get_time_song_seconds(self):
        return self.time_song.minute*60 + self.time_song.second

def main():
    root = tk.Tk()
    play_button = tk.Button(root, text="PLAY")
    play_button.grid(row=0, column=0)

    pause_button = tk.Button(root, text="PAUSE")
    pause_button.grid(row=0, column=1)

    stop_button = tk.Button(root, text="STOP", state="disabled")
    stop_button.grid(row=0, column=2)

    list_music = os.listdir(DIR_MUSIC)
    list_box = tk.Listbox(root, highlightcolor="blue", selectmode="SINGLE")
    list_box.grid(row=1, column=0)
    id = 1
    for song in list_music:
        list_box.insert(id, song)
        id += 1

    slider_song = tk.Scale(root, from_=0, to=0, orient=tk.HORIZONTAL, length=400, showvalue=False)
    slider_song.grid(row=id, column=0)

    lab_len_song = tk.Label(root, text="00:00")
    lab_len_song.grid(row=id, column=2)
    lab_curr_time = tk.Label(root, text="00:00")
    lab_curr_time.grid(row=id, column=1)

    player = Player(play_button, pause_button, stop_button, list_box,
            lab_len_song, lab_curr_time, slider_song)

    root.mainloop()

if __name__ == "__main__":
    main()
