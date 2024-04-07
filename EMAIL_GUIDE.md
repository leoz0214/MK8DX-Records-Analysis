# Email Script - Guide
The email script automatically generates a new snapshot at set day/times, and sends emails providing information on new records since the previous snapshot.

Note: it is assumed that compatibility requirements have been met and the setup is complete. The script to run the scraper is `src/email_.py`. Obviously a decent Internet connection is necessary.

Warning: only sending through **Gmail** is supported, so a Google email must be used as the sender.

To start the script, at least **one snapshot** must be obtained manually through `src/scrape.py` before running the email script - for the initial snapshot. The input configuration file must be set correctly too, explained in a moment.

## Script Input
The script requires a **JSON configuration file** as input. The path of this file is `data/email_config.json` and must contain the following fields:
- "sender" - the **sender email address** (must be a valid Google email) e.g. "example@gmail.com"
- "password" - the **app password** of the sender email (not the same as the main password - search up Google app passwords for details).
- "recipients" - a **list of email addresses** to send to. Note, even if you only wish to send to one email address e.g. yourself, it must be placed into a list of its own e.g. ["example2@gmail.com", "example3@yahoo.com"]. Note the recipients do not have to be Google emails.
- "day_times" - a **list of day/time** pairs to refresh the data and send update emails at. The list must consist of sub-lists of length 2 in the format [day_of_week, 24_hour_time], where day_of_week is a case-sensitive day of the week e.g. Monday and 24_hour_time is the time of the day to send at in HHMM (based on the **UTC** time zone). If only planning to send at one day/time, it must still be in a nested list. For example, the following is valid: \[\["Friday", "2200"]]

An overall JSON configuration file could be like so:
{"sender": "example@gmail.com", "password": "app_password123", "recipients": ["example2@gmail.com","example3@yahoo.com"], "day_times": \[\["Friday", "2200"]]}

## Script Logic
Provided the above requirements have been met, the script will proceed to run indefinitely, until an error occurs. Here is the script's logic explained in depth:
- At regular intervals, the config file is loaded and the day/times to send at are compared with the current day/time. If there is a **matching day/time** (to the minute), the email sending process begins, otherwise the script sleeps and checks again in a moment.
- The scraping script is run and a **new snapshot** is generated accordingly. This process takes about 7 minutes.
- The new snapshot that was just obtained is **compared** with the previous snapshot. Courses/CCs with new records between this time will have the new record outlined in the email. This includes all data on the record: player, time, character etc. and including a video link if available.
- If there have been no new records within the time frame, this is indicated in the email.
- The email is sent using **BCC** (blind carbon-copy).
- The process repeats.
- Logging is provided in the `email.log` file.

## Additional Notes
The script works effectively and performs the required functionality. Additional points to note include:
- The input data is carefully **validated** to ensure integrity. Any invalid input data will cause the script to crash immediately. 
- **Changes to the config** file will be registered even when the script is already running - there is no need to restart the script.
- Since re-scraping all records takes around **7 minutes**, if you wish to time your email better, consider setting the time to be a bit **earlier** than the actual send time. For example, if you have scheduled a send at Friday 2200, consider setting this to Friday 2153 or 2154 so the timing is better.
- Best usage of this script involves running it indefinitely. This is up to you and could be achieved using an old computer left on permanently, or more practically, a **cloud server**. 
