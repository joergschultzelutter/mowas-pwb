# Useful information

## TTL and general processing logic

### MOWAS "Alert" and "Update" message types

``mowas-pwb`` uses a decaying memory dictionary which will prevent message duplicates being sent to the user. The program's default life span for a messsage is 8 hours. If a MOWAS message (identified by its unique MOWAS message ID) has been sent to the user, it will enter this decaying dictionary. The same MOWAS message ID's content will be resent to the user if:

- the MOWAS message ID is already present in the dictionary but changed its status (e.g. a message's status was changed from "Alert" to "Update")
- the MOWAS message ID's is already present in the dictionary, its status in the dictionary AND in the current message is "Update" AND its update time stamp has changed. This indicates a message that was at least updated twice ("Alert" -> "Update" (1) --> "Update" (2))
- the MOWAS message ID is NOT present in the dictionary AND its status is either "Alert" or "Update". We may never either have never encountered this message yet or it was already present in our dictionary but its entry has already expired. In that case, we will simply resend the message again and re-add the MOWAS message ID to our dictionary.

If at least one "Alert" or "Update" message has been detected during a program cycle __which was deemed to be forwarded to the user__, ``mowas-pwb`` will assume that there is an incident going on. The sleep interval will change from 60 to 15 mins (default settings), thus allowing the program to stay up to date with any ongoing changes.

### MOWAS "Cancel" message type

Similar to the "Alert" and "Update" message types, ``mowas-pwb`` will handle "Cancel" messages in the following way:

- If the MOWAS message ID is already present in the dictionary and its status has changed from "Alert"/"Update" to "Cancel", ``mowas-pwb`` will send out a cancel message to the user for one last time. The MOWAS message ID is then removed from the decaying dictionary.
- If the MOWAS message ID is NOT present in the dictionary AND its status is "Cancel", the program will ignore this message. The MOWAS interface has no official documentation and it is unknown for how long a "Cancel" message will be present in the data stream. Rather than re-sending "Cancel" messages over and over, the program will ignore these cases.

The potential side effect for this constraint is that if you start the program and there is a MOWAS "Cancel" message for your watch area(s), you will not receive a message by the program. You WOULD have received one if that area had either been in "Alert" or "Update" status, though. Anyway, as the imminent danger is over, that cancellation message will no longer be sent to the user.

## Known issues

- In order to match with a given watch area, the user's coordinates (```mowas_watch_areas``` from the program config file) have either to be _inside_ of the given polygon or _intersect_ with it.
- Currently, there is no option that enables the user to specify and additional proximity to that polygon ("Polygon plus 10km distance")
- This program uses native MOWAS data. All warning messages are in German - there does not seem to be an international message warning interface.
- Obviously, the current version of this program does not scale and cannot support multiple user's needs with just one program instance -  you can specify only _one_ DAPNET/Telegram/Email target account.
- As the MOWAS APIs are not officially available to end users, government authorities might either terminate the services without notice and / or change the format settings of the services that are currently exposed (but not officially available to end users)
- Although all MOWAS messages do contain warncell references (which allows the program's DAPNET part to use the region's abbreviated region description), certain messages do contain invalid warncell identifiers. If such an case is encountered, MOWAS will use the (lenghty) original regional description instead. For DAPNET messages which are limited to 80 characters per message, the program will try to shorten that description by removing some clutter from that message.
- If you want to use this program for a different country's warning system:
    - remove the call for retrieving the 'warncell' information - this one is only relevant to German users
    - replace the MOWAS module with your country's native warn system parser code
    - change the DAPNET message group setting from ``dl-all`` (Germany) to your locale's transponder group.
- There is no message dupe check; if the same message is present in more than one MOWAS category and ``mowas-pwb`` deemed this message to be valid for your coordinates and program parameters' selection, you may receive that message more than once - unless the MOWAS government feed provides the message with the same unique identifier.
- All MOWAS messages contain a LOT of text, meaning that DAPNET users will likely receive a lot of messages in case an alarm is triggered (keep in mind that DAPNET is limited to 80 chars per messages). Unfortunately, abbreviated warning messages are not available.
- You may want to set up you Telegram bot as a private bot, thus preventing other Telegram users from discovering and using it. Good instructions on how to do this can be found here: [https://sarafian.github.io/low-code/2020/03/24/create-private-telegram-chatbot.html](https://sarafian.github.io/low-code/2020/03/24/create-private-telegram-chatbot.html).
