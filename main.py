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
        print(f'\033[94m Getting playlist {playlist["nickname"]} on Apple Music... \033[90m')
        songs: list(AppleSong) =  get_songs_from_apple_playlist(playlist["applemusic_playlist_url"])

        # Clear old songs in Playlist
        print(f'\033[94m Clearing old songs from Spotify playlist... \033[90m ')
        clear_spotify_playlist(spAuth, playlist)

        # Add new songs to playlist
        print(f'\033[94m Adding new songs to playlist... \033[90m ')
        add_songs_to_spotify_playlist(spAuth, playlist['spotify_playlist_id'], songs)
        

class AppleSong:
    def __init__(self, title: str, artists: list, length: int):
        self.title = title.strip()
        self.artists = artists
        self.length = length
    
    
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


def get_songs_from_apple_playlist(playlist_url):
    r = requests.get(playlist_url)
    
    if r.status_code != 200:
        print(f'\033[32m Error while getting the playlist: {r.text}')
        return []
    
    soup = BeautifulSoup(r.content, 'html.parser')
    
    songs = []
    song_meta_tags = soup.find_all('meta', property=re.compile(r"^music:song$"))

    # Scrape songdata for each song
    for tag in song_meta_tags:
        # retry 3 times if there is an issue
        for attempt in range(3):
            try:
                song_url = tag['content']

                r = requests.get(song_url)
                if r.status_code != 200:
                    print(f'\033[93m Could not get songinfo for: {song_url} ({r.status_code}) retrying...  \033[90m')
                    continue

                soup = BeautifulSoup(r.content, 'html.parser')

                # Find the server data script tag by its type and id
                script_tag = soup.find('script', {'type': 'application/json', 'id': 'serialized-server-data'})

                # Extract the JSON content from the script tag
                json_data = script_tag.string
                data = json.loads(json_data)

                song_title = data[0]['data']['sections'][0]['items'][0]['title']
                song_length_ms = data[0]['data']['seoData']['ogSongs'][0]['attributes']['durationInMillis']
                artists_string = data[0]['data']['sections'][0]['items'][0]['artists']
                artists = artists_string.split(', ')


                print(f"Fetched AppleMusic data for {song_title} by {artists}")

                songs.append(AppleSong(song_title, artists, song_length_ms))
            except:
                print(f'\033[93m Could not get songinfo for: {song_url} ({r.status_code}) retrying...  \033[90m')
                continue
            else:
                break
        else:
            print(f"\033[91m There seems to be an permanent issue while fetching: {song_url}  \033[90m")

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
            len_diff = song.length - item['duration_ms'] # difference in length
            title_diff = SequenceMatcher(None, spotify_name, apple_name).ratio() # difference in title
            same_title = apple_name in spotify_name or spotify_name in apple_name

            if len_diff < 1500 and len_diff > -1500 and (same_title or title_diff > 0.8):
                list.append(item['uri'])
                break
            elif len_diff < 15 and len_diff > -15:
                list.append(item['uri'])
                break
            else:
                if(config.debug):
                    print(f'\033[0m [DEBUG] Songs not matching: \033[34m {apple_name} \033[0m vs. \033[34m {spotify_name} (\033[90m len_dif:{len_diff} title_dif:{title_diff} \033[0m)')

                if(is_last):
                    print(f'\033[33m Could not find any Spotify matches for {song.search_str()}')
                continue

    return list
    

def normalize_string(string: str) -> str:
    string = string.lower()
    string = re.sub('[^a-z0-9 ]', '', string)
    string = re.sub("[\(\[].*?[\)\]]", "", string)

    return string
    

main()