
import os
import tkinter as tk
from time import sleep
import vlc
import datetime

DIR_MUSIC = "./music"
DIR_ICONS = "./icons"

class Player:
    def __init__(self, play, list_box, list_music, lab_len_song, lab_curr_time,
                slider_song, lab_name_song):
        self.play = play
        self.play.bind("<Button-1>", lambda event: self.play_pause_music_event(event))
        self.music = None
        self.list_box = list_box
        self.list_music = list_music
        # abilito il doppio click
        self.list_box.bind("<Double-Button-1>", lambda event : self.double_click_event(event))
        self.length_song = datetime.datetime.now()
        self.time_song = None
        self.lab_len_song = lab_len_song
        self.lab_curr_time = lab_curr_time
        self.new_song = False
        self.slider_song = slider_song
        # callback per quando muovo lo slider della canzone
        self.slider_song.configure(command=self.slider_moving)
        self.slider_song.bind("<ButtonRelease-1>", lambda event : self.release_slider_song(event))
        self.slider_song.bind("<Button-1>", lambda event : self.press_slider_song(event))
        self.slider_song_is_pressed = False
        self.position_list = 0
        self.lab_name_song = lab_name_song
        self.len_list_music = len(self.list_music)

    def slider_moving(self, event):
        position = self.slider_song.get()
        time = self.from_position_to_time(position)
        self.lab_curr_time.configure(text=time)

    def from_position_to_time(self, position):
        seconds = int((position)%60)
        minutes = int((position/(60))%60)
        time = self.length_song.replace(minute=minutes, second=seconds)
        return datetime.datetime.strftime(time, "%M:%S")

    def play_pause_music_event(self, event):
        # se non ho ancora una traccia caricata, carico la prima dell'elenco
        if(not self.music):
            if(self.len_list_music > 0):
                self.play_song(song=self.list_music[0])
            else:
                print("Non c'è nessuna canzone nell'elenco")
        else:
            if(self.music.get_state() == vlc.State.Playing):
                self.play.configure(text="PLAY", image=self.play.play_icon)
                self.music.pause()
            elif(self.music.get_state() == vlc.State.Paused):
                self.play.configure(text="PAUSE", image=self.play.pause_icon)
                self.music.play()
            elif(self.music.get_state() == vlc.State.Ended):
                self.play_song(song=self.list_box.get("active"))

    def stop_music(self):
        if(self.music and self.music.get_state() == vlc.State.Playing):
            self.music.stop()

    def double_click_event(self, event):
        song = self.list_box.get("active")
        self.play_song(song)

    def play_song(self, song):
        self.play.configure(text="PAUSE", image=self.play.pause_icon)
        self.lab_name_song.configure(text=song)
        index = self.position_list = self.list_music.index(song)
        self.list_box.select_set(index)
        self.list_box.activate(index)
        self.new_song = True
        # nell'eventualità che stia suonando qualcosa la stoppo
        self.stop_music()
        self.music = vlc.MediaPlayer(DIR_MUSIC + "/" + song)
        self.music.play()
        self.vlc_event_manager = self.music.event_manager()
        self.vlc_event_manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, lambda event : self.time_changed(event))
        self.vlc_event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, lambda event : self.end_reached_song(event))
        self.time_song = datetime.datetime.now().replace(minute=0, second=0)

    def time_changed(self, event):
        self.lab_len_song.configure(text=self.get_length_song())
        self.slider_song.configure(to=self.get_length_song_seconds())
        # se sto premendo non aggiorno il valore
        if(not self.slider_song_is_pressed):
            self.lab_curr_time.configure(text=self.get_time_song())
            seconds = self.get_time_song_seconds()
            self.slider_song.set(seconds)

    def end_reached_song(self, event):
        self.position_list += 1
        # sono arrivato alla fine dell'elenco delle canzoni
        if(self.position_list == self.len_list_music):
            self.lab_name_song.configure(text="----")
            self.lab_len_song.configure(text="--:--")
            self.lab_curr_time.configure(text="--:--")
            self.list_box.selection_clear(0, tk.END)
            self.list_box.select_set(0)
            self.list_box.activate(0)
            self.play.configure(text="PLAY", image=self.play.play_icon)
        else:
            index = self.position_list
            self.list_box.selection_clear(0, tk.END)
            self.list_box.selection_set(index)
            song = self.list_music[index]
            self.play_song(song)

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
    root.resizable(0,0)

    listbox_frame = tk.Frame(root)
    listbox_frame.pack(fill="x")

    name_song_frame = tk.Frame(root)
    name_song_frame.pack()

    slider_frame = tk.Frame(root)
    slider_frame.pack()

    buttons_frame = tk.Frame(root)
    buttons_frame.pack()

    lab_name_song = tk.Label(name_song_frame, text="----")
    lab_name_song.pack(side="bottom")

    play_icon = tk.PhotoImage(file=DIR_ICONS + "/" + "play.png")
    play_button = tk.Button(buttons_frame, text="PLAY", image=play_icon)
    # evito il garbage collector associandolo al campo del Button
    play_button.play_icon = play_icon
    play_button.pause_icon = tk.PhotoImage(file=DIR_ICONS + "/" + "pause.png")
    play_button.pack(side="left")

    list_music = os.listdir(DIR_MUSIC)

    list_box = tk.Listbox(listbox_frame, selectbackground="sky blue", selectmode="SINGLE")
    list_box.pack(side="top", fill=tk.BOTH, expand=1)
    id = 1
    for song in list_music:
        list_box.insert(id, song)
        id += 1

    slider_song = tk.Scale(slider_frame, from_=0, to=0, orient=tk.HORIZONTAL, length=400, showvalue=False)
    slider_song.pack(side="left")

    lab_curr_time = tk.Label(slider_frame, text="--:--")
    lab_curr_time.pack(side="left")
    lab_len_song = tk.Label(slider_frame, text="--:--")
    lab_len_song.pack(side="left")

    player = Player(play_button, list_box, list_music, lab_len_song,
                    lab_curr_time, slider_song, lab_name_song)

    root.mainloop()

if __name__ == "__main__":
    main()
