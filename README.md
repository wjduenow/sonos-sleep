# Sonos Sleep

A modern web-based controller for Sonos speakers with a focus on sleep routines, room control, and music management. This application provides a beautiful, responsive interface to control your Sonos system from any device on your network.

## Features

🎵 **Full Sonos Control**
- Play/pause, skip tracks, adjust volume
- Real-time progress tracking with seek functionality
- Queue management and track jumping
- Support for all Sonos-compatible music services

🏠 **Multi-Room Management**
- Control multiple Sonos rooms/zones
- Individual volume control per room
- Room-specific wake and sleep routines

🎭 **Rich Media Display**
- Album art display (sourced directly from Sonos)
- Expandable album art with click-to-zoom
- Track information with artist, title, and album details
- Real-time playback progress with time remaining

📱 **Modern Interface**
- Progressive Web App (PWA) support
- Responsive design works on desktop, tablet, and mobile
- Material Design components
- Dark/light theme support
- Touch-friendly controls with haptic feedback

🎼 **Playlist & Queue Management**
- Browse and play Sonos playlists
- View current queue with track listings
- Jump to any track in the queue
- Support for imported music library playlists

🎤 **Lyrics Integration**
- View lyrics for currently playing tracks
- Powered by lyrics.ovh API
- Clean, readable lyrics display

⏰ **Sleep & Wake Routines**
- Dedicated sleep and wake functions
- Configurable volume levels per room
- Perfect for bedtime automation

## Requirements

- **Python**: 3.3 or higher
- **Network**: Sonos speakers on the same network
- **Browser**: Modern web browser with JavaScript enabled

## Installation

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sonos-sleep
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure the application**
   ```bash
   cp config.py.default config.py
   ```
   
   Edit `config.py` to match your Sonos setup:
   ```python
   ROOMS = {
       "Living Room": {"volume": 25},
       "Bedroom": {"volume": 20},
       "Kitchen": {"volume": 30}
   }
   
   SECRET_KEY = 'your-secret-key-here'
   HOST_IP = "0.0.0.0"
   ```

4. **Run the application**
   ```bash
   python run.py
   ```

5. **Access the web interface**
   Open your browser to `http://localhost:5000/?secret_key=your-secret-key-here`

### Docker Installation

#### Using Docker Compose (Recommended)

1. **Clone and configure**
   ```bash
   git clone <repository-url>
   cd sonos-sleep
   cp config.py.default config.py
   # Edit config.py as needed
   ```

2. **Build and run**
   ```bash
   docker-compose up -d
   ```

#### Manual Docker Build

1. **Build the image**
   ```bash
   docker build -t sonos-sleep .
   ```

2. **Run the container**
   ```bash
   docker run -d --name sonos-sleep --network host sonos-sleep
   ```

#### Cross-platform Build (Intel from Apple Silicon)
   ```bash
   docker build --platform=linux/amd64 -t sonos-sleep . && docker save sonos-sleep > sonos-sleep.tar
   ```

## Configuration

### Room Configuration

Edit `config.py` to define your Sonos rooms and their default volume levels:

```python
ROOMS = {
    "Room Name": {"volume": 25},  # Volume level 0-100
    "Another Room": {"volume": 35}
}
```

### Security

Set a secure secret key in `config.py`:
```python
SECRET_KEY = 'your-unique-secret-key'
```

This key is required for all API access and should be kept secure.

## Usage

### Basic Playback Control
- **Play/Pause**: Click the play/pause button in any room
- **Skip Tracks**: Use next/previous buttons
- **Volume**: Use volume up/down buttons
- **Seek**: Click anywhere on the progress bar

### Queue Management
- Click the queue icon to view the current playlist
- Click any track to jump to it
- Scroll through long playlists

### Playlists
- Browse your Sonos playlists on the main page
- Click any playlist to select a room and start playing
- Supports both Sonos playlists and imported music library playlists

### Album Art
- Click album art to view full-screen
- Click anywhere outside or press Escape to close
- Album art is sourced directly from your Sonos system

### Lyrics
- Click on track information to view lyrics (when available)
- Lyrics are fetched from lyrics.ovh
- Works with most popular songs

## API Endpoints

### Room Control
- `GET /room_status?room=<name>&secret_key=<key>` - Get room status
- `POST /play?room=<name>&secret_key=<key>` - Play/resume
- `POST /wake?room=<name>&secret_key=<key>` - Wake routine (pause)
- `POST /volume?room=<name>&change=<up|down>&secret_key=<key>` - Volume control

### Track Control
- `POST /next?room=<name>&secret_key=<key>` - Next track
- `POST /previous?room=<name>&secret_key=<key>` - Previous track
- `POST /seek?room=<name>&position_sec=<seconds>&secret_key=<key>` - Seek to position

### Queue Management
- `GET /queue?room=<name>&secret_key=<key>` - Get current queue
- `POST /jump_to_track?room=<name>&track_index=<index>&secret_key=<key>` - Jump to track

### Playlists
- `POST /sonos_playlist?play_list=<name>&room=<name>&secret_key=<key>` - Play playlist
- `GET /playlist_tracks?play_list=<name>&secret_key=<key>` - Get playlist tracks

### Lyrics
- `GET /lyrics?artist=<artist>&title=<title>&secret_key=<key>` - Get song lyrics

## Dependencies

### Core Libraries
- **Flask** (≥2.2.5) - Web framework
- **SoCo** (0.30.10) - Sonos controller library
- **Requests** (≥2.25.0) - HTTP client for lyrics API

### Production Dependencies
- **Gunicorn** (≥23.0.0) - WSGI HTTP server
- **Click** (≥8.0) - Command line interface
- **Jinja2** (≥2.10.1) - Template engine

### Frontend Libraries (CDN)
- **Material Components for Web** - UI components
- **Material Icons** - Icon set

## Technical Architecture

### Backend
- **Flask** application with RESTful API
- **SoCo** library for Sonos communication
- Real-time status polling for live updates
- Error handling and graceful degradation

### Frontend
- Vanilla JavaScript with modern ES6+ features
- Progressive Web App capabilities
- Responsive CSS with Material Design
- Real-time UI updates via polling
- Touch and keyboard navigation support

### Network Communication
- Uses UPnP/SOAP for Sonos communication
- Requires network access to Sonos speakers
- Host networking mode for Docker deployment

## Development

### Project Structure
```
sonos-sleep/
├── run.py              # Main Flask application
├── config.py           # Configuration (created from .default)
├── requirements.txt    # Python dependencies
├── templates/
│   └── index.html     # Main web interface
├── static/            # Static assets (CSS, JS, icons)
├── Dockerfile         # Docker build configuration
└── docker-compose.yml # Docker Compose setup
```

### Running in Development Mode
```bash
python run.py
```
The application runs with debug mode enabled by default.

### API Development
All API endpoints return JSON responses and require the secret key for authentication.

## Known Limitations

- **YouTube Music**: Due to authentication limitations in the SoCo library, YouTube Music functionality is limited. Use the official Sonos app for YouTube Music control.
- **Network Dependency**: Requires Sonos speakers to be on the same network
- **Single User**: Designed for single-user operation (no multi-user authentication)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Troubleshooting

### Common Issues

**Can't find Sonos speakers**
- Ensure speakers are on the same network
- Check firewall settings
- Verify Sonos speakers are powered on

**Authentication errors**
- Check that the secret key in the URL matches config.py
- Ensure config.py exists (copy from config.py.default)

**Docker networking issues**
- Use `--network host` for Docker run commands
- Ensure Docker can access your local network

## License

This project is provided as-is for personal and educational use.
