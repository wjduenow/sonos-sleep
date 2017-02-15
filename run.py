from flask import Flask
from flask import request
import soco
from pyHS100 import SmartPlug
from pprint import pformat as pf
import time


app = Flask(__name__)

rooms = {"Master Bedroom": {"volume": 30}, "Bedroom": {"volume": 35}, "Living Room": {"volume": 40}}

@app.route('/sleep', methods=['GET', 'POST'])
def sleep():

  room = "Master Bedroom"
  if request.args.get('room'):
      room = request.args.get('room')

  room_volume = rooms[room]['volume']
  if request.args.get('room_volume'):
      room_volume = request.args.get('room_volume')

  content = request.get_json(silent=True)
  if content:
      room = content['Room_Name']

  #Manage Lights if Girls Room
  if room == "Bedroom":
    girls_night_light("On")

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
  if room == "Bedroom":
    girls_night_light("Off")

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

  room_volume = rooms[room]['volume']
  if request.args.get('room_volume'):
      room_volume = request.args.get('room_volume')

  try:
    play_playlist(room, play_list, room_volume)
    return ("Playing %s in %s at %s volume" % (play_list, room, room_volume))
  except Exception as e:
     return ("error: %s in (room: %s)" % (e, room))


def girls_night_light(state = "Off"):
  
  plug = SmartPlug("192.168.86.113")

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
  playlists = sonos.get_music_library_information('sonos_playlists')
  for playlist in playlists:
      print("#%s#" % (playlist.title))
      if str(playlist.title) == str(playlist_name):
          print("Assigning #%s#" % (playlist_name))
          new_pl = playlist

  sonos.clear_queue()
  print("Adding %s to the queue" % (playlist.title))
  sonos.add_to_queue(new_pl)
  sonos.play_from_queue(0)
  sonos.volume = volume
  sonos.play()

if __name__ == '__main__':
    app.run(debug=True)


#if __name__ == "__main__":
#    app.run(host='0.0.0.0')

