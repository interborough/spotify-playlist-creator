import sys
import re

import tkinter
from tkinter.filedialog import askopenfilenames

from string import ascii_letters, digits, whitespace

import keyboard

import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError

from mutagen.id3 import ID3NoHeaderError
from mutagen.mp3 import MP3, HeaderNotFoundError


def main():
    # Replace these two variables with your own id values.
    client_id = "PLACEHOLDER"
    client_secret = "PLACEHOLDER"

    # Get user input and MP3 files.
    playlist_name, playlist_status, files = get_input()
    redirect_uri = "https://open.spotify.com/"

    # Determine API scope depending upon the whether the playlist is public or private.
    if playlist_status.lower() == 'y':
        scope = 'playlist-modify-public'
        is_public = True
    else:
        scope = "playlist-modify-private"
        is_public = False

    # Get access to the Spotify APU using the Authorization Code Flow.
    spotify = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id, client_secret=client_secret,
                                                        redirect_uri=redirect_uri, scope=scope))

    # Look up each song using the Spotify API.
    track_ids, manual_check_list, not_found_list, no_metadata_list = get_song_ids(files, spotify)

    # If there are no tracks in the tracks_ids list, exit the script.
    if len(track_ids) == 0:
        print("No valid tracks are available to add to the playlist. The script will now close.\n")
        exit_routine()

    # Get access to the current user and create a new playlist.
    user = spotify.current_user()
    user_id = user['id']
    playlist = spotify.user_playlist_create(user=user_id, name=playlist_name, public=is_public)
    print(f"\n\"{playlist_name}\" playlist created successfully.")

    # Get the newly created playlist's ID and then add all of the tracks to it.
    playlist_id = playlist["id"]
    spotify.playlist_add_items(playlist_id=playlist_id, items=track_ids)

    # Inform user of errors that occurred, and then exit.
    print_errors(manual_check_list, not_found_list, no_metadata_list)
    print("\nScript complete! For more detailed information on what was done, along with potential issues that may "
          "have occurred, see the console output above. Thank you for using the Spotify Playlist Creator.")
    exit_routine()


def get_input():
    playlist_name = input("Enter the title of the playlist you wish to create:\n").strip()

    # If the user doesn't input anything, keep asking until they do.
    while playlist_name == "":
        playlist_name = input("Enter the title of the playlist you wish to create:\n").strip()

    playlist_status = input("Would you like to make this playlist public? Type 'Y' to make the playlist public, or 'N' "
                            "to make the playlist private:\n").strip()

    # If the user input isn't a "y" or "n", keep asking them until it is.
    while playlist_status.lower() != 'y' and playlist_status.lower() != 'n':
        playlist_status = input(
            "Would you like to make this playlist public? Type 'Y' to make the playlist public, or 'N' to make the "
            "playlist private:\n").strip()

    print("Please select the MP3 file(s) you wish to add to your new Spotify playlist.")
    tkinter.Tk().withdraw()
    files = askopenfilenames()

    # If the user doesn't select any files, keep asking them to select files until they do.
    while len(files) == 0:
        print("You did not select any files! Please select at least one file to add to your playlist.")
        tkinter.Tk().withdraw()
        files = askopenfilenames()

    return playlist_name, playlist_status, files


def get_song_ids(files, spotify):
    track_id_list = []
    manual_check_list = []
    not_found_list = []
    no_metadata_list = []

    # Try to get the song name and artist from the MP3 file.
    for file in files:
        try:
            mp3_file = MP3(file)
            song_title = str(mp3_file['TIT2'])
            song_artist = str(mp3_file['TPE1'])
        except (KeyError, ID3NoHeaderError, HeaderNotFoundError) as e:
            no_metadata_list.append(file)
            continue

        song_title_backup = song_title

        # If there is a apostrophe in the song title, remove it (to prevent the Spotify query from breaking)
        if "'" in song_title:
            song_title = song_title.replace("'", "")

        # If the song is marked as "remastered", remove this designation to increase the possibility of a match being
        # found.
        if "remastered" in song_title.lower() or "remaster" in song_title.lower():
            song_title = re.sub(r'\([^)]*\)$', '', song_title)

        # If the song has special characters, search for the song only by its title. Otherwise search by title and
        # artist.
        try:
            if set(song_title).difference(ascii_letters + digits + whitespace):
                track_query = spotify.search(q=song_title, limit=1)
                manual_check_list.append(song_artist + " - " + song_title_backup)
            else:
                track_query = spotify.search(q="artist:" + song_artist + " track:" + song_title, limit=1)
        except SpotifyOauthError:
            print("There was an error authenticating your Spotify account. Please try again, and ensure that you "
                  "enter the correct redirect url.\n")
            exit_routine()

        # Try to get the Spotify ID for the current song.
        try:
            track_id = track_query['tracks']['items'][0]['id']
            track_id_list.append(track_id)
        except IndexError:
            not_found_list.append(song_artist + " - " + song_title_backup)
            continue

    return track_id_list, manual_check_list, not_found_list, no_metadata_list


def print_errors(manual_check_list, not_found_list, no_metadata_list):
    if len(no_metadata_list) > 0:
        print("\nThe script was unable to read metadata for the following files. Please ensure that the files have "
              "the proper metadata required for this script to work.\n")

        for file in no_metadata_list:
            print(file)

    if len(not_found_list) > 0:
        print("\nThe following songs were not found on Spotify. Try adding them to your playlist manually.\n")

        for song in not_found_list:
            print(song)

    if len(manual_check_list) > 0:
        print("\nThe following songs were found on Spotify only using their titles (due to them having special "
              "characters in their titles). It is highly recommended to manually check each of the following songs in "
              "the playlist to ensure that they are correct.\n")

        for song in manual_check_list:
            print(song)


def exit_routine():
    print("Press the \"Q\" key to quit.")

    while True:
        if keyboard.is_pressed("q"):
            sys.exit(0)


main()
