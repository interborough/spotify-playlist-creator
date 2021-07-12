# Spotify Playlist Creator
A Python script that creates and populates a Spotify playlist based on MP3 files that are inputted by the user.

This script will prompt you for a selection of one or more MP3 files through a file selection menu. After selecting your files, you will be prompted to login to Spotify. A Spotify playlist will be created containing all of the songs that you selected. 

The MP3 files that you use for this script must have the appropriate metadata embedded into them, as the script determines both the song title and song artist using the corresponding metadata fields (the `Title` and `Contributing Artists` fields need to be filled out). If your MP3 files do not have any metadata information embedded into them, you can use my [MP3 Metadata Autofiller](https://github.com/interborough/mp3-metadata-autofiller) script to obtain the fields needed for this script to function.  

# Dependencies
For this program to function correctly you must have Python installed, along with the spotipy, mutagen, and keyboard libaries for Python.

- Download Python: https://www.python.org/downloads/
- Install spotipy: `pip install spotipy`
- Install mutagen: `pip install mutagen`
- Install keyboard: `pip install keyboard`

# First Time Setup
- Download and install Python, along with the other relevant dependencies as outlined above. 
- Download the zip file of the spotify-playlist-creator Github archive, and extract it to a folder. 
- Create a Spotify account (if you don't have one already), log in, and navigate to the following link: https://developer.spotify.com/dashboard/
- Click on the "Create an App" button on the top right corner of the page. 
- Enter a name and description for your app (it can be anything you'd like) and click on the "Create" button.
- You should be redirected to a seperate page for your app. Click on the "Edit Settings" button, and a menu should pop up. Scroll down within this sub-menu until you see a section titled "Redirect URIs". Enter the following URL: `https://open.spotify.com/`, and click on the "Add" button. After adding the URI, click on the "Save" button (which can be found on the bottom right of the menu).  
- Underneath the title and description for your app, there should be a "Client ID", and a "Client Secret" value (you may have to click the text labeled "Show Client Secret" to see the Client Secret value). 
- Edit lines 20 and 21 in the playlist.py script, replacing the "PLACEHOLDER" text with your Client ID and Client Secret values (ex: `client_id = "PLACEHOLDER"` should become `client_id = "YOUR_CLIENT_ID_VALUE"`, and `client_secret = "PLACEHOLDER"` should become `client_secret = "YOUR_CLIENT_SECRET_VALUE"`, where you substitute in your Cilent ID and Client Secret values accordingly).

# How to Use
- Complete the steps outlined in the "First Time Setup" section above. 
- Run a terminal window in the folder that you extracted the zip file to, and enter `python playlist.py`.
- Follow the on screen prompts to enter your playlist name and whether the playlist should be public or private. 
- A file selection window will appear. Select the MP3 files that you wish to add to your Spotify playlist. Ensure that these files have the proper metadata embedded into them. 
- After selecting your files, you will be prompted to login to Spotify. Login, and grant the relevant permissions to this script. 
- After logging in, you will be redirected to the Spotify Web Player. Copy the URL, and paste it into the console when prompted for a redirect URL.
- The playlist will then be created, and the songs will be added to it.  
- After the script is complete, the names of any songs that had issues being added to the playlist will be output to the console. The console will specify whether these songs had missing metadata, whether they could not be found on Spotify, or whether they were found on Spotify using only their titles (in which case they should be manually checked to ensure that they are the correct version of the song - see the Troubleshooting section for more details). 

# Troubleshooting
If the script is unable to locate a song, here are a few things to try or take note of. 

- Not every song is on Spotify. If the script can't find a particular song, check to make sure that the song you're looking for is actually on Spotify. 
- A bug exists in the Spotify API itself. If a song title has special characters (things like apostrophes, quotation marks, or non-English letters), and you provide both the song title and the artist into a search query, then the query will break and always return no results. To solve this issue, this script checks whether a song title has special characters, and only searches using the song title if this is the case. This works as intended. However, this means that if your song has both special characters and a very commonly used song title, then Spotify may confuse the song you are looking for with another song with the same title. The script will output the names of all of the songs that are searched for using only their titles, so you can quickly check the generated playlist manually to see if there are any issues with those particular songs. If the script did fetch the incorrect song, try adding the correct song to your playlist manually. Other than that, however, there's not much I can do about the issue seeing as the bug exists within the API itself.
- Some songs on Spotify aren't available in all markets. The Spotify search function searches the US market by default, but if you're not finding your song you can override this behavior. To do this, edit lines 124 and 127 of the playlist.py script to include a "market" parameter in the search query. 
    - ex: `track_query = spotify.search(q="artist:" + song.artist + " track:" + song.title, limit=1)` can become `track_query = spotify.search(q="artist:" + song.artist + " track:" + song.title, limit=1, market="GB")` to search the Great Britain market.
    - A list of valid market values can be found at the following link: https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
