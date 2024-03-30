# Mario Kart 8 Deluxe – World Record Data Analysis

This project involves **scraping Mario Kart 8 Deluxe world records** from the following website: https://mkwrs.com/mk8dx/, storing these records in a SQLite database, processing the data, and yielding interesting insights.

The following is a summary of what I hope to achieve in this project:
- Create a script to **scrape all 192 web pages** (150cc and 200cc for each of the 96 courses) and store the data into a SQLite database.
- Create a GUI to view **various analytics** regarding the collected data. There is no point in directly displaying the raw data since the website can simply be visited to view full data. Instead, relevant **graphs, tables and stats** will be shown instead. **Date filtering** and exporting to **CSV/XLSX/DOCX/PDF** will be supported.
- Create a script to refresh the data automatically every week (or any other suitable timeframe) and send an **email with new records** (including ties), including video links if available.

A nice, relaxed project whilst still practicing key programming skills. The project will be developed such that a moderately technical user could use the different features comfortably.