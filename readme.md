# Python Script for Cloning Apple Music Playlists to Spotify

## Overview

A Script, designed to automatically copy your favorite Apple Music playlists to Spotify. 

### Heads-up

Apple Music frequently updates how they format song information on their pages. This can sometimes make my script stop working. If you experience any issues you can take a look into the `get_songs_from_apple_playlist` function in the `main.py` file. Feel free to fix it and send me a Pull Request. I really appreciate every help in keeping everything running smoothly!

## Features

The following features are done automatically:

1. **Song Scraping**: The script will scrape songs from your Apple Music Playlist URLs.

2. **Song Matching**: The script matches scraped songs with songs available on Spotify.

3. **Spotify Playlist Update**: The script updates Spotify playlist with the help of the Spotify API.

4. **Token Refresh**: The Spotify API token is refreshed automatically when needed, so users do not have to worry about manually refreshing the token.

## Setup

To use the script, follow the steps below:

1. Install dependencies with `pip install -r requirements.txt`.

2. Create a `config.py` file in the root directory. You clone the `config.template.py` file to do so.

3. Create your own Spotify application at https://developer.spotify.com/dashboard and set the Callback URL to `http://localhost:8080`. Then fill in the `client_id` and `client_secret` from your new application into the `config.py` file.
``` python
# https://developer.spotify.com/dashboard
client_id = 'xxx'
client_secret = 'xxx'
```

4. Get your own refresh token using your application and this tutorial:  https://benwiz.com/blog/create-spotify-refresh-token/ and add it to the `refresh_token` in `config.py`. Make sure to set the $SCOPE during the tutorial to `playlist-modify-private`.

``` python
# https://benwiz.com/blog/create-spotify-refresh-token/
refresh_token = 'xxx'
```

5. Create the Spotify playlists you want to mirror and fill in the information in `config.py`.
``` python
# https://open.spotify.com/playlist/4C0kEXdGkLuIDaBSVRjwpr?...
#                                           ^ This is the playlist id
playlists = [
    {
        'applemusic_playlist_url': 'https://music.apple.com/us/playlist/xxx/pl.xxx',
        'spotify_playlist_id': 'xxx',
    },
    {
        'applemusic_playlist_url': 'https://music.apple.com/us/playlist/xxx/pl.xxx',
        'spotify_playlist_id': 'xxx',
    },
]
```

6. Start the script using `python3 main.py` in the terminal. The application will start mirroring all the playlists once. If you want to do this regularly, you can set up a scheduler like cron to run the script.

7. Feel free to enable debug mode in the config if you want to see why songs are not matching.
 ``` python
debug = True
```   


## ToDo (Please Send a PR, in case you anything)

The following tasks still need to be completed:

1. Cloning of image and description of playlists
