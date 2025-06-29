import os
import sys

# Add vendor directory to module search path
parent_dir = os.path.abspath(os.path.dirname(__file__))
vendor_dir = os.path.join(parent_dir, 'vendor')

sys.path.append(vendor_dir)

from flask import Flask
from flask import request
from flask import render_template
from flask import flash, redirect, jsonify
from http import HTTPStatus
import soco
import asyncio
import time
import requests
from config import ROOMS, SECRET_KEY




app = Flask(__name__)
app.secret_key = SECRET_KEY

#wsl_ip = "192.168.68.131"

@app.route('/', methods=['GET', 'POST'])
def list_play_lists():

  if request.args.get("secret_key") != app.secret_key:
      return 'Forbidden' , http_status.HTTP_403_FORBIDDEN

  zones = soco.discover()  # returns a set or None

  sonos = None
  if zones:
      zones = sorted(list(zones), key=lambda z: z.player_name)

      # Choose a default player (first in sorted list)
      sonos = zones[0]

      # Prefer the Living Room player if it exists
      for zone in zones:
          if zone.player_name == "Living Room":
              sonos = zone
              break
  else:
      # When running without any Sonos system, fall back to empty list
      zones = []

  # Fetch playlists only if we have a valid Sonos object
  playlists = []
  if sonos is not None:
      try:
        playlists = sonos.get_sonos_playlists()
      except Exception as e:
        print(f"Error fetching Sonos playlists: {e}")

  playlist_titles = [pl.title for pl in playlists]

  # Render without per-room status (will be fetched client-side)
  return render_template('index.html', zones = zones, playlists = playlist_titles, secret_key = app.secret_key)

@app.route('/sleep', methods=['GET', 'POST'])
def sleep():

  if request.args.get("secret_key") != app.secret_key:
      return 'Forbidden' , http_status.HTTP_403_FORBIDDEN

  secret_key = request.args.get("secret_key")

  room = "Master Bedroom"
  if request.args.get('room'):
      room = request.args.get('room')

  room_volume = ROOMS[room]['volume']
  if request.args.get('room_volume'):
      room_volume = request.args.get('room_volume')

  content = request.get_json(silent=True)
  if content:
      room = content['Room_Name']

  try:
    play_playlist(room, 'Sleep', room_volume)
    flash("Running Sleep Routine in %s" %(str(room)), 'success')
    return redirect("/?secret_key=%s" % (secret_key))
  except Exception as e:
     return ("error: %s" % (e))

@app.route('/wake', methods=['GET', 'POST'])
def wake():

  if request.args.get("secret_key") != app.secret_key:
      return 'Forbidden' , http_status.HTTP_403_FORBIDDEN

  secret_key = request.args.get("secret_key")

  room = "Master Bedroom"
  if request.args.get('room'):
      room = request.args.get('room')

  content = request.get_json(silent=True)
  if content:
      room = content['Room_Name']

  try:
    zones = soco.discover()
    for zone in zones:
        print(zone.player_name)
        if zone.player_name == room: #'Master Bedroom':
            sonos = zone

    sonos.pause()

    if request.args.get('ajax') == '1':
        return jsonify({'status': 'ok', 'is_playing': False})

    flash("Running Wake Routine in %s" %(str(room)), 'success')
    return redirect("/?secret_key=%s" % (secret_key))

  except Exception as e:
     return ("error: %s" % (e))

@app.route('/sonos_playlist', methods=['GET', 'POST'])
def sonos_playlist():


  if request.args.get("secret_key") != app.secret_key:
      return 'Forbidden' , http_status.HTTP_403_FORBIDDEN

  secret_key = request.args.get("secret_key")

  room = "Master Bedroom"
  if request.args.get('room'):
      room = request.args.get('room')

  play_list = "Sleep"
  if request.args.get('play_list'):
      play_list = request.args.get('play_list')

  try:
    room_volume = ROOMS[room]['volume']
  except:
    room_volume = 30

  if request.args.get('room_volume'):
      room_volume = request.args.get('room_volume')

  try:
    play_playlist(room, play_list, room_volume)
    
    # Handle AJAX requests
    if request.args.get('ajax') == '1':
        return jsonify({
            'status': 'ok',
            'message': f'Playing {play_list} in {room} at {room_volume} volume'
        })
    
    flash("Playing %s in %s at %s volume" % (play_list, room, str(room_volume)), 'success')
    return redirect("/?secret_key=%s" % (secret_key))
  except Exception as e:
     error_msg = "error: %s in (room: %s)" % (e, room)
     
     # Handle AJAX requests
     if request.args.get('ajax') == '1':
         return jsonify({
             'status': 'error',
             'error': str(e),
             'message': error_msg
         }), HTTPStatus.INTERNAL_SERVER_ERROR
     
     flash(error_msg, 'error')
     return redirect("/?secret_key=%s" % (secret_key))    

# ---------------------------------------------------------
#   API ENDPOINTS
# ---------------------------------------------------------


@app.route('/playlist_tracks', methods=['GET'])
def playlist_tracks():

  """Return tracks for the requested Sonos playlist as JSON."""

  if request.args.get("secret_key") != app.secret_key:
      return jsonify({"error": "Forbidden"}), http_status.HTTP_403_FORBIDDEN

  playlist_name = request.args.get("play_list")
  if not playlist_name:
      return jsonify({"error": "Missing play_list parameter"}), http_status.HTTP_400_BAD_REQUEST

  room = request.args.get("room", "Living Room")

  zones = soco.discover()
  if not zones:
      return jsonify([])

  # Select zone
  sonos = next((z for z in zones if z.player_name == room), list(zones)[0])

  try:
      playlists = sonos.get_sonos_playlists()
  except Exception as e:
      return jsonify({"error": f"Unable to fetch playlists: {e}"}), http_status.HTTP_500_INTERNAL_SERVER_ERROR

  target_playlist = next((pl for pl in playlists if pl.title == playlist_name), None)
  if target_playlist is None:
      return jsonify([])

  try:
      browse_result = sonos.browse(target_playlist) if hasattr(sonos, 'browse') else sonos.music_library.browse(target_playlist)
      pl_tracks = browse_result.item_list if hasattr(browse_result, 'item_list') else list(browse_result or [])

      tracks_json = [
          {
              "title": getattr(t, 'title', ''),
              "creator": getattr(t, 'creator', ''),
              "album": getattr(t, 'album', '')
          } for t in pl_tracks
      ]

      return jsonify(tracks_json)
  except Exception as e:
      return jsonify({"error": f"Error fetching tracks: {e}"})

def play_playlist(room, playlist_name, volume):

  zones = soco.discover()
  for zone in zones:
      print(zone.player_name)
      if zone.player_name == room:
          ## Removing Target Player from Any Groups it may be in
          zone.unjoin()
          sonos = zone

  playlists = sonos.get_sonos_playlists()
  for playlist in playlists:
      print("#%s#" % (playlist.title))
      if str(playlist.title) == str(playlist_name):
          print("Assigning #%s#" % (playlist_name))
          new_pl = playlist

  sonos.clear_queue()
  print("Adding %s to the queue" % (playlist_name))
  sonos.add_to_queue(new_pl)
  sonos.play_from_queue(0)
  sonos.volume = volume
  sonos.play()


# ---------------------------------------------------------
#   Room playback control (resume)
# ---------------------------------------------------------


@app.route('/play', methods=['GET', 'POST'])
def room_play():

  if request.args.get("secret_key") != app.secret_key:
      return 'Forbidden' , http_status.HTTP_403_FORBIDDEN

  secret_key = request.args.get("secret_key")

  room = request.args.get('room', 'Master Bedroom')

  try:
    zones = soco.discover()
    for zone in zones:
        if zone.player_name == room:
            sonos = zone
            break
    else:
        return "Room not found", http_status.HTTP_404_NOT_FOUND

    sonos.play()

    if request.args.get('ajax') == '1':
        return jsonify({'status': 'ok', 'is_playing': True})

    flash("Resumed playback in %s" % (room), 'success')
    return redirect("/?secret_key=%s" % (secret_key))

  except Exception as e:
     return ("error: %s" % (e))

# ---------------------------------------------------------
#   Volume control
# ---------------------------------------------------------


@app.route('/volume', methods=['GET', 'POST'])
def room_volume():

  if request.args.get("secret_key") != app.secret_key:
      return 'Forbidden' , http_status.HTTP_403_FORBIDDEN

  secret_key = request.args.get("secret_key")

  room = request.args.get('room')
  change = request.args.get('change', 'up')  # up / down

  STEP = 5

  try:
    zones = soco.discover()
    for zone in zones:
        if zone.player_name == room:
            sonos = zone
            break
    else:
        return "Room not found", http_status.HTTP_404_NOT_FOUND

    current_vol = sonos.volume or 0
    if change == 'down':
        new_vol = max(current_vol - STEP, 0)
    else:
        new_vol = min(current_vol + STEP, 100)

    sonos.volume = new_vol

    if request.args.get('ajax') == '1':
        return jsonify({'status': 'ok', 'volume': new_vol})

    flash("Set volume in %s to %s" % (room, new_vol), 'info')
    return redirect("/?secret_key=%s" % (secret_key))

  except Exception as e:
     return ("error: %s" % (e))

# ---------------------------------------------------------
#   Room status (lazy load)
# ---------------------------------------------------------


@app.route('/room_status', methods=['GET'])
def room_status():

  if request.args.get("secret_key") != app.secret_key:
      return jsonify({"error": "Forbidden"}), http_status.HTTP_403_FORBIDDEN

  room = request.args.get('room')
  if not room:
      return jsonify({"error": "Missing room"}), http_status.HTTP_400_BAD_REQUEST

  try:
    zones = soco.discover()
    for zone in zones:
        if zone.player_name == room:
            sonos = zone
            break
    else:
        return jsonify({"error": "Room not found"}), http_status.HTTP_404_NOT_FOUND

    # Track info
    title = ''
    artist = ''
    album_art = ''
    try:
        track_info = sonos.get_current_track_info()
        title = track_info.get('title', '')
        artist = track_info.get('artist', '') or track_info.get('creator', '')
        album_art = track_info.get('album_art', '')
        desc = f"{title} - {artist}" if title else 'Nothing playing'

        # Extract duration & position for progress bar
        def _to_seconds(time_str):
            """Convert Sonos HH:MM:SS (or MM:SS) time string to seconds."""
            if not time_str:
                return 0
            try:
                parts = [int(float(p)) for p in time_str.split(':') if p.isdigit()]
            except ValueError:
                return 0
            if len(parts) == 3:
                h, m, s = parts
            elif len(parts) == 2:
                h, m, s = 0, parts[0], parts[1]
            elif len(parts) == 1:
                h, m, s = 0, 0, parts[0]
            else:
                return 0
            return h * 3600 + m * 60 + s

        duration_sec = _to_seconds(track_info.get('duration', ''))
        position_sec = _to_seconds(track_info.get('position', ''))
    except Exception:
        desc = 'Unknown'
        duration_sec = 0
        position_sec = 0

    state = sonos.get_current_transport_info().get('current_transport_state', '')
    is_playing = state == 'PLAYING'
    vol = sonos.volume or 0

    return jsonify({
        'status': 'ok',
        'track': desc,
        'title': title,
        'artist': artist,
        'album_art': album_art,
        'is_playing': is_playing,
        'volume': vol,
        'duration_sec': duration_sec,
        'position_sec': position_sec
    })

  except Exception as e:
     return jsonify({"error": str(e)})

# ---------------------------------------------------------
#   Next / Previous track
# ---------------------------------------------------------


def _find_sonos(room):
    zones = soco.discover()
    if not zones:
        return None
    for z in zones:
        if z.player_name == room:
            return z
    return None


def _simple_control(route, action_fn):
    if request.args.get("secret_key") != app.secret_key:
        return 'Forbidden', http_status.HTTP_403_FORBIDDEN

    secret_key = request.args.get("secret_key")
    room = request.args.get('room', 'Master Bedroom')

    sonos = _find_sonos(room)
    if sonos is None:
        return "Room not found", http_status.HTTP_404_NOT_FOUND

    try:
        action_fn(sonos)
    except Exception as e:
        return f"error: {e}", http_status.HTTP_500_INTERNAL_SERVER_ERROR

    if request.args.get('ajax') == '1':
        return jsonify({'status': 'ok'})

    flash(f"{route.title()} track in {room}", 'success')
    return redirect(f"/?secret_key={secret_key}")


@app.route('/next', methods=['GET', 'POST'])
def room_next():
    return _simple_control('next', lambda s: s.next())


@app.route('/previous', methods=['GET', 'POST'])
def room_previous():
    return _simple_control('previous', lambda s: s.previous())

# ---------------------------------------------------------
#   Seek within current track
# ---------------------------------------------------------


@app.route('/seek', methods=['GET', 'POST'])
def room_seek():

    if request.args.get("secret_key") != app.secret_key:
        return 'Forbidden', http_status.HTTP_403_FORBIDDEN

    secret_key = request.args.get("secret_key")

    room = request.args.get('room', 'Master Bedroom')

    # Accept position in seconds (int) or HH:MM:SS string
    position_sec = request.args.get('position_sec')
    position_str = request.args.get('position')  # alternative param

    if position_sec is None and position_str is None:
        return 'Missing position', http_status.HTTP_400_BAD_REQUEST

    # convert seconds to HH:MM:SS if provided as seconds
    if position_str is None:
        try:
            sec = int(float(position_sec))
        except ValueError:
            return 'Invalid position', http_status.HTTP_400_BAD_REQUEST

        h = sec // 3600
        m = (sec % 3600) // 60
        s = sec % 60
        position_str = f"{h:02d}:{m:02d}:{s:02d}"

    sonos = _find_sonos(room)
    if sonos is None:
        return "Room not found", http_status.HTTP_404_NOT_FOUND

    try:
        sonos.seek(position_str)
    except Exception as e:
        return f"error: {e}", http_status.HTTP_500_INTERNAL_SERVER_ERROR

    if request.args.get('ajax') == '1':
        return jsonify({'status': 'ok'})

    flash(f"Seeked to {position_str} in {room}", 'info')
    return redirect(f"/?secret_key={secret_key}")

# ---------------------------------------------------------
#   Queue endpoint
# ---------------------------------------------------------

@app.route('/queue', methods=['GET'])
def get_queue():
    """Return the current queue for the requested room as JSON."""
    
    if request.args.get("secret_key") != app.secret_key:
        return jsonify({"error": "Forbidden"}), HTTPStatus.HTTP_403_FORBIDDEN

    room = request.args.get('room')
    if not room:
        return jsonify({"error": "Missing room parameter"}), HTTPStatus.HTTP_400_BAD_REQUEST

    try:
        sonos = _find_sonos(room)
        if sonos is None:
            return jsonify({"error": "Room not found"}), HTTPStatus.HTTP_404_NOT_FOUND

        # Get the current queue
        queue = sonos.get_queue()
        
        # Get current track info to determine position in queue
        current_track_info = sonos.get_current_track_info()
        current_index = 0
        
        # Try to get the current track index from queue position
        try:
            queue_position = current_track_info.get('playlist_position', '1')
            if queue_position and queue_position.isdigit():
                current_index = int(queue_position) - 1  # Convert to 0-based index
        except (ValueError, TypeError):
            current_index = 0

        # Convert queue items to JSON
        queue_items = []
        for i, track in enumerate(queue):
            # Extract duration in seconds
            duration_str = getattr(track, 'duration', '') or ''
            duration_sec = 0
            if duration_str:
                try:
                    # Parse duration string (format: H:MM:SS or MM:SS)
                    time_parts = duration_str.split(':')
                    if len(time_parts) == 3:
                        h, m, s = map(int, time_parts)
                        duration_sec = h * 3600 + m * 60 + s
                    elif len(time_parts) == 2:
                        m, s = map(int, time_parts)
                        duration_sec = m * 60 + s
                except (ValueError, TypeError):
                    duration_sec = 0

            queue_items.append({
                "title": getattr(track, 'title', 'Unknown Title'),
                "artist": getattr(track, 'creator', '') or getattr(track, 'artist', 'Unknown Artist'),
                "album": getattr(track, 'album', ''),
                "duration": duration_sec
            })

        return jsonify({
            'status': 'ok',
            'queue': queue_items,
            'current_index': current_index,
            'total_tracks': len(queue_items)
        })

    except Exception as e:
        return jsonify({"error": f"Failed to get queue: {str(e)}"}), HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR

# ---------------------------------------------------------
#   Jump to track in queue
# ---------------------------------------------------------

@app.route('/jump_to_track', methods=['GET', 'POST'])
def jump_to_track():
    """Jump to a specific track in the queue by index."""
    
    if request.args.get("secret_key") != app.secret_key:
        return jsonify({"error": "Forbidden"}), HTTPStatus.HTTP_403_FORBIDDEN

    room = request.args.get('room')
    track_index = request.args.get('track_index')
    
    if not room:
        return jsonify({"error": "Missing room parameter"}), HTTPStatus.HTTP_400_BAD_REQUEST
    
    if track_index is None:
        return jsonify({"error": "Missing track_index parameter"}), HTTPStatus.HTTP_400_BAD_REQUEST

    try:
        track_index = int(track_index)
    except ValueError:
        return jsonify({"error": "Invalid track_index parameter"}), HTTPStatus.HTTP_400_BAD_REQUEST

    try:
        sonos = _find_sonos(room)
        if sonos is None:
            return jsonify({"error": "Room not found"}), HTTPStatus.HTTP_404_NOT_FOUND

        # Jump to the specified track in the queue (soco uses 0-based indexing)
        sonos.play_from_queue(track_index)

        if request.args.get('ajax') == '1':
            return jsonify({'status': 'ok', 'track_index': track_index})

        flash(f"Jumped to track {track_index + 1} in {room}", 'success')
        return redirect(f"/?secret_key={request.args.get('secret_key')}")

    except Exception as e:
        error_msg = f"Failed to jump to track: {str(e)}"
        if request.args.get('ajax') == '1':
            return jsonify({"error": error_msg}), HTTPStatus.HTTP_500_INTERNAL_SERVER_ERROR
        else:
            flash(error_msg, 'error')
            return redirect(f"/?secret_key={request.args.get('secret_key')}")

# ---------------------------------------------------------
#   Playlist management endpoints
# ---------------------------------------------------------

@app.route('/delete_playlist', methods=['POST'])
def delete_playlist():
    """Delete a Sonos playlist."""
    
    if request.args.get("secret_key") != app.secret_key:
        return jsonify({"error": "Forbidden"}), HTTPStatus.FORBIDDEN

    playlist_name = request.args.get("playlist_name")
    room = request.args.get("room", "Living Room")
    
    if not playlist_name:
        return jsonify({"error": "Missing playlist_name parameter"}), HTTPStatus.BAD_REQUEST
    
    try:
        zones = soco.discover()
        if not zones:
            return jsonify({"error": "No Sonos speakers found"}), HTTPStatus.NOT_FOUND
            
        sonos = next((z for z in zones if z.player_name == room), list(zones)[0])
        
        # Find the playlist
        playlists = sonos.get_sonos_playlists()
        target_playlist = next((pl for pl in playlists if pl.title == playlist_name), None)
        
        if not target_playlist:
            return jsonify({"error": "Playlist not found"}), HTTPStatus.NOT_FOUND
        
        # Delete the playlist
        success = sonos.remove_sonos_playlist(target_playlist)
        
        if success:
            return jsonify({
                "status": "ok", 
                "message": f"Successfully deleted playlist '{playlist_name}'"
            })
        else:
            return jsonify({"error": "Failed to delete playlist"}), HTTPStatus.INTERNAL_SERVER_ERROR
            
    except Exception as e:
        return jsonify({"error": f"Error deleting playlist: {str(e)}"}), HTTPStatus.INTERNAL_SERVER_ERROR

# ---------------------------------------------------------
#   Lyrics API endpoint
# ---------------------------------------------------------

@app.route('/lyrics', methods=['GET'])
def get_lyrics():
    """Fetch lyrics for a song from lyrics.ovh API."""
    
    if request.args.get("secret_key") != app.secret_key:
        return jsonify({"error": "Forbidden"}), HTTPStatus.FORBIDDEN

    artist = request.args.get('artist')
    title = request.args.get('title')
    
    if not artist or not title:
        return jsonify({"error": "Missing artist or title parameter"}), HTTPStatus.BAD_REQUEST

    try:
        # Use lyrics.ovh API - it's free and doesn't require API key
        url = f"https://api.lyrics.ovh/v1/{artist}/{title}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'lyrics' in data:
                return jsonify({
                    'status': 'ok',
                    'lyrics': data['lyrics'],
                    'artist': artist,
                    'title': title
                })
            else:
                return jsonify({"error": "No lyrics found"}), HTTPStatus.NOT_FOUND
        else:
            return jsonify({"error": "Lyrics not found"}), HTTPStatus.NOT_FOUND
            
    except requests.exceptions.Timeout:
        return jsonify({"error": "Request timeout - lyrics service unavailable"}), HTTPStatus.REQUEST_TIMEOUT
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to fetch lyrics: {str(e)}"}), HTTPStatus.INTERNAL_SERVER_ERROR
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), HTTPStatus.INTERNAL_SERVER_ERROR

# create mapping for http_status.* names used in code
class _HttpCodes:
    HTTP_403_FORBIDDEN = HTTPStatus.FORBIDDEN
    HTTP_400_BAD_REQUEST = HTTPStatus.BAD_REQUEST
    HTTP_404_NOT_FOUND = HTTPStatus.NOT_FOUND
    HTTP_500_INTERNAL_SERVER_ERROR = HTTPStatus.INTERNAL_SERVER_ERROR

http_status = _HttpCodes

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

