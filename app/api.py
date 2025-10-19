from fastapi import FastAPI, UploadFile, File, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from transformers import pipeline
from PIL import Image, UnidentifiedImageError
from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
import numpy as np
import io
import random


# ------------------ APP CONFIG ------------------
app = FastAPI(title="MoodMate API", description="Emotion detection via text or image + music recommendation")

origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------ MODEL LOADING ------------------
MODEL_PATH = r"D:\moodmate\output\fer2013_mobilenetv2_se_selu_finetuned - Copy.keras"
model = load_model(MODEL_PATH)
emotion_labels = ["angry", "happy", "sad", "neutral", "surprise"]

# Text classifier - Hugging Face
emotion_classifier = pipeline(
    "text-classification",
    model="boltuix/bert-emotion",
    top_k=None,
    function_to_apply="softmax"
)


# ------------------ SPOTIFY AUTH ------------------
sp = Spotify(auth_manager=SpotifyOAuth(
    client_id='b236e8dcb93b401a82cfd275426765ae',
    client_secret='dd30e57243c942589779e153e7e42682',
    redirect_uri='http://127.0.0.1:8888/callback',
    scope='user-read-private'
))

emotion_genre_map = {
    "happy": ["pop", "dance", "indie"],
    "sad": ["acoustic", "piano", "soul"],
    "angry": ["rock", "metal", "hip-hop"],
    "surprise": ["electronic", "edm", "alternative"],
    "neutral": ["chill", "ambient", "lo-fi"]
}


# ------------------ HELPER FUNCTIONS ------------------
def search_tracks_by_genre(genre, limit=5):
    results = sp.search(q=f'genre:"{genre}"', type='track', limit=limit)
    tracks = [{
        "name": track['name'],
        "artist": track['artists'][0]['name'],
        "url": track['external_urls']['spotify']
    } for track in results['tracks']['items']]
    return tracks


def recommend_music_for_emotion(emotion_label, n_songs=5):
    genres = emotion_genre_map.get(emotion_label, ['pop'])
    genre = random.choice(genres)
    return search_tracks_by_genre(genre, n_songs)


def detect_emotion_text(text):
    results = emotion_classifier(text)[0]
    top_result = max(results, key=lambda x: x['score'])
    return top_result['label'].lower(), top_result['score']


def preprocess_image(image_bytes):
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Invalid image file or unreadable format.")
    image = image.resize((224, 224))
    arr = img_to_array(image)
    arr = np.expand_dims(arr, axis=0)
    arr = preprocess_input(arr)
    return arr


def detect_emotion_image(image_bytes):
    processed = preprocess_image(image_bytes)
    preds = model.predict(processed)
    idx = np.argmax(preds)
    return emotion_labels[idx], float(preds[0][idx])


async def validate_image_file(file: UploadFile):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file format. Only JPG or PNG allowed."
        )
    MAX_SIZE_MB = 2 * 1024 * 1024
    contents = await file.read()
    if len(contents) > MAX_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large (max 2MB)"
        )
    await file.seek(0)
    return True


# ------------------ ROUTES ------------------
@app.get("/")
async def root():
    return {"message": "MoodMate API is running"}


@app.post("/recommend")
async def recommend(
    text: str = Form(None),
    file: UploadFile = File(None)
):
    print(f"Received: text={bool(text)}, file={file.filename if file else 'None'}")

    # Validation: Only one mode allowed
    if (not text and not file) or (text and file):
        raise HTTPException(
            status_code=400,
            detail="Please provide either text OR an image, not both."
        )

    text_emotion = text_conf = image_emotion = image_conf = None

    # TEXT MODE
    if text:
        text_emotion, text_conf = detect_emotion_text(text)
        print(f"Text emotion: {text_emotion} ({text_conf:.3f})")

    # IMAGE MODE
    if file:
        await validate_image_file(file)
        image_bytes = await file.read()
        image_emotion, image_conf = detect_emotion_image(image_bytes)
        print(f"Image emotion: {image_emotion} ({image_conf:.3f})")

    final_emotion = image_emotion or text_emotion
    songs = recommend_music_for_emotion(final_emotion)

    return {
        "text_emotion": text_emotion,
        "text_confidence": float(text_conf) if text_conf is not None else None,
        "image_emotion": image_emotion,
        "image_confidence": float(image_conf) if image_conf is not None else None,
        "final_emotion": final_emotion,
        "recommended_songs": songs
    }
