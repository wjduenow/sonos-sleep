from flask import Flask
from flask import request
from flask import render_template
from flask import flash, redirect
import soco
from pyHS100 import SmartPlug
from pprint import pformat as pf
import time
import socket
from config import ROOMS, NIGHT_LIGHT_POWER_PLUG


app = Flask(__name__)
app.secret_key = 'mixelplk'


@app.route('/', methods=['GET', 'POST'])
def list_play_lists():

  zones = soco.discover()
  if zones:
    for zone in zones:
        sonos = zone
        if zone.player_name == "Living Room":
            sonos = zone
  else:
    zones = {'Example': {"player_name": "Example 3"}, 'Example 2': {"player_name": "Example 3"}, "Example 3": {"player_name": "Example 3"}}

  try:
    plug = SmartPlug(NIGHT_LIGHT_POWER_PLUG)
    plug_state = plug.state
  except:
    plug_state = "unknown"

  try:
    playlists = sonos.get_sonos_playlists()
  except:
    playlists = {}

  dict_play_lists = {}



  for playlist in playlists:
      pl_tracks = []
      dict_play_lists[playlist.title] = pl_tracks

  return render_template('list_play_lists.html', zones = zones, dict_play_lists = dict_play_lists, plug_state = plug_state)

@app.route('/sleep', methods=['GET', 'POST'])
def sleep():

  room = "Master Bedroom"
  if request.args.get('room'):
      room = request.args.get('room')

  room_volume = ROOMS[room]['volume']
  if request.args.get('room_volume'):
      room_volume = request.args.get('room_volume')

  content = request.get_json(silent=True)
  if content:
      room = content['Room_Name']

  #Manage Lights if Girls Room
  if room == "Brynn":
    brynn_night_light("On")

  try:
    play_playlist(room, 'Sleep', room_volume)
    return "Running Sleep Routine in %s" % (room)
  except Exception as e:
     return ("error: %s" % (e))

@app.route('/wake', methods=['GET', 'POST'])
def wake():

  room = "Master Bedroom"
  if request.args.get('room'):
      room = request.args.get('room')

  #Manage Lights if Girls Room
  if room == "Brynn":
    brynn_night_light("Off")

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

    return "Running Wake Routine in %s" % (room)

  except Exception as e:
     return ("error: %s" % (e))

@app.route('/sonos_playlist', methods=['GET', 'POST'])
def sonos_playlist():

  room = "Master Bedroom"
  if request.args.get('room'):
      room = request.args.get('room')

  play_list = "Sleep"
  if request.args.get('play_list'):
      play_list = request.args.get('play_list')

  room_volume = ROOMS[room]['volume']
  if request.args.get('room_volume'):
      room_volume = request.args.get('room_volume')

  try:
    play_playlist(room, play_list, room_volume)
    flash("Playing %s in %s at %s volume" % (play_list, room, room_volume), 'success')
    return redirect('/')
    #return ("Playing %s in %s at %s volume" % (play_list, room, room_volume))
  except Exception as e:
     flash("error: %s in (room: %s)" % (e, room), 'error')
     #return ("error: %s in (room: %s)" % (e, room))


def brynn_night_light(state = "Off"):
  
  plug = SmartPlug(NIGHT_LIGHT_POWER_PLUG)

  if state == "On":
    plug.turn_on()
    plug.led = False
  else:
    plug.turn_off()
    plug.led = True

def play_playlist(room, playlist_name, volume):

  zones = soco.discover()
  for zone in zones:
      print(zone.player_name)
      if zone.player_name == room:
          sonos = zone

  print(sonos.player_name)
  print(dir(sonos))
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


if __name__ == '__main__':
    app.run(host='192.168.86.143', port=8999)
    #app.run(host='0.0.0.0')


#if __name__ == "__main__":
#    app.run(host='0.0.0.0')

