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
  * Definitely! Stepping is really quiter slow.

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

DS3231 class almost completely re-written to implement OO access methods for RTC and Alarm1. Using the FreeRTOS RTC for routine time updates, with automatic NTP updates. When NTP-syncs, set the DS from the RTC, but if there's no NTP, work the other way around since hte DS is supremely accurate.

Basic version of the main thread now working - pulses the clock fast if it is behind the realtime, but stops it if it's *"only"* an hour or so ahead as it's quicker to let real-time catch up. Clock pulsing is HYPER sensitive to duration - too fast and it can miss a pulse, or even start "sliding". Worse, a single pulse can occasionally be missed, hence now doing a 75:25 double-pulse with a short dwell in between. If the next pulse occurs too quickly, however, the clock can "glide" forward by several seconds, or even step backwards! There also appears to be a temperature sensitivity, and maybe a voltage sensitivity too.

## To Do
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
  
## OLED displays
6 lines of text available, with two buttons near top-left and bottom-left of the display
### Normal

    DG Clock
    Running / Catch-up
    Current Time
    NTP Sync / No network

    <--- Press for more

### Info

    <--- Back
    Network name
    IP Address
    Current Time
    Hand position
    <--- Stop hands

### Stop hands

    <--- Adjust hands

    Hands Stopped!
    Showing <current>

    <--- Restart hands

### Adjust hands

    <--- Accept and start
    Current  (as currently displayed)
    HH:MM:00 (current time, zero seconds)
    12:00:00
    6:00:00
    <--- Move down
