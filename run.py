#from eve import Eve
from flask import Flask
import soco

app = Flask(__name__)
#app = Eve()

@app.route('/sleep', methods=['GET', 'POST'])
def sleep():

  try:
    zones = soco.discover()
    for zone in zones:
        if zone.player_name == 'Master Bedroom':
            sonos = zone #.ip_address

    playlists = sonos.get_music_library_information('sonos_playlists')
    for playlist in playlists:
        print playlist.title
        if playlist.title == 'Sleep':
            new_pl = playlist

    sonos.clear_queue()
    sonos.add_to_queue(new_pl)
    sonos.play()

    return 'Running Sleep Routine'

  except Exception as e:
     return ("error: %s" % (e))

@app.route('/wake', methods=['GET', 'POST'])
def wake():

  try:
    zones = soco.discover()
    for zone in zones:
        if zone.player_name == 'Master Bedroom':
            sonos = zone

    sonos.pause()

    return 'Running Wake Routine'

  except Exception as e:
     return ("error: %s" % (e))


if __name__ == '__main__':
    app.run(debug=True)
