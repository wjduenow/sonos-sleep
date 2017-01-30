from flask import Flask
from flask import request
import soco
from pyHS100 import SmartPlug
from pprint import pformat as pf

app = Flask(__name__)

@app.route('/sleep', methods=['GET', 'POST'])
def sleep():

  room = "Master Bedroom"
  if request.args.get('room'):
      room = request.args.get('room')

  content = request.get_json(silent=True)
  if content:
#['Room_Name']:
      room = content['Room_Name']

  if room == "Bedroom":
    girls_night_light("On")


  try:
    zones = soco.discover()
    for zone in zones:
        if zone.player_name == room:  #'Master Bedroom':
            sonos = zone #.ip_address

    playlists = sonos.get_music_library_information('sonos_playlists')
    for playlist in playlists:
        print playlist.title
        if playlist.title == 'Sleep':
            new_pl = playlist

    sonos.clear_queue()
    sonos.add_to_queue(new_pl)
    sonos.volume = 35
    sonos.play()



    return "Running Sleep Routine in %s" % (room)

  except Exception as e:
     return ("error: %s" % (e))

@app.route('/wake', methods=['GET', 'POST'])
def wake():

  room = "Master Bedroom"
  if request.args.get('room'):
      room = request.args.get('room')

  if room == "Bedroom":
    girls_night_light("Off")

  content = request.get_json(silent=True)
  if content:
#['Room_Name']:
      room = content['Room_Name']

  try:
    zones = soco.discover()
    for zone in zones:
        if zone.player_name == room: #'Master Bedroom':
            sonos = zone

    sonos.pause()

    return "Running Wake Routine in %s" % (room)

  except Exception as e:
     return ("error: %s" % (e))


def girls_night_light(state = "Off"):
  plug = SmartPlug("192.168.250.186")
  if state == "On":
    plug.turn_on()
    plug.led = False
  else:
    plug.turn_off()
    plug.led = True

if __name__ == '__main__':
    app.run(debug=True)
