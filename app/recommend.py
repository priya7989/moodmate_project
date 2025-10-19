from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from transformers import pipeline
import random


# Emotion to genre mapping dictionary
emotion_genre_map = {
    "happy": ["pop", "dance", "indie"],
    "sad": ["acoustic", "piano", "soul"],
    "angry": ["rock", "metal", "hip-hop"],
    "surprise": ["electronic", "edm", "alternative"],
    "neutral": ["chill", "ambient", "lo-fi"]
}

# Spotify client initialization (replace with your credentials)
sp = Spotify(auth_manager=SpotifyOAuth(
    client_id='b236e8dcb93b401a82cfd275426765ae',
    client_secret='dd30e57243c942589779e153e7e42682',
    redirect_uri='http://127.0.0.1:8888/callback',
    scope='user-read-private'
))

# Huggingface emotion classification pipeline
emotion_classifier = pipeline(
    "text-classification",
    model="boltuix/bert-emotion",
    top_k=None,
    function_to_apply="softmax"
)

def search_tracks_by_genre(genre, limit=5):
    results = sp.search(q=f'genre:"{genre}"', type='track', limit=limit)
    tracks = []
    for track in results['tracks']['items']:
        tracks.append({
            "name": track['name'],
            "artist": track['artists'][0]['name'],
            "url": track['external_urls']['spotify']
        })
    return tracks


def recommend_music_for_emotion(emotion_label, n_songs=5):
    genres = emotion_genre_map.get(emotion_label, ['pop'])
    # Pick a random genre from the list associated with the emotion
    genre = random.choice(genres)
    return search_tracks_by_genre(genre, n_songs)

def detect_emotion(text):
    results = emotion_classifier(text)[0]
    top_result = max(results, key=lambda x: x['score'])
    emotion = top_result['label'].lower()
    confidence = top_result['score']
    return emotion, confidence
