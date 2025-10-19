import { useState } from "react";
import './App.css';

function App() {
  const [text, setText] = useState("");
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const [results, setResults] = useState(null);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      alert("Please upload a valid image file!");
      return;
    }
    setImageFile(file);
    setImagePreview(URL.createObjectURL(file));
    setText(""); // Clear text, only one allowed!
  };

  const handleTextChange = (e) => {
    setText(e.target.value);
    setImageFile(null); // Clear image when typing text
    setImagePreview(null);
  };

  const getRecommendations = async () => {
    // Validation: Only one input!
    if ((text && imageFile) || (!text && !imageFile)) {
      alert("Please enter text OR choose an image (not both).");
      return;
    }
    const formData = new FormData();
    if (text) {
      formData.append("text", text);
    }
    if (imageFile) {
      formData.append("file", imageFile);
    }
    try {
      const response = await fetch("http://localhost:8000/recommend", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      setResults(data);
    } catch (error) {
      alert("Error connecting to server");
      console.error(error);
    }
  };

  return (
    <div className="App">
      <h1>🎶 Smart Song Recommender</h1>
      <textarea
        rows={4}
        value={text}
        onChange={handleTextChange}
        placeholder="Enter your text OR choose an image"
        style={{ width: '100%' }}
        disabled={imageFile ? true : false}
      />
      <br />
      {/* Custom File Input */}
      <label className="custom-file-label">
        Choose Image
        <input
          type="file"
          accept="image/*"
          onChange={handleFileChange}
          disabled={text ? true : false}
        />
      </label>
      {/* Image preview */}
      {imagePreview && (
        <div style={{ marginTop: 12 }}>
          <img src={imagePreview} alt="preview" />
        </div>
      )}
      <br />
      <button onClick={getRecommendations}>Get Recommendations</button>
      {results && (
        <div>
          <p>
            Text Emotion: {results.text_emotion} ({(results.text_confidence * 100).toFixed(2)}%)
          </p>
          {results.image_emotion && (
            <p>
              Image Emotion: {results.image_emotion} ({(results.image_confidence * 100).toFixed(2)}%)
            </p>
          )}
          <p>Final Emotion: {results.final_emotion}</p>
          <h4>Recommended Songs:</h4>
          <ul>
            {results.recommended_songs?.map((song, index) => (
  <li key={index} style={{ "--delay": `${90 + 60 * index}ms` }}>
    <span className="song-icon" aria-label="music"></span>
    <a href={song.url} target="_blank" rel="noreferrer">
      {song.name} by {song.artist}
    </a>
  </li>
))}

          </ul>
        </div>
      )}
    </div>
  );
}

export default App;
