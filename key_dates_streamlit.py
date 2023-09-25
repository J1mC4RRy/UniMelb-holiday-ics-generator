import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from ics import Calendar, Event
import pytz
import base64
import pandas as pd

# Function to create a timed event with local time starting at 9 AM and ending at 5 PM
def create_timed_event(event_name, start_datetime, end_datetime):
    event = Event()
    event.name = f'[HOLIDAY] {event_name}'  # Prefix event_name with '[HOLIDAY]'
    
    # Set the start time to 9 AM and the end time to 5 PM
    start_datetime = start_datetime.replace(hour=9, minute=0)
    end_datetime = end_datetime.replace(hour=17, minute=0)
    
    event.begin = start_datetime
    event.end = end_datetime
    return event

# Function to convert date strings to the "DD\MM\YYYY" format
def format_date(date_str):
    date_obj = datetime.strptime(date_str, "%A %d %B %Y")
    return date_obj.strftime("%d/%m/%Y")

# Function to generate a download link for a binary file
def get_binary_download_link(file_path):
    with open(file_path, 'rb') as f:
        file_contents = f.read()
        b64 = base64.b64encode(file_contents).decode()
        href = f'<a href="data:file/ics;base64,{b64}" download="{file_path}">Download iCalendar (.ics) file</a>'
        return href

# Streamlit web app
st.title("UniMelb Holiday Calendar Generator")

# Instructions
st.markdown("Select the year from the dropdown below, and then click 'Scrape and Generate Calendar' to generate the calendar for that year.")

# Get the current year and convert it to a string
current_year = datetime.now().year
current_year_str = str(current_year)

# Year selection dropdown with the current year as the default
selected_year = st.selectbox("Select the year:", ["2022", "2023", "2024"], index=["2022", "2023", "2024"].index(current_year_str))

# Define URLs for different years
year_to_url = {
    "2022": "https://www.unimelb.edu.au/dates/university-holidays?queries_year_fquery=previous_year",
    "2023": "https://www.unimelb.edu.au/dates/university-holidays?queries_year_fquery=this_year",
    "2024": "https://www.unimelb.edu.au/dates/university-holidays?queries_year_fquery=next_year"
}

# Input URL
url = year_to_url.get(selected_year, "")

if st.button("Scrape and Generate Calendar"):
    if not url:
        st.error("Please select a valid year.")
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
                start_time = row.find('span', itemprop='startTime').get_text(strip=True) + " " + selected_year
                end_time_tag = row.find('span', itemprop='endTime')
                if end_time_tag:
                    end_time = end_time_tag.get_text(strip=True) + " " + selected_year
                else:
                    end_time = start_time

                # Append previous year to the first row's Start Date
                if i == 0:
                    start_time = start_time.replace(selected_year, str(int(selected_year) - 1))

                # Append next year to the last row's End Date
                if i == len(rows) - 1:
                    end_time = end_time.replace(selected_year, str(int(selected_year) + 1))

                activity = row.find('span', itemprop='name').get_text(strip=True)
                start_time_formatted = format_date(start_time)
                end_time_formatted = format_date(end_time)

                if 'holiday' in activity.lower():
                    holiday_data.append({"Start Date": start_time_formatted, "End Date": end_time_formatted, "Holiday Name": activity})

            # Highlight events with '[HOLIDAY]' prefix with custom column headers
            if holiday_data:
                st.header("Holiday Events:")
                st.write(pd.DataFrame(holiday_data))

                # Create an iCalendar object
                calendar = Calendar()

                # Define timezone (Australia/Melbourne)
                melbourne_timezone = pytz.timezone('Australia/Melbourne')

                # Read events from the CSV file and add them to the calendar
                for row in holiday_data:
                    start_date_str, end_date_str, event_name = row.values()
                    start_datetime = datetime.strptime(start_date_str, '%d/%m/%Y')
                    end_datetime = datetime.strptime(end_date_str, '%d/%m/%Y')

                    # Set the event to start at 9 AM and end at 5 PM
                    start_datetime = melbourne_timezone.localize(start_datetime.replace(hour=9, minute=0))
                    end_datetime = melbourne_timezone.localize(end_datetime.replace(hour=17, minute=0))

                    event = create_timed_event(event_name, start_datetime, end_datetime)
                    calendar.events.add(event)

                # Save the calendar to the .ics file
                ics_filename = f'holiday_events_{selected_year}.ics'
                with open(ics_filename, 'w') as f:
                    f.write(str(calendar))

                # Create a button to download the .ics file
                st.header("Download iCalendar (.ics) File:")
                st.markdown(get_binary_download_link(ics_filename), unsafe_allow_html=True)

# Collapsible "How Does It Work?" section
with st.expander("**How Does It Work?**"):
    st.write("**1. Choose the Year:**")
    st.write("Pick a year (2022, 2023, or 2024) for your calendar.")

    st.write("**2. Generate the Calendar:**")
    st.write("Hit the 'Generate' button, and the app will collect holiday dates and names from the [University of Melbourne's website](https://www.unimelb.edu.au/dates/university-holidays?queries_year_fquery=this_year) for the chosen year.")

    st.write("**3. Behind the Scenes:**")
    st.write("The app works behind the scenes to create a calendar file (iCalendar) with all the holidays, naming them '[HOLIDAY] Holiday Name.'")

    st.write("**4. Download and Enjoy:**")
    st.write("You can download the calendar and import it into Outlook or your favorite calendar app. Now, you have all the holiday events in your calendar, starting at 9 AM and ending at 5 PM.")

# Hide Streamlit footer by injecting custom CSS
st.markdown(
    """
    <style>
    footer {
        visibility: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True
)
