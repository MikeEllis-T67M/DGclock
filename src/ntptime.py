try:
    import usocket as socket
except:
    import socket
try:
    import ustruct as struct
except:
    import struct

# NTP counts seconds from Jan 1st 1900, MicroPython uses 1970
# (date(1970, 1, 1) - date(1900, 1, 1)).days * 24*60*60
NTP_DELTA = 2208988800

def ntp_query(host = "pool.ntp.org"):
    NTP_QUERY = bytearray(48)
    NTP_QUERY[0] = 0x1B
    try:
        addr = socket.getaddrinfo(host, 123)[0][-1]
    except:
        return None
    
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(1)
        res = s.sendto(NTP_QUERY, addr)
        msg = s.recv(48)
        #print("Received: {}".format(msg))
    except OSError: # Timeout
        return None
    finally:
        try:
            s.close() # TODO: Can sometimes fail with "local variable referenced before assignment"...???
        except Exception:
            pass

    val = struct.unpack("!I", msg[40:44])[0]
    #print("Convert {} to {}".format(msg[40:44], val))
    return val - NTP_DELTA # Convert from 1/1/1900 to 1/1/1970 EPOCH

# There's currently no timezone support in MicroPython, so
# utime.localtime() will return UTC time (as if it was .gmtime())
def settime():
    t = time()
    import machine
    import utime

    tm = utime.localtime(t)
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))