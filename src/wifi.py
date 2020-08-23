import network
from utime import sleep_ms

def connect_sta(ssid, password, hostname):
    """ Connect to a WiFI Access Point and obtain a DHCP address

    Args:
        ssid     (string): The network SSID to connect to
        password (string): The password for the network
        hostname (string): The hostname to register as
    
    Returns:
        string: The IP address
    """   
    try:
        sta_if = network.WLAN(network.STA_IF)
        if not sta_if.isconnected():
            print('connecting to network...')
            sta_if.active(True)
            sleep_ms(100)
            sta_if.config(dhcp_hostname=hostname)
            sta_if.connect(ssid, password)
            tries = 1
            while not sta_if.isconnected() and tries < 5:
                sleep_ms(100)
                tries += 1
    except:
        pass # If no WiFi, gracefully fail

    if sta_if.isconnected():
        return sta_if.ifconfig()[0]
    else:
        return None

def setup_ap(ssid, password, hostname):
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(True)
    sleep_ms(100)
    ap_if.config(essid = ssid, authmode = network.AUTH_WPA2_PSK, password = password)
    return ap_if.ifconfig()