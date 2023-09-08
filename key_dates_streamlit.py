import streamlit as st
import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime, timedelta
from ics import Calendar, Event
import pytz
import base64

# Function to create a timed event with local time
def create_timed_event(event_name, start_datetime, end_datetime):
    event = Event()
    event.name = event_name
    event.begin = start_datetime
    event.end = end_datetime
    return event

# Function to convert date strings to the "DD\MM\YYYY" format
def format_date(date_str):
    date_obj = datetime.strptime(date_str, "%A %d %B %Y")
    return date_obj.strftime("%d/%m/%Y")

# Streamlit web app
st.title("UniMelb Holiday Events Scraper and Calendar generator")

# Instructions
st.markdown("Please visit UniMelb Holiday dates website: [UniMelb Holiday Dates](https://www.unimelb.edu.au/dates/university-holidays)\n\n"
            "Select the year, copy the link, and paste it in the input below.")

# Input URL
url = st.text_input("Enter the URL of the webpage to scrape:")

if st.button("Scrape and Generate Calendar"):
    if not url:
        st.error("Please enter a valid URL.")
    else:
        response = requests.get(url)

        if response.status_code != 200:
            st.error(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        else:
            soup = BeautifulSoup(response.content, 'html.parser')

            # Find all table rows in the content
            rows = soup.find_all('tr', attrs={'itemscope': True})

            data = []
            holiday_data = []

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
                start_time_formatted = format_date(start_time)
                end_time_formatted = format_date(end_time)

                data.append([start_time_formatted, end_time_formatted, activity])

                if 'holiday' in activity.lower():
                    holiday_data.append([start_time_formatted, end_time_formatted, activity])

            # Display the list of events
            st.header("List of All Events:")
            st.table(data)

            # Highlight events with 'holiday / Holiday'
            st.header("Holiday Events:")
            highlighted_events = [event for event in data if 'holiday' in event[2].lower()]
            st.table(highlighted_events)

            # Create an iCalendar object
            calendar = Calendar()

            # Define timezone (Australia/Melbourne)
            melbourne_timezone = pytz.timezone('Australia/Melbourne')

            # Read events from the CSV file and add them to the calendar
            for row in holiday_data:
                start_date_str, end_date_str, event_name = row
                start_datetime = datetime.strptime(start_date_str, '%d/%m/%Y')
                end_datetime = datetime.strptime(end_date_str, '%d/%m/%Y')

                if event_name in ['Australia Day', 'ANZAC Day', "King's Birthday", 'AFL Grand Final']:
                    start_datetime = melbourne_timezone.localize(start_datetime.replace(hour=8, minute=0))
                    end_datetime = melbourne_timezone.localize(end_datetime.replace(hour=20, minute=0))

                event = create_timed_event(event_name, start_datetime, end_datetime)
                calendar.events.add(event)

            # Save the calendar to the .ics file
            with open('holiday_events.ics', 'w') as f:
                f.write(str(calendar))

            # Create a button to download the .ics file
            st.header("Download iCalendar (.ics) File:")
            with open('holiday_events.ics', 'rb') as f:
                file_contents = f.read()
                b64 = base64.b64encode(file_contents).decode()
                href = f'<a href="data:file/ics;base64,{b64}" download="holiday_events.ics">Download iCalendar (.ics) file</a>'
                st.markdown(href, unsafe_allow_html=True)
