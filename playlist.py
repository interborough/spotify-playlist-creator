import sys
import re
import unicodedata
import tkinter
from tkinter.filedialog import askopenfilenames
import keyboard
import spotipy
from spotipy.oauth2 import SpotifyOAuth, SpotifyOauthError
from mutagen.id3 import ID3NoHeaderError
from mutagen.mp3 import MP3, HeaderNotFoundError
from fuzzywuzzy import fuzz

def sanitize_string(input_string):
    # Remove non-ASCII characters and normalize
    normalized = unicodedata.normalize('NFKD', input_string).encode('ASCII', 'ignore').decode('ASCII')
    # Remove any remaining non-alphanumeric characters except spaces
    sanitized = re.sub(r'[^a-zA-Z0-9\s]', '', normalized)
    return sanitized.strip()

def main():
    # Replace these two variables with your own id values.
    client_id = "PLACEHOLDER"
    client_secret = "PLACEHOLDER"

    # Get user input and MP3 files.
    playlist_name, playlist_status, files = get_input()
    redirect_uri = "https://open.spotify.com/"

    # Determine API scope depending upon whether the playlist is public or private.
    if playlist_status.lower() == 'y':
        scope = 'playlist-modify-public'
        is_public = True
    else:
        scope = "playlist-modify-private"
        is_public = False

    # Get access to the Spotify API using the Authorization Code Flow.
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

    # Get the newly created playlist's ID and then add all the tracks to it.
    playlist_id = playlist["id"]

    # Add tracks in batches of 100
    for i in range(0, len(track_ids), 100):
        spotify.playlist_add_items(playlist_id=playlist_id, items=track_ids[i:i+100])

    # Inform user of errors that occurred, and then exit.
    print_errors(manual_check_list, not_found_list, no_metadata_list)
    print("\nScript complete! For more detailed information on what was done, along with potential issues that may "
          "have occurred, see the console output above. Thank you for using the Spotify Playlist Creator.")
    exit_routine()
    
playlist_name = "not set";

def get_input():
    playlist_name = input("Enter the title of the playlist you wish to create:\n").strip()
    while playlist_name == "":
        playlist_name = input("Enter the title of the playlist you wish to create:\n").strip()

    playlist_status = input("Would you like to make this playlist public? Type 'Y' to make the playlist public, or 'N' "
                            "to make the playlist private:\n").strip()
    while playlist_status.lower() not in ['y', 'n']:
        playlist_status = input("Would you like to make this playlist public? Type 'Y' to make the playlist public, or 'N' to make the "
                                "playlist private:\n").strip()

    print("Please select the MP3 file(s) you wish to add to your new Spotify playlist.")
    tkinter.Tk().withdraw()
    files = askopenfilenames()
    while len(files) == 0:
        print("You did not select any files! Please select at least one file to add to your playlist.")
        files = askopenfilenames()

    return playlist_name, playlist_status, files

def clean_tag(tag):
    tag = re.sub(r'\s*\((Original Mix|Official Audio|Official Lyric|Official Music|lyrics)\)', '', tag, flags=re.IGNORECASE) # Add more strings to be ignored here
    tag = re.sub(r'\s*\[[^\]]+\]', '', tag)
    tag = tag.replace('_', ' ')
    tag = re.sub(r'\s+', ' ', tag)
    tag = re.sub(r'\s*-\s*', ' ', tag)
    return tag.strip()

def clean_artist_name(artist):
    artist = re.sub(r'\b(\w)\s+(?=\w\b)', r'\1', artist)
    artist = re.sub(r'\s*feat\..*', '', artist)
    return artist.strip()

def process_mp3_tag(artist, track):
    artist = clean_tag(artist)
    track = clean_tag(track)
    
    if re.match(r'^\d+$', artist) or re.match(r'^\d+$', track):
        return None
    
    if artist.lower() == "unknown artist" and re.match(r'^(-+|\d+|track\d+)$', track, re.IGNORECASE):
        return None
    
    artist = clean_artist_name(artist)
    
    if not artist:
        return None
        
    # Check if artist has no alphabetical characters in any language
    if not any(char.isalpha() for char in artist):
        return None
    
    artist = unicodedata.normalize('NFKC', artist)
    track = unicodedata.normalize('NFKC', track)
    
    return artist, track

def get_song_ids(files, spotify):
    track_id_list = []
    manual_check_list = []
    not_found_list = []
    no_metadata_list = []

    for file in files:
        try:
            mp3_file = MP3(file)
            song_title = str(mp3_file.get('TIT2', ''))
            song_artist = str(mp3_file.get('TPE1', ''))
        except (KeyError, ID3NoHeaderError, HeaderNotFoundError) as e:
            no_metadata_list.append(file)
            continue

        print(f"Getting Info for {song_artist} - {song_title}")

        processed = process_mp3_tag(song_artist, song_title)
        if not processed:
            no_metadata_list.append(file)
            continue

        sanitized_artist, sanitized_title = processed
        
        
        # Replace '-' and '_' with spaces
        sanitized_title = sanitized_title.replace('-', ' ').replace('_', ' ').replace('.', ' ').replace(',', ' ').replace('&', ' ').replace('feat ', ' ')
        sanitized_artist = sanitized_artist.replace('-', ' ').replace('_', ' ').replace('.', ' ').replace(',', ' ').replace('&', ' ').replace('feat ', ' ')

        # Remove "remastered" designation and common words
        sanitized_title = re.sub(r'\([^)]*remaster(ed)?[^)]*\)$', '', sanitized_title, flags=re.IGNORECASE)
        sanitized_title = re.sub(r'\b(feat|ft|with)\b\.?\s*', '', sanitized_title, flags=re.IGNORECASE)
        
        print(f"Sanitized: {sanitized_artist} - {sanitized_title}")

        # Split artists for multiple artist tracks
        artists = [artist.strip() for artist in sanitized_artist.split(',')]

        # Try different search combinations
        search_queries = [
            f"artist:{' '.join(artists)} track:{sanitized_title}",
            f"artist:{artists[0]} track:{sanitized_title}",
            f"{' '.join(artists)} {sanitized_title}"
        ]

        track_id = None
        for query in search_queries:
            try:
                track_query = spotify.search(q=clean_query(query), limit=5)
                tracks = track_query['tracks']['items']
                
                if tracks:
                    # Use fuzzy matching to find the best match
                    best_match = max(tracks, key=lambda x: fuzz.partial_ratio(
                        f"{sanitized_title}".lower(),
                        f"{x['name']}".lower()
                    ))
                    print(f"checking {sanitized_artist} {sanitized_title}".lower())
                    if ((fuzz.partial_ratio(f"{sanitized_artist} {sanitized_title}".lower(),f"{best_match['artists'][0]['name']} {best_match['name']}".lower()) > 75) or (fuzz.partial_ratio(f"{sanitized_artist}".lower(),f"{best_match['name']}".lower()) > 62) or (fuzz.partial_ratio(f"{sanitized_title}".lower(),f"{best_match['artists'][0]['name']}".lower()) > 62)):  # Adjusted threshold
                        print(f"matched {best_match['artists'][0]['name']} {best_match['name']}".lower())
                        track_id = best_match['id']
                        break
                    else:
                        print(f"not matched {best_match['artists'][0]['name']} {best_match['name']}".lower())
            except SpotifyOauthError:
                print("There was an error authenticating your Spotify account. Please try again.")
                exit_routine()

        if track_id:
            track_id_list.append(track_id)
        else:
            not_found_list.append(f"{sanitized_artist} - {sanitized_title}")

    return track_id_list, manual_check_list, not_found_list, no_metadata_list

def clean_query(query):
    # Remove or replace special characters
    cleaned = re.sub(r'[^\w\s]', '', query)
    # Remove extra whitespace
    cleaned = ' '.join(cleaned.split())
    return cleaned

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
        f = open(f"{playlist_name}.txt", "w")
        f.write(manual_check_list)
        f.close()

def exit_routine():
    print("Press the \"Q\" key to quit.")
    while True:
        if keyboard.is_pressed("q"):
            sys.exit(0)

if __name__ == "__main__":
    main()
