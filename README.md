# DGclock
## Driving the DG's Pulse Clock

The DG has a semi-working, manually adjusted Pulse Clock in his office. How can we make this into an accurate, automatic-setting clock?

## Open questions:
* Motor drive voltage and current
* Motor pulse characteristics - bi-phase assumed
* Hand position sensors - will capacitive sensiing work?
* Hand identification - pulse counting? Hand length?
* WiFi setup - WPS only, or WPS plus minimal manual UI?
* WPA2 only?
* Auto-detecting slipped hands?
* Stopping rather than spinning for small backward adjustments?
* Leapsecond handling

## Outline solution

Use a TTGO-T ESP32 processor with built-in WiFi, Bluetooth, GPIO and capacitive sensors driving the motor via an off-the-shelf H-bridge board. Get the current time and date via NTP over WiFi, then step the hands appropriately.

