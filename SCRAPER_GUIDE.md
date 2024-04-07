# Scraping Script - Guide
The scraping script is the primary script of the program and is run to collect all MK8DX records data into the database.

Note: it is assumed that compatibility requirements have been met and the setup is complete. The script to run the scraper is `src/scrape.py`. Obviously a decent Internet connection is necessary.

## Script Logic
Simply run the script and the data will be collected and output in the generated `data/snapshots` folder as a database.

Nonetheless, below are key points in how this script works, in detail, and what data is captured:
- Each course as specified in `data/_courses.json` is iterated over and the **150cc and 200cc** records for each course are obtained from the website. Note, there are 96 courses (including the **Booster Pass** courses), thus 96 x 2 = **192** web pages will be scraped.
- The scraping is throttled to **2 seconds per page** to reduce the burden on the web server. This means that the script should take around 2 x 196 = 392 seconds ~ **7 minutes** to complete, which is reasonable.
- If any requests to the web server fail, they are **retried** twice before the script crashes.
- Suitable **logging** is included in the script, which can be viewed in the generated `data/scrape.log` file.
- Snapshots are stored in the `data/snapshots` folder with **UTC date/time** as their name.
- Up to **5 recent snapshots** are stored, older ones are automatically deleted. This is because the accumulation of past snapshots is unnecessary since new snapshots build on older ones anyways.

## Data Fields
In terms of the actual data obtained, here are the captured data points, taking the first record from https://mkwrs.com/mk8dx/display.php?track=Mario+Kart+Stadium as an example in each case:
- **Course name** - the full name of the course the record involves e.g *Mario Kart Stadium*. This is stored as a unique integer in the database to save some space.
- **Cubic capacity** - whether the record is 150cc or 200cc. Stored as a Boolean in the program, where True indicates 200cc.
- **Date** - the date the record was achieved, where *Pre-release* records will have the date set as NULL.
- **Time** - the finish time of the record, stored internally in milliseconds e.g. 102184 (equivalent to *1:42.184*).
- **Player** - the name of the player who achieved the record e.g. *Crazykonga*.
- **Country** - the country of the player who achieved the record e.g. *France*.
- **Days lasted** - the number of days a previous record lasted, or has lasted, where <1 will be interpreted as 0 for simplicity.
- **Lap times** - the number of milliseconds each lap took, set to NULL if data is unavailable. Stored as a tuple string in the database e.g *(35143, 33699, 33342)*.
- **Coins** - the number of coins obtained per lap, set to NULL if data is unavailable. Again, stored as a tuple string in the database e.g. *(7, 3, 0)*.
- **Mushrooms** - the number of mushrooms used per lap, set to NULL if data is unavailable e.g. *(1, 1, 1)*.
- **Character** - the character used in the record, with coloured/style variants indeed considered distinct and NULL indicating no data, e.g. *Dry Bowser*.
- **Kart** - the vehicle used in the record with NULL indicating no data, e.g. *Wild Wiggler*.
- **Tyres** - the wheels used in the record with NULL indicating no data e.g. *Slim*.
- **Glider** - the glider used in the record with NULL indicating no data e.g. *Super Glider*.
- **Video link** - a video link serving as visual proof of the record, likely a YouTube link to a video of the MK8DX records channel, with no video being considered NULL.

Indeed, this covers all the data that can be seen in the huge table of all courses/CCs.

## Additional Notes
The script is robust and works well, collecting as much data as possible and handling missing entries properly. Additional points to note include:
- **GCN Baby Park** is the edge case of the script since it has a torturous **7 laps** instead of 3 laps. Hence, the table for this course is slightly different compared to the others - https://mkwrs.com/mk8dx/display.php?track=GCN+Baby+Park. The script handles this by ensuring data of all 7 laps is captured correctly, through special code to handle this distinct table.
- Unfortunately, it is possible for the script to break at some point if the **website changes**. The only solution will be to update the script to account for any site changes.