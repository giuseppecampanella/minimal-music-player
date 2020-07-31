#-------------------------------------------
# music player based on tkinter library
# 2020, Giuseppe Campanella
#-------------------------------------------

import os
import json
from tkinter import filedialog
from tkinter import messagebox
import tkinter as tk
from time import sleep
import vlc
import datetime

MIN_VOLUME = 0
MAX_VOLUME = 100

class Utility:
    def __init__(self, dir_music, dir_icons):
        self.dir_music = dir_music
        self.dir_icons = dir_icons
        self.isshown = False

    def add_listbox_widget(self, listbox):
        self.listbox = listbox

    def show_settings_frame(self, player):
        # Se è gia visibile la schermata Settings non ne creo un'altra
        if(self.isshown == True):
            return
        else:
            self.isshown = True

        folder_selected = self.dir_music
        root = tk.Toplevel()
        # non faccio nascondere questa finestra
        # root.attributes('-topmost', 'true')
        root.title("Settings")

        dir_frame = tk.Frame(root)
        dir_frame.pack()

        lab_directory = tk.Label(dir_frame, text="directory")
        lab_directory.pack(side="left")

        entry_dir = tk.Entry(dir_frame, relief=tk.RAISED)
        entry_dir.delete(0, tk.END)
        entry_dir.insert(0, folder_selected)
        entry_dir.pack(side="left")

        self.entry = entry_dir

        button_explore = tk.Button(dir_frame, text="Explore...")
        button_explore.pack(side="left")

        button_explore.bind("<Button-1>", lambda event : self.choose_directory_event(event))

        button_save = tk.Button(dir_frame, text = "Save")
        button_save.pack(side="left")

        button_save.bind("<Button-1>", lambda event : self.save_modifications_and_close(root, player, event))

        root.protocol("WM_DELETE_WINDOW", lambda : self.close_window(root))

    def close_window(self, root):
        self.isshown = False
        root.destroy()

    def save_modifications_and_close(self, root, player, event):
        folder = self.entry.get()
        if(os.path.exists(folder)):
            self.isshown = False
            self.dir_music = folder
            self.write_settings_json_to_file()
            self.get_list_music_from_dir()
            # cambio la lista della musica all'iterno di player
            player.change_list_music()
            root.destroy()
        else:
            messagebox.showerror("Error", "This directory does not exist. Click the browse button and chose a valid path.")

    def choose_directory_event(self, event):
        folder_selected = filedialog.askdirectory()
        # se non scelgo nulla rimango con la scelta precedente
        if(len(folder_selected) > 0):
            self.entry.delete(0, tk.END)
            self.entry.insert(0, folder_selected)

    # cambio la lista della musica
    def get_list_music_from_dir(self):
        self.list_music = os.listdir(self.dir_music)

        # cancello i vecchi elementi e aggiungo i nuovi
        self.listbox.delete(0,tk.END)
        id = 1
        for song in self.list_music:
            self.listbox.insert(id, song)
            id += 1

    def write_settings_json_to_file(self):
        dict = {}
        dict["directory_music"] = self.dir_music
        dict["directory_icons"] = "./icons"
        with open('settings.json', 'w') as f:
            json.dump(dict, f)

class Player:
    def __init__(self, utility, play, list_box, list_music, lab_len_song,
                lab_curr_time, slider_song, lab_name_song, slider_volume,
                next_button, previous_button):
        self.utility = utility
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
        self.slider_volume = slider_volume
        self.slider_volume.bind("<B1-Motion>", lambda event : self.drag_slider_volume(event))
        self.slider_volume.bind("<Button-1>", lambda event : self.press_slider_volume(event))
        self.slider_volume.set(30)
        self.next_button = next_button
        self.next_button.bind("<Button-1>", lambda event: self.change_song_event(event, next=True))
        self.previous_button = previous_button
        self.previous_button.bind("<Button-1>", lambda event: self.change_song_event(event, previous=True))

    def change_song_event(self, event, next=False, previous=False):
        if next:
            if(self.position_list < self.len_list_music - 1):
                self.position_list += 1
            else:
                self.position_list = 0
        else:
            if(self.position_list > 0):
                self.position_list -= 1
            else:
                self.position_list = self.len_list_music - 1

        index = self.position_list
        self.list_box.selection_clear(0, tk.END)
        self.list_box.selection_set(index)
        song = self.list_music[index]
        self.play_song(song)

    def change_list_music(self):
        self.list_music = self.utility.list_music
        self.len_list_music = len(self.list_music)
        self.position_list = 0

    def press_slider_volume(self, event):
        position = event.x
        if(position < MIN_VOLUME):
            position = MIN_VOLUME
        elif(position > MAX_VOLUME):
            position = MAX_VOLUME

        self.slider_volume.set(position)
        # se ho una traccia caricata cambio il volume
        if self.music:
            self.music.audio_set_volume(position)

    def drag_slider_volume(self, event):
        position = event.x
        if(position < MIN_VOLUME):
            position = MIN_VOLUME
        elif(position > MAX_VOLUME):
            position = MAX_VOLUME
        # se ho una traccia caricata cambio il volume
        if self.music:
            self.music.audio_set_volume(position)

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
                messagebox.showinfo("Info", f"This directory `{self.utility.dir_music}` is empty. Click the settings button and chose a valid path.")
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
        self.music = vlc.MediaPlayer(self.utility.dir_music + "/" + song)
        self.music.audio_set_volume(self.slider_volume.get())
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

    def change_music_path_from_settings(self, player):
        self.utility.show_settings_frame(player)


def read_settings_json_from_file():
    dir_music = dir_icons = ""
    with open("settings.json") as file:
        data = json.load(file)
        dir_music = data['directory_music']
        dir_icons = data['directory_icons']
    return dir_music, dir_icons

def main():

    dir_music, dir_icons = read_settings_json_from_file()

    utility = Utility(dir_music, dir_icons)

    root = tk.Tk()
    root.title("minimal music player")
    root.resizable(0,0)

    listbox_frame = tk.Frame(root)
    listbox_frame.pack(fill="x")

    name_song_frame = tk.Frame(root)
    name_song_frame.pack()

    slider_frame = tk.Frame(root)
    slider_frame.pack()

    buttons_frame = tk.Frame(root)
    buttons_frame.pack(fill="x")

    volume_frame = tk.Frame(buttons_frame)
    volume_frame.pack(side="right")

    lab_name_song = tk.Label(name_song_frame, text="----")
    lab_name_song.pack(side="bottom")

    play_icon = tk.PhotoImage(file=utility.dir_icons + "/" + "play.png")
    play_button = tk.Button(buttons_frame, text="PLAY", image=play_icon)
    # evito il garbage collector associandolo al campo del Button
    play_button.play_icon = play_icon
    play_button.pause_icon = tk.PhotoImage(file=utility.dir_icons + "/" + "pause.png")
    play_button.pack(side="left")

    previous_icon = tk.PhotoImage(file=utility.dir_icons + "/" + "previous.png")
    previous_button = tk.Button(buttons_frame, text="PREVIOUS", image=previous_icon)
    previous_button.previous_icon = previous_icon
    previous_button.pack(side="left")

    next_icon = tk.PhotoImage(file=utility.dir_icons + "/" + "next.png")
    next_button = tk.Button(buttons_frame, text="NEXT", image=next_icon)
    next_button.next_icon = next_icon
    next_button.pack(side="left")

    slider_volume = tk.Scale(volume_frame, from_=0, to=100, orient=tk.HORIZONTAL, length=100)
    slider_volume.pack(side="right")

    list_music = []
    # controllo che il path esista
    if(not os.path.exists(dir_music)):
        messagebox.showinfo("Info", f"This directory `{dir_music}` does not exist. Click the settings button and chose a valid path.")
    else:
        list_music = os.listdir(dir_music)

    list_box = tk.Listbox(listbox_frame, selectbackground="sky blue", selectmode="SINGLE")
    list_box.pack(side="top", fill=tk.BOTH, expand=1)
    id = 1
    for song in list_music:
        list_box.insert(id, song)
        id += 1

    utility.add_listbox_widget(list_box)

    slider_song = tk.Scale(slider_frame, from_=0, to=0, orient=tk.HORIZONTAL, length=400, showvalue=False)
    slider_song.pack(side="left")

    lab_curr_time = tk.Label(slider_frame, text="--:--")
    lab_curr_time.pack(side="left")
    lab_len_song = tk.Label(slider_frame, text="--:--")
    lab_len_song.pack(side="left")

    player = Player(utility, play_button, list_box, list_music, lab_len_song,
                    lab_curr_time, slider_song, lab_name_song, slider_volume,
                    next_button, previous_button)

    root.iconphoto(False, play_icon)

    menubar = tk.Menu(root)
    menubar.add_command(label="Settings", command=lambda : player.change_music_path_from_settings(player))

    root.config(menu=menubar)

    root.mainloop()

if __name__ == "__main__":
    main()
