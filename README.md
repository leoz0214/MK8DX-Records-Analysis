# Mario Kart 8 Deluxe – World Record Data Analysis

Released in 2017, ***Mario Kart 8 Deluxe*** has become one of the most popular racing games of all time as per the series. Indeed, there exists the concept of **time trials** and thus world record times for all courses, both 150cc and 200cc.

This Python project involves **scraping Mario Kart 8 Deluxe world records** from the following website: https://mkwrs.com/mk8dx/, storing these records in a SQLite database, processing the data, and yielding interesting insights in a detailed GUI, even allowing data exportation.

The following is a summary of the components of the project:
- A script to **scrape all 192 web pages** (150cc and 200cc for each of the 96 courses) and store the data into a SQLite database serving as a snapshot of all the records. Data collected includes but is not limited to: date, time, player, country, build etc.
- A detailed GUI to view **various analytics** regarding the collected data. You can analyse records by **individual course/CC** combinations or **general 150cc/200cc** records analysis. Many **tables** will be available, with some **graphs** too. It is possible to create multiple tabs allowing you to perform **parallel analysis**. Exporting to **tabular** form (CSV/XLSX) and **document** form (DOCX/PDF) is supported in a moderately flexible way.
- Another script to refresh the data automatically at set time frames and send an **email** to given recipients regarding the course/CC combinations with **new records** since the previous stored snapshot.

If you are interested in exploring the project further or are even considering using it in some way, great! An installation/requirements guide follows, and guides on how to use the 3 main components are available in this repository.

## Requirements/Setup
Depending on which components you wish to use, the requirements and compatibility vary.

Overall, **Python 3.10** and above is supported. Ensure a suitable version of Python has been installed before proceeding.

### Scraping Script
The scraping script is the core of the program by collecting and storing the data from the website. It is relied on by all other components of the program so is the bare minimum to use the project at all.

#### Compatibility
The script has proven to work on Windows and Linux, and should thus work on MacOS too. There is nothing explicitly platform-specific.

#### Setup
Follow these steps to ensure the scraping script can be used.
1. Ensure all the libraries in the `core_requirements.txt` file have been installed using pip.
2. Extract the following files into an empty folder (if this is too much hassle or if you indeed plan to use the entire project, simply download the entire project folder and ignore any irrelevant files for your use case):
    - `data/_courses.json`
    - `src/const.py`
    - `src/scrape.py`
    - `src/utils.py`
3. The program can be run through the `src/scrape.py` file. Run it like any Python program.
4. [Guide](SCRAPER_GUIDE.md)

### GUI
The GUI processes the collected data in detailed ways and outputs various tables, stats and graphs, with the ability to export data for external analysis and viewing.

#### Compatibility
The GUI has been demonstrated to work correctly on Windows. It should generally work for MacOS, but this has not been confirmed and system differences might cause partial issues. It is unlikely to work on Linux.

#### Setup
Follow these steps to ensure the GUI can be used.
1. Ensure the scraping script has been fully set up.
2. Ensure all the libraries in the `gui_requirements.txt` file have been installed using pip.
3. Alongside the scraping script files, ensure the following files have been included:
    - `data/_cups.json`
    - The entire `bin` folder
    - The entire `src/gui` folder
4. The GUI can be run through the `src/gui/main` file.
5. [Guide](GUI_GUIDE.md)

### Email Script
The email script automatically refreshes the records dataat configured times and sends an email to set recipients outlining new records since the previous snapshot.

#### Compatibility
Like the scraping script, the email script should work on Windows, MacOS and Linux.

#### Setup
Follow these steps to set up the email script:
1. Ensure the scraping script has been fully set up.
2. Ensure all the libraries in the `email_requirements.txt` file have been installed using pip.
3. Alongside the scraping script files, ensure the `src/email_.py` file is included.
4. The script can be run through the `src/email_.py` file.
5. [Guide](EMAIL_GUIDE.md)

Note: The script needs to run all the time to work correctly. If truly interested in leveraging it, find a way to keep it running non-stop, such as on a cloud server.

## Disclaimer
Unsurprisingly, this project is just for fun and has no real-world use other than allow those who are truly interested in MK8DX time trial records data explore it in great depth and also be able to stay updated with new records. It is still an interesting and niche project nonetheless.

The source code is available to read and can be used and modified freely without restriction. However, there will be NO LIABILITY for any issues caused by using the program.

The project relies on an external data source (https://mkwrs.com/mk8dx/), hence it is possible for the website to change at any time, thus breaking the scraping script and rendering the project broken. Hopefully this will not occur, but be wary of the possibility. There does not seem to be any bot detection on the website but the program scrapes the data at a respectful speed nonetheless which ideally should not be modified.