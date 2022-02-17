import requests
import config

class SpotifyAuth:
    def __init__(self) -> None:
        self.client_id = config.client_id
        self.client_secret = config.client_secret
        self.refresh_token = config.refresh_token
        self.token = None
        
    def get_new_token(self):
        r = requests.post('https://accounts.spotify.com/api/token', 
                            data={
                                'grant_type': 'refresh_token',
                                'refresh_token': self.refresh_token,
                                'redirect_uri': 'http://localhost:8080',
                                'client_id': self.client_id,
                                'client_secret': self.client_secret
                            })
        
        if(r.status_code == 200):
            self.token = r.json()['access_token']
        else:
            print(f'Could not get token: {r.text}')