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
from config import ROOMS, NIGHT_LIGHT_POWER_PLUG, SECRET_KEY, HOST_IP




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
      # Choose a default player
      sonos = next(iter(zones))
      # Prefer the Living Room player if it exists
      for zone in zones:
          if zone.player_name == "Living Room":
              sonos = zone
              break
  else:
      # When running without any Sonos system, fall back to demo data
      zones = []

  # Fetch playlists only if we have a valid Sonos object
  playlists = []
  if sonos is not None:
      try:
        playlists = sonos.get_sonos_playlists()
      except Exception as e:
        print(f"Error fetching Sonos playlists: {e}")

  playlist_titles = [pl.title for pl in playlists]

  return render_template('list_play_lists.html', zones = zones, playlists = playlist_titles, secret_key = app.secret_key, rooms = ROOMS)

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


#if __name__ == '__main__':
    #app.run(host='192.168.86.34', port=8999)
#    app.run(host=HOST_IP, port=8999)


if __name__ == "__main__":
    app.run(host='0.0.0.0')

