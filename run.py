from flask import Flask
from flask import request
import soco

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
    sonos.volume = 40
    sonos.play()

    return "Running Sleep Routine in %s" % (room)

  except Exception as e:
     return ("error: %s" % (e))

@app.route('/wake', methods=['GET', 'POST'])
def wake():

  room = "Master Bedroom"
  if request.args.get('room'):
      room = request.args.get('room')

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


if __name__ == '__main__':
    app.run(debug=True)
