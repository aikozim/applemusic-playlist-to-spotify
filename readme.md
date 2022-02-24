# Apple Music playlists to Spotify

## Functions:
- Scrape songs from Apple Music Playlist URL
- Match scraped songs with songs from Spotify
- Update Spotify playlist with the help of the Spotify API
- refresh Spotify API token when needed

## Setup
1. Install dependencies with `pip install -r requirements.txt`
2. Create a `config.py` file in the root directory
2. Create your own Spotify application at https://developer.spotify.com/dashboard and set the Callback URL to `http://localhost:8080`. Then fill in the `client_id` and `client_secret` from your new application into the `config.py` file
3. get your own refresh token using your application and this tutorial:  https://benwiz.com/blog/create-spotify-refresh-token/ and add it to the `refresh_token` in `config.py`. Make sure to set the $SCOPE during the tutorial to `playlist-modify-private`
4. Create the Spotify playlists you want to mirror and fill the information in `config.py`. When done it should look something like this:

``` python
# https://developer.spotify.com/dashboard
client_id = 'xxx'
client_secret = 'xxx'

# https://benwiz.com/blog/create-spotify-refresh-token/
refresh_token = 'xxx'


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

5. Start the script using `python3 main.py` in the terminal. It should start the script and mirror all the Playlists once. If you want to do this regularly you have to set up some kind of scheduler like cron to run the script.


## ToDo
- Descriptions