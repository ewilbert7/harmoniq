import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = 'http://127.0.0.1:8000';

function App() {
  const [accessToken, setAccessToken] = useState<string>('');
  const [playlistUrl, setPlaylistUrl] = useState<string>('');
  const [playlistData, setPlaylistData] = useState<any[]>([]);
  const [recommendations, setRecommendations] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    // Check if access token is in URL (after OAuth redirect)
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('access_token');
    if (token) {
      setAccessToken(token);
      window.history.replaceState({}, document.title, '/');
    }
  }, []);

  const handleLogin = async () => {
    const response = await axios.get(`${API_URL}/login`);
    window.location.href = response.data.auth_url;
  };

  const extractPlaylistId = (url: string): string => {
    const match = url.match(/playlist\/([a-zA-Z0-9]+)/);
    return match ? match[1] : url;
  };

  const loadPlaylist = async () => {
    if (!accessToken || !playlistUrl) return;
    
    setLoading(true);
    try {
      const playlistId = extractPlaylistId(playlistUrl);
      const response = await axios.get(`${API_URL}/playlist/${playlistId}`, {
        headers: { Authorization: `Bearer ${accessToken}` }
      });
      setPlaylistData(response.data);
    } catch (error) {
      console.error('Error loading playlist:', error);
      alert('Error loading playlist. Make sure the URL is correct and the playlist is public.');
    }
    setLoading(false);
  };

  const getRecommendations = async () => {
    if (!accessToken || playlistData.length === 0) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/recommend`, 
        { playlist_tracks: playlistData },
        { headers: { Authorization: `Bearer ${accessToken}` } }
      );
      setRecommendations(response.data);
    } catch (error) {
      console.error('Error getting recommendations:', error);
    }
    setLoading(false);
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎵 Playlist Continuation Engine</h1>
        
        {!accessToken ? (
          <button onClick={handleLogin} className="login-btn">
            Login with Spotify
          </button>
        ) : (
          <div className="main-content">
            <div className="input-section">
              <input
                type="text"
                placeholder="Paste Spotify playlist URL..."
                value={playlistUrl}
                onChange={(e) => setPlaylistUrl(e.target.value)}
                className="playlist-input"
              />
              <button onClick={loadPlaylist} disabled={loading}>
                {loading ? 'Loading...' : 'Load Playlist'}
              </button>
            </div>

            {playlistData.length > 0 && (
              <div className="playlist-section">
                <h2>Your Playlist ({playlistData.length} tracks)</h2>
                <div className="track-list">
                  {playlistData.slice(-5).map((track) => (
                    <div key={track.id} className="track-item">
                      <img src={track.album_art} alt={track.name} />
                      <div>
                        <p><strong>{track.name}</strong></p>
                        <p>{track.artist}</p>
                      </div>
                    </div>
                  ))}
                </div>
                <button onClick={getRecommendations} className="recommend-btn">
                  Get AI Recommendations
                </button>
              </div>
            )}

            {recommendations.length > 0 && (
              <div className="recommendations-section">
                <h2>Recommended Tracks</h2>
                <div className="track-list">
                  {recommendations.map((track) => (
                    <div key={track.id} className="track-item recommendation">
                      <img src={track.album_art} alt={track.name} />
                      <div className="track-info">
                        <p><strong>{track.name}</strong></p>
                        <p>{track.artist}</p>
                        <div className="explanations">
                          {track.explanations.map((exp: string, i: number) => (
                            <span key={i} className="explanation-tag">{exp}</span>
                          ))}
                        </div>
                        <p className="confidence">Confidence: {track.confidence}%</p>
                      </div>
                      {track.preview_url && (
                        <audio controls src={track.preview_url} />
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </header>
    </div>
  );
}

export default App;