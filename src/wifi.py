import network
from utime import sleep_ms

class wifi:
    def __init__(self, config):
        self.config     = config
        self.connection = 0
        self.tries      = 0
        self.sta        = network.WLAN(network.STA_IF)
        self.connected  = False


    def __repr__(self):
        '''Returns representation of the object'''
        return("{}({!r})".format(self.__class__.__name__, self.config))

    def connect(self):
        """ Ensure we have a network connection. If not connection, try each set of credentials in turn
            up to ten times before trying the next connection.
        """        
        if self.sta.isconnected():  # If we have an active connection, our work is done.
            if not self.connected:
                print("Connected to connection {}".format(self.connection))
                self.connected = True
            return

        self.connected = False

        if self.tries > 9: # Tried this connection ten times - try the next one
            self.tries       = 0
            self.connection += 1
            self.connection %= len(self.config)

        # We're not connected - so try again
        print("Trying WiFi connection #{}".format(self.connection))
        self.sta.active(True)
        sleep_ms(20)
        self.sta.config(dhcp_hostname = self.config[self.connection]['Hostname'])
        self.sta.connect(self.config[self.connection]['SSID'], self.config[self.connection]['Password'])
        self.tries += 1

    def get_ip_addr(self):
        """ Get the current IP address

        Returns:
            String: Current IP address, or None if not connected
        """        
        if self.sta.isconnected():
            return self.sta.ifconfig()[0]
        else:
            return None          

# ---- Old code below here -----------------------------------------------------------------------------------
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