import network
from utime import sleep_ms

def connect(ssid, password, hostname):
    """ Connect to a WiFI Access Point and obtain a DHCP address

    Args:
        ssid     (string): The network SSID to connect to
        password (string): The password for the network
        hostname (string): The hostname to register as
    
    Returns:
        string: The IP address
    """
    
    ap_if = network.WLAN(network.AP_IF)
    ap_if.active(False)
    
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        print('connecting to network...')
        sta_if.active(True)
        sleep_ms(100)
        sta_if.config(dhcp_hostname=hostname)
        sta_if.connect(ssid, password)
        while not sta_if.isconnected():
            sleep_ms(100)

    return sta_if.ifconfig()[0]