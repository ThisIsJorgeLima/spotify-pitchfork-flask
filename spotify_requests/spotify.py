from __future__ import print_function
import base64
import json
import requests
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn import preprocessing

# Workaround to support both python 2 & 3
try:
    import urllib.request, urllib.error
    import urllib.parse as urllibparse
except ImportError:
    import urllib as urllibparse

# Set up Spotify API base URL
SPOTIFY_API_BASE_URL = 'https://api.spotify.com'
API_VERSION = "v1"
SPOTIFY_API_URL = "{}/{}".format(SPOTIFY_API_BASE_URL, API_VERSION)

# Set up authorization URL
SPOTIFY_AUTH_BASE_URL = "https://accounts.spotify.com/{}"
SPOTIFY_AUTH_URL = SPOTIFY_AUTH_BASE_URL.format('authorize')
SPOTIFY_TOKEN_URL = SPOTIFY_AUTH_BASE_URL.format('api/token')

# Client keys
CLIENT = json.load(open('conf.json', 'r+'))
CLIENT_ID = CLIENT['id']
CLIENT_SECRET = CLIENT['secret']

# Server side parameters, which should be changed accordingly in Spotify dev account
CLIENT_SIDE_URL = "http://127.0.0.1"
PORT = 8081
REDIRECT_URI = "{}:{}/callback/".format(CLIENT_SIDE_URL, PORT)
SCOPE = "user-top-read"
STATE = ""
SHOW_DIALOG_bool = True
SHOW_DIALOG_str = str(SHOW_DIALOG_bool).lower()

# https://developer.spotify.com/web-api/authorization-guide/
auth_query_parameters = {
    "response_type": "code",
    "redirect_uri": REDIRECT_URI,
    "scope": SCOPE,
    "client_id": CLIENT_ID
}

# Generate URL for Spotify API call
URL_ARGS = "&".join(["{}={}".format(key, urllibparse.quote(val))
                     for key, val in list(auth_query_parameters.items())])
AUTH_URL = "{}/?{}".format(SPOTIFY_AUTH_URL, URL_ARGS)


# Returns authorization header in URL, which allows request to API
def authorize(auth_token):

    code_payload = {
        "grant_type": "authorization_code",
        "code": str(auth_token),
        "redirect_uri": REDIRECT_URI
    }

    base64encoded = base64.b64encode(("{}:{}".format(CLIENT_ID, CLIENT_SECRET)).encode())
    headers = {"Authorization": "Basic {}".format(base64encoded.decode())}

    post_request = requests.post(SPOTIFY_TOKEN_URL, data=code_payload, headers=headers)

    # Return access token
    response_data = json.loads(post_request.text)
    access_token = response_data["access_token"]

    # use the access token to access Spotify API
    auth_header = {"Authorization": "Bearer {}".format(access_token)}
    return auth_header


# https://developer.spotify.com/web-api/get-users-top-artists-and-tracks/
def get_users_top(auth_header, t):
    if t not in ['artists', 'tracks']:
        print('invalid type')
        return None
    url = 'https://api.spotify.com/v1/me/top/tracks?limit=' + '50' + '&time_range=' + 'medium_term'
    r_tt = requests.get(url, headers=auth_header)
    tt_json = r_tt.json()
    track_list = []
    track_ids = []

    for x in range(0, tt_json['limit']):
        track_name = tt_json['items'][x]['name']
        track_id = tt_json['items'][x]['id']
        track_album = tt_json['items'][x]['album']['name']
        track_artist = tt_json['items'][x]['artists'][0]['name']

        track = {'name':track_name,
                 'artist':track_artist,
                 'album':track_album,
                 'id':track_id}

        track_list.append(track)
        track_ids.append(track_id)

    return track_list, track_ids


# https://developer.spotify.com/web-api/track-endpoints/
GET_TRACK_ENDPOINT = "{}/{}".format(SPOTIFY_API_URL, 'tracks')  # /<id>


# https://developer.spotify.com/web-api/get-track/
def get_track(track_id):
    url = "{}/{id}".format(GET_TRACK_ENDPOINT, id=track_id)
    resp = requests.get(url)
    return resp.json()


# https://developer.spotify.com/web-api/get-several-tracks/
def get_several_tracks(list_of_ids):
    url = "{}/?ids={ids}".format(GET_TRACK_ENDPOINT, ids=','.join(list_of_ids))
    resp = requests.get(url)
    return resp.json()


# https://developer.spotify.com/documentation/web-api/reference/tracks/get-several-audio-features/
def get_audio_features(auth_header, track_ids):  # track_ids = list of track ids generated from 'get_users_top'

    GET_AUDIOFEAT_ENDPOINT = "{}/{}".format(SPOTIFY_API_URL, 'audio-features/?ids=')  # /<track id>

    url= GET_AUDIOFEAT_ENDPOINT  # generate URL to query track ids
    for id in track_ids:
        url = url + id + ','

    r_tt = requests.get(url, headers=auth_header)  # Get JSON of each track's audio features
    tt_json = r_tt.json()

    # Define which features you want to keep
    features = ['acousticness', 'danceability', 'energy', 'instrumentalness',
                'liveness', 'loudness', 'speechiness', 'tempo', 'mode',
                'valence']

    # Convert results to dataframe
    df_trackfeat = pd.DataFrame(tt_json['audio_features'])
    df_trackfeat_matrix = df_trackfeat[features]

    # make weights, where ranking of most-played song receives higher weight
    weights = np.linspace(0.02, 1, num=50)  # evenly spaced weights, 0-1; num = track limit given to Spotify
    weights = np.flip(weights, axis=0)  # change to descending order

    # Generate weighted average of audio features
    weighted_average = df_trackfeat_matrix.multiply(weights, axis=0).sum() * 10 / (len(df_trackfeat_matrix) / 2)

    # Connect to SQLite database & import as dataframe
    engine = create_engine('sqlite:///pitchfork_authors.db')
    connection = engine.connect()
    sql = "SELECT * FROM mytable"
    df = pd.read_sql(sql, connection)
    df = df.drop('index', axis=1)

    # 1. Make difference matrix
    df_difference = pd.DataFrame.copy(df.drop('author_fullname', axis=1))

    for feature in df_difference.columns:
        df_difference[feature] = abs(df[feature] - weighted_average[feature])  # absolute value of features
        # 2. Scale features
        min_max_scaler = preprocessing.MinMaxScaler()
        df_difference[feature] = min_max_scaler.fit_transform(df_difference[feature].values.reshape(-1, 1))
        # 3. Average each critic's feature differences from user's
    average_difference = df_difference.mean(axis=1)
    # 4. Take least-different critic ('best critic')
    best_critic = average_difference.idxmin()
    best_critic = df['author_fullname'].loc[best_critic]

    return best_critic
