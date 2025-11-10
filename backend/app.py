from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from spotipy.oauth2 import SpotifyOAuth
import os
from dotenv import load_dotenv
import spotipy

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

sp_oauth = SpotifyOAuth(
    client_id=os.getenv('SPOTIFY_CLIENT_ID'),
    client_secret=os.getenv('SPOTIFY_CLIENT_SECRET'),
    redirect_uri=os.getenv('REDIRECT_URI'),
    scope='playlist-read-private playlist-modify-public playlist-modify-private user-library-read'
)

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return jsonify({'auth_url': auth_url})

@app.route('/callback')
def callback():
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    return redirect(f'http://127.0.0.1:3000?access_token={token_info["access_token"]}')

@app.route('/playlist/<playlist_id>')
def get_playlist(playlist_id):
    token = request.headers.get('Authorization').replace('Bearer ', '')
    sp = spotipy.Spotify(auth=token)
    
    results = sp.playlist_tracks(playlist_id)
    tracks = results['items']
    
    track_ids = [item['track']['id'] for item in tracks if item['track']]
    audio_features = sp.audio_features(track_ids)
    
    # Combine track info with audio features
    playlist_data = []
    for track, features in zip(tracks, audio_features):
        if track['track'] and features:
            playlist_data.append({
                'id': track['track']['id'],
                'name': track['track']['name'],
                'artist': track['track']['artists'][0]['name'],
                'album_art': track['track']['album']['images'][0]['url'] if track['track']['album']['images'] else None,
                'preview_url': track['track']['preview_url'],
                'audio_features': features
            })
    
    return jsonify(playlist_data)

@app.route('/recommend', methods=['POST'])
def recommend():
    data = request.json
    token = request.headers.get('Authorization').replace('Bearer ','')
    playlist_tracks = data['playlist_tracks']

    recs = get_recs(playlist_tracks,token)

    return jsonify(recs)

def get_recs(playlist_tracks, token):
    sp = spotipy.Spotify(auth=token)

    last_tracks = playlist_tracks[-5:]

    avg_features = {
        'danceability': sum(t['audio_features']['danceability'] for t in last_tracks) / len(last_tracks),
        'energy': sum(t['audio_features']['energy'] for t in last_tracks) / len(last_tracks),
        'valence': sum(t['audio_features']['valence'] for t in last_tracks) / len(last_tracks),
        'tempo': sum(t['audio_features']['tempo'] for t in last_tracks) / len(last_tracks),
    }

    seed_tracks = [t['id'] for t in last_tracks[:2]]
    seed_artists = list(set([t['artist'] for t in last_tracks[:3]]))

    recs = sp.recommendations(
        seed_tracks=seed_tracks,
        limit=20,
        target_danceability=avg_features['danceability'],
        target_energy=avg_features['energy'],
        target_valence=avg_features['valence'],
        target_tempo=avg_features['tempo']
    )

    formatted_recs = []
    for track in recs['tracks']:
        features = sp.audio_features([track['id']])[0]

        explanations = []
        if abs(features['energy'] - avg_features['energy']) < 0.15:
            explanations.append(f"Similar energy level ({int(features['energy']*100)}%)")
        if abs(features['valence'] - avg_features['valence']) < 0.15:
            explanations.append(f"Matches the mood")
        if abs(features['tempo'] - avg_features['tempo']) < 20:
            explanations.append(f"Similar tempo ({int(features['tempo'])} BPM)")
        
        formatted_recs.append({
            'id': track['id'],
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
            'preview_url': track['preview_url'],
            'audio_features': features,
            'explanations': explanations if explanations else ["Great fit for your playlist"],
            'confidence': calculate_confidence(features, avg_features)
        })

    return formatted_recs

def calculate_confidence(track_features, target_features):
    score = 0
    weights = {'danceability': 0.25, 'energy': 0.25, 'valence': 0.25, 'tempo': 0.25}

    for feature, weight in weights.items():
        if feature == 'tempo':
            similarity = 1 - min(abs(track_features[feature] - target_features[feature]) / 100, 1)
        else:
            similarity = 1 - abs(track_features[feature] - target_features[feature])
        score += similarity * weight
    
    return round(score * 100, 1)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
