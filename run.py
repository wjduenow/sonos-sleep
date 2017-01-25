from eve import Eve
import soco
#from soco import SoCo

app = Eve()

@app.route('/test')
def test():
    return 'Test'

@app.route('/hello')
def hello_world():

#  try:
    zones = soco.discover()
    for zone in zones:
        if zone.player_name == 'Master Bedroom':
            sonos = zone #.ip_address

    playlists = sonos.get_music_library_information('sonos_playlists')
    for playlist in playlists:
        print playlist.title
        if playlist.title == 'The Gambler': #'Sleep':
            new_pl = playlist

    sonos.clear_queue()
    sonos.add_to_queue(new_pl)
    sonos.play()

    return 'hello world!'

#  except: 
#    return 'error'




if __name__ == '__main__':
    app.run(debug=True)
