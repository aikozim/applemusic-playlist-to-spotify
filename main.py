from bs4 import BeautifulSoup
from auth import SpotifyAuth
from helpers import signal_last
from difflib import SequenceMatcher
import requests, re, json, config

def main():
    # Get Spotify authetication
    spAuth = SpotifyAuth()
    spAuth.get_new_token()
    
    # loop through playlists from config
    for playlist in config.playlists:
        
        # Get songs from Apple Music playlist
        print(f'\033[90m Getting playlist {playlist["nickname"]} on Apple Music...')
        songs: list(AppleSong) =  get_songs_from_apple_playlist(playlist)

        # Clear old songs in Playlist
        print(f'\033[90m Clearing old songs from Spotify playlist...')
        clear_spotify_playlist(spAuth, playlist)

        # Add new songs to playlist
        print(f'\033[90m Adding new songs to playlist...')
        add_songs_to_spotify_playlist(spAuth, playlist['spotify_playlist_id'], songs)
        

class AppleSong:
    def __init__(self, title: str, artists: list, length: str):
        self.title = title.strip()
        self.artists = artists
        self.length = length.strip()
        
    def length_in_ms(self) -> int:
        string = self.length
        return int(string.split(':')[0]) * 60 * 1000 + int(string.split(':')[1]) * 1000
    
    def search_str(self) -> str:
        artists = " ".join(self.artists).strip()
        title = self.title.strip()
                
        return f'{title} {artists}'


def clear_spotify_playlist(auth:SpotifyAuth, playlist_id):
    r = requests.put(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks',
                headers={'Authorization': f'Bearer {auth.token}',
                }, data=json.dumps({'uris': []}))

    # Check if the request was successful and Print the output
    if(r.status_code == 201):
        print(f'\033[32m Playlist cleared!')


def add_songs_to_spotify_playlist(auth: SpotifyAuth, playlist_id, songs: AppleSong):
    # Separate the songs into lists of 100 to avoid the 100 limit of the Spotify API
    separeted_songs = [songs[i:i+99] for i in range(0, len(songs), 99)]

    updated_songs = 0

    for song_list in separeted_songs:
        song_uris = get_spotify_uris(song_list, auth)

        r = requests.post(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', 
                        headers={
                            'Content-Type': 'application/json',
                            'Accept': 'application/json',
                            'Authorization': f'Bearer {auth.token}',
                            }, 
                        data=json.dumps(song_uris))
        
        # Check if the request was successful and Print the output
        if(r.status_code == 201):
            updated_songs += len(song_uris)
        else:
            print(f'\033[31m Could not add songs to playlist: {r.content}')
            pass

    print(f'\033[32m {updated_songs} songs Updated!')
    if(len(songs) - updated_songs > 0):
        print(f'\033[32m Could not find uris for {len(songs) - updated_songs} songs')
    print(f'\n\n')



def get_songs_from_apple_playlist(playlist):
    r =  requests.get(playlist['applemusic_playlist_url'])
    
    # Check if the request was successful
    if r.status_code != 200:
        print(f'\033[31m there was an error while getting playlist {playlist["nickname"]} on Apple Music: {r.text}')
        pass
    
    soup = BeautifulSoup(r.content, 'html.parser')
    
    # get table with songs
    divs = soup.find_all('div', {'class': 'songs-list-row'})
    
    # Create a list of songs
    songs = []
    for div in divs:
        title = re.sub("[\(\[].*?[\)\]]", "", div.find('div', {'class': 'songs-list-row__song-name'}).text)
        artists = [artist.text for artist in div.find('div', {'class': 'songs-list-row__by-line'}).find_all('a')]
        length = div.find('time', {'class': 'songs-list-row__length'}).text.strip()
        
        songs.append(AppleSong(title, artists, length))
    
    return songs 

def get_spotify_uris(songs, auth: SpotifyAuth):
    list = []
    
    for song in songs:
        # Make search request to Spotify
        try:
            r = requests.get(f'https://api.spotify.com/v1/search?q={song.search_str()}&type=track', 
                            headers={'Authorization': f'Bearer {auth.token}'}) 
        except:
            print(f'\033[31m Internal error while searching for song: {song.search_str()}')

        data = r.json()

        if(r.status_code != 200 and r.status_code != 201 and r.status_code != 404):
            print(f'\033[31m Spotify API Error while searching for song: {song.search_str()}. ({r.status_code} {r.json()["error"]["message"]})')
            continue

        if len(data['tracks']['items']) == 0:
            print(f'\033[33m No results for spotify search:  {song.search_str()}')
            continue

        # Loop through the results and get the uri of the first match
        for is_last, item in signal_last(r.json()['tracks']['items']):

            # Normalize the Titles 
            spotify_name = normalize_string(item['name'])
            apple_name = normalize_string(song.title)

            # Compare the songs
            len_diff = song.length_in_ms() - item['duration_ms'] # difference in length
            title_diff = SequenceMatcher(None, spotify_name, apple_name).ratio() # difference in title
            same_title = apple_name in spotify_name or spotify_name in apple_name

            if len_diff < 1500 and len_diff > -1500 and (same_title or title_diff > 0.8):
                list.append(item['uri'])
                break
            else:
                if(config.debug):
                    print(f'\033[0m [DEBUG] Songs not matching: \033[34m {apple_name} \033[0m vs. \033[34m {spotify_name} (\033[90m len_dif:{len_diff} title_dif:{title_diff} \033[0m)')

                if(is_last):
                    print(f'\033[33m Could not find any matches for {song.title} by {song.artists}')
                continue

    return list
    

def normalize_string(string: str) -> str:
    string = string.lower()
    string = re.sub('[^a-z0-9 ]', '', string)
    string = re.sub("[\(\[].*?[\)\]]", "", string)

    return string
    

main()