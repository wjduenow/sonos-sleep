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
from flask_api import status
import soco
import asyncio
import time
import socket
from config import ROOMS, SECRET_KEY




app = Flask(__name__)
app.secret_key = SECRET_KEY

#wsl_ip = "192.168.68.131"

@app.route('/', methods=['GET', 'POST'])
def list_play_lists():

  if request.args.get("secret_key") != app.secret_key:
      return 'Forbidden' , status.HTTP_403_FORBIDDEN

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

  # Gather current playing information for each zone
  current_info = {}
  for zone in zones:
      try:
          track_info = zone.get_current_track_info()
          title = track_info.get('title', '')
          artist = track_info.get('artist', '') or track_info.get('creator', '')
          if title:
              desc = f"{title} - {artist}" if artist else title
          else:
              desc = 'Nothing playing'

          state = zone.get_current_transport_info().get('current_transport_state', '')
          is_playing = state == 'PLAYING'
      except Exception:
          desc = 'Unknown'
          is_playing = False

      current_info[zone.player_name] = {
          'track': desc,
          'is_playing': is_playing
      }

  return render_template('list_play_lists.html', zones = zones, playlists = playlist_titles, secret_key = app.secret_key, current_info=current_info)

@app.route('/sleep', methods=['GET', 'POST'])
def sleep():

  if request.args.get("secret_key") != app.secret_key:
      return 'Forbidden' , status.HTTP_403_FORBIDDEN

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
      return 'Forbidden' , status.HTTP_403_FORBIDDEN

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

    #return "Running Wake Routine in %s" %(str(room))
    flash("Running Wake Routine in %s" %(str(room)), 'success')
    return redirect("/?secret_key=%s" % (secret_key))

  except Exception as e:
     return ("error: %s" % (e))

@app.route('/sonos_playlist', methods=['GET', 'POST'])
def sonos_playlist():


  if request.args.get("secret_key") != app.secret_key:
      return 'Forbidden' , status.HTTP_403_FORBIDDEN

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
    flash("Playing %s in %s at %s volume" % (play_list, room, str(room_volume)), 'success')
    return redirect("/?secret_key=%s" % (secret_key))
    #return ("Playing %s in %s at %s volume" % (play_list, room, room_volume))
  except Exception as e:
     flash("error: %s in (room: %s)" % (e, room), 'error')
     #return ("error: %s in (room: %s)" % (e, room))    

# ---------------------------------------------------------
#   API ENDPOINTS
# ---------------------------------------------------------


@app.route('/playlist_tracks', methods=['GET'])
def playlist_tracks():

  """Return tracks for the requested Sonos playlist as JSON."""

  if request.args.get("secret_key") != app.secret_key:
      return jsonify({"error": "Forbidden"}), status.HTTP_403_FORBIDDEN

  playlist_name = request.args.get("play_list")
  if not playlist_name:
      return jsonify({"error": "Missing play_list parameter"}), status.HTTP_400_BAD_REQUEST

  room = request.args.get("room", "Living Room")

  zones = soco.discover()
  if not zones:
      return jsonify([])

  # Select zone
  sonos = next((z for z in zones if z.player_name == room), list(zones)[0])

  try:
      playlists = sonos.get_sonos_playlists()
  except Exception as e:
      return jsonify({"error": f"Unable to fetch playlists: {e}"}), status.HTTP_500_INTERNAL_SERVER_ERROR

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

def get_plug_ip():
   return socket.gethostbyname(POWER_PLUG)


# ---------------------------------------------------------
#   Room playback control (resume)
# ---------------------------------------------------------


@app.route('/play', methods=['GET', 'POST'])
def room_play():

  if request.args.get("secret_key") != app.secret_key:
      return 'Forbidden' , status.HTTP_403_FORBIDDEN

  secret_key = request.args.get("secret_key")

  room = request.args.get('room', 'Master Bedroom')

  try:
    zones = soco.discover()
    for zone in zones:
        if zone.player_name == room:
            sonos = zone
            break
    else:
        return "Room not found", status.HTTP_404_NOT_FOUND

    sonos.play()

    flash("Resumed playback in %s" % (room), 'success')
    return redirect("/?secret_key=%s" % (secret_key))

  except Exception as e:
     return ("error: %s" % (e))


if __name__ == "__main__":
    app.run(host='0.0.0.0')

