import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timedelta
from ics import Calendar, Event
import pytz  # Required for timezone handling

# Provide the URL of the webpage you want to scrape
URL = 'https://www.unimelb.edu.au/dates'  # Replace with the actual URL

response = requests.get(URL)

# Check if the request was successful
if response.status_code != 200:
    print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
    exit()

soup = BeautifulSoup(response.content, 'html.parser')

# Find all table rows in the content
rows = soup.find_all('tr', attrs={'itemscope': True})

data = []
holiday_data = []  # Separate file for events with 'holiday' or 'Holiday' in the name

# Extract dates and event names from the rows
for i, row in enumerate(rows):
    start_time = row.find('span', itemprop='startTime').get_text(strip=True) + " " + str(datetime.now().year)
    end_time_tag = row.find('span', itemprop='endTime')
    if end_time_tag:
        end_time = end_time_tag.get_text(strip=True) + " " + str(datetime.now().year)
    else:
        end_time = start_time

    # Append previous year to the first row's Start Date
    if i == 0:
        start_time = start_time.replace(str(datetime.now().year), str(datetime.now().year - 1))

    # Append next year to the last row's End Date
    if i == len(rows) - 1:
        end_time = end_time.replace(str(datetime.now().year), str(datetime.now().year + 1))

    activity = row.find('span', itemprop='name').get_text(strip=True)

    # Convert date strings to the "DD\MM\YYYY" format
    start_time_formatted = datetime.strptime(start_time, "%A %d %B %Y").strftime("%d/%m/%Y")
    end_time_formatted = datetime.strptime(end_time, "%A %d %B %Y").strftime("%d/%m/%Y")

    data.append([start_time_formatted, end_time_formatted, activity])

    # Check if 'holiday' or 'Holiday' is in the event name and append to the holiday_data list
    if 'holiday' in activity.lower():
        holiday_data.append([start_time_formatted, end_time_formatted, activity])

# Write all data to a CSV file
with open('events.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Start Date', 'End Date', 'Event Name'])  # header
    writer.writerows(data)

print("Data written to events.csv")

# Write holiday data to a separate CSV file
if holiday_data:
    with open('holiday_events.csv', 'w', newline='') as holiday_csvfile:
        holiday_writer = csv.writer(holiday_csvfile)
        holiday_writer.writerow(['Start Date', 'End Date', 'Event Name'])  # header
        holiday_writer.writerows(holiday_data)

    print("Holiday data written to holiday_events.csv")

    # Create an iCalendar object
    calendar = Calendar()

    # Define timezone (Australia/Melbourne)
    melbourne_timezone = pytz.timezone('Australia/Melbourne')

    # Read events from the CSV file and add them to the calendar
    with open('holiday_events.csv', 'r', newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader)  # Skip the header row
        for row in reader:
            start_date_str, end_date_str, event_name = row
            start_datetime = datetime.strptime(start_date_str, '%d/%m/%Y')
            end_datetime = datetime.strptime(end_date_str, '%d/%m/%Y')

            # Check for specific events and set the time frame (8 am to 8 pm)
            if event_name in ['Australia Day', 'ANZAC Day', "King's Birthday", 'AFL Grand Final']:
                start_datetime = melbourne_timezone.localize(start_datetime.replace(hour=8, minute=0))
                end_datetime = melbourne_timezone.localize(end_datetime.replace(hour=20, minute=0))

            # Create a timed event with local time
            event = Event()
            event.name = event_name
            event.begin = start_datetime
            event.end = end_datetime

            # Add the event to the calendar
            calendar.events.add(event)

    # Define the output .ics file
    output_ics_file = 'holiday_events.ics'

    # Save the calendar to the .ics file
    with open(output_ics_file, 'w') as f:
        f.write(str(calendar))

    print(f"iCalendar file '{output_ics_file}' created with holiday events.")
