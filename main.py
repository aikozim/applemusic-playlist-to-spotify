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
        songs: list(AppleSong) =  get_songs_from_apple_playlist(playlist['applemusic_playlist_url'])

        # Get the Spotify uris for the songs
        spotify_uris = get_spotify_uris(songs, spAuth)
        
        # Create the playlist
        create_spotify_playlist(spAuth, spotify_uris, songs, playlist['spotify_playlist_id'])


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
    
def create_spotify_playlist(auth: SpotifyAuth, song_uris, songs, playlist_id):
    # Create the playlist
    r = requests.put(f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks', 
                     headers={'Authorization': f'Bearer {auth.token}'}, 
                     data=json.dumps({'uris': song_uris}))
    
    # Check if the request was successful and Print the output
    if(r.status_code == 201):
        print(f'\033[32m Playlist with length of {len(song_uris)} songs Updated!')
        print(f'\033[32m Original Playlist length: {len(songs)}')
        print(f'\033[32m Could not find uris for {len(songs) - len(song_uris)} songs')
        print('\n \n')
    else:
        print(f'\033[31m Could not add songs to playlist: {r.text}')

def get_songs_from_apple_playlist(url: str):
    r =  requests.get(url)
    
    # Check if the request was successful
    if r.status_code == 200:
        print(f'\033[32m Found playlist!')
    else:
        print(f'\033[31m there was an error while getting playlist: {r.text}')
        pass
    
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # get table with songs
    divs = soup.select('div.songs-list-row, div.songs-list-row--web-preview web-preview, div.songs-list-row--two-lines, div.songs-list-row--song')
    
    # Create a list of songs
    songs = []
    for div in divs:
        title = re.sub("[\(\[].*?[\)\]]", "", div.find('div', {'class': 'songs-list-row__song-name'}).text)
        artists = [artist.text for artist in div.find('div', {'class': 'songs-list__col--secondary'}).find_all('a')]
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
            print(f'\033[31m Error while searching for song: {song.search_str()}')

        data = r.json()

        if(r.status_code != 200 and r.status_code != 201 and r.status_code != 404):
            print(f'\033[31m Error while searching for song: {song.search_str()}')

        if len(data['tracks']['items']) == 0:
            print(f'\033[33m ######## Could not find uri for {song.search_str()}')
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
                print(f'\033[34m {len_diff}:{title_diff} \033[0m {apple_name} vs. {spotify_name}')

                if(is_last):
                    print(f'\033[33m ######## Could not find uri for {song.search_str()}')
                continue

    return list
    

def normalize_string(string: str) -> str:
    string = string.lower()
    string = re.sub('[^a-z0-9 ]', '', string)
    string = re.sub("[\(\[].*?[\)\]]", "", string)

    return string
    

main()