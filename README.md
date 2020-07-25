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
