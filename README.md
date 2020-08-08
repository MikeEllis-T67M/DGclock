# DGclock
## Driving the DG's Pulse Clock

The DG has a semi-working, manually adjusted Pulse Clock in his office. How can we make 
this into an accurate, automatic-setting clock?

## Open questions:
### Basic mechanics
* Motor drive voltage and current **24V bi-phase pulse per second**

### WiFi
* WiFi setup - WPS only, or WPS plus minimal manual UI?
* WPA2 only?
* Could also run a minimal UI over an isolated AP...

### Hand positioning
* Hand position sensors
  * Will capacitive sensing work? **No**
  * Will magnetic sensing work? **Maybe**
    * Hand weight balance is an issue
    * Second hand is only ~1mm wide
    * Risk of hands sticking to each other as they pass
  * Will optical sensing work? **Maybe, but would disfigure face**
* Hand identification
  * Pulse counting? Hand length?  Auto-detecting slipped hands? 
    * Possible... but...only if hand position detection can be made to work
  * Hands are pretty solidly held in position without power
    * Pulse counting might actually be practicable
    * NV storage of "last known hand position" may be enough
* Stopping rather than spinning for small backward adjustments?
  * Definitely!

### Knowing the time
* NTP from a pool server **Yes**
* Time zone selection? Assume London? **Maybe mini UI???**
  * DST switching
  * From Timezone file...?
* Leapsecond handling
  * Knowing when there is one - might come from NTP


## Outline solution

Use a TTGO-T ESP32 processor with built-in WiFi, Bluetooth, GPIO and capacitive sensors driving the motor via an off-the-shelf H-bridge board. Get the current time and date via NTP over WiFi, then step the hands appropriately. Provide a stand-alone WiFi AP running a minimal UI for configuration, and/or use the two buttons for an even more minimal UI.

Circuit now built and working. Motor drive is configured such that Pin 25 drives from even numbered seconds to odd seconds, while Pin 26 drives from odd seconds to even. Pulse length of around 125ms just about works, but 200ms is much more reliable. Actively stopping the hands before disabling the driver produces a "nicer" look to the movement. Stop duration about the same as the pulse duration is best - but this does seriously limit the maximum speed the clock can be moved.

DS3231 class almost completely re-written to implement OO access methods for RTC and Alarm1. 

Basic version of the main thread now working - pulses the clock fast if it is behind the realtime, but stops it if it's *"only"* an hour or so ahead as it's quicker to let real-time catch up.

## To Do
* Set the DS3231 RTC from NTP - kinda done, but via the FreeRTOS RTC which runs in localtime mode not UTC, so.... 
* Periodically align the FreeRTOS RTC from the DS3231 - set to every 60 seconds for debug purposes
* Process a TZ description - tricky given that the FreeRTOS RTC runs in localtime
  * Applying the change at the right time given it's written in local time but the RTC is in UTC
* Use the OLED for a status display
  * Manually set hands to midnight and press "go"?
* Set up AP
* Build a simple UI config web form
  * WiFi parameters
  * Timezone description
  * Hand position - and ensure the pulse polarity is adjusted correctly
* Handle leap seconds (more) elegantly {???}

### DS3231 class

**None of these are critical for this application**

Need to add support for:
  * Alarm2
  * Interrupts
  * Squarewave generator
  * Clock stop/start control
  

