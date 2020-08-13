import ujson
from time import sleep_ms, time

def load_settings(settings_file):
  try:
    fd = open(settings_file)
    encoded = fd.read()
    fd.close()
    settings = ujson.loads(encoded)
    return settings
  except Exception as e:
    print(settings_file + ": read error: " + str(e))
    
def do_connect(ssid, password, hostname):
    import network
    
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sleep_ms(100)
        # Sets the device hostname
        sta_if.config(dhcp_hostname=hostname)
        # print(sta_if.config('dhcp_hostname'))
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            pass
    

    
wifi = load_settings("wifi.json")

do_connect(wifi['SSID'], wifi['Password'], wifi['Hostname'])

#################################################################
## Raw JSON
{
    "SSID": "IOT",
    "Password": "AntherSecret!",
    "Hostname": "esp32-3.citadel.home",
}

#################################################################
# Writing the encrypted JSON
def save_settings(settings, settings_file):
  encoded = ujson.dumps(settings)
  print("Saving settings in: " + settings_file)
  try:
    fd = open(settings_file, 'w')
    fd.write(encoded)
    fd.close()
  except:
    print(settings_file + ": write error:")