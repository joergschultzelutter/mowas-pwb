# mowas-pwb
[MOWAS](https://de.wikipedia.org/wiki/MoWaS) personal warning beacon

- User can specify 1..n fixed sets of lat/lon coordinates which will be validated against MOWAS warnings.
- Additionally, licensed amateur radio operators can specify an APRS call sign whose lat/lon coordinates will also be monitored
- User can specify a minimal warning level which needs to be met for triggering a message (e.g. "Severe", "Extreme"). mowas-pwb will only send messages to the user if the message's sttatus is greater or equal to the given warning level.
- In addition to the aforementioned warning level, the user can specify a warning level threshold. Any messages whose status is equal or greater to this threshold will be forwarded to the user's DAPNET account with high priority.

Supported MOWAS features: 
- supports all current MOWAS categories (tempest, flood, wildfire, earthquake, emergency announcements)
- supports alerts, updates and cancellation messages

## Command line parameters:

    Blah
    Blah
