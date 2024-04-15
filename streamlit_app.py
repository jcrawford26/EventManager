import streamlit as st
import pymysql
import pandas as pd
import hashlib
from datetime import datetime, timedelta

# Updated connect_to_db function to use Streamlit secrets for database credentials
def connect_to_db(db_name=None):
    # Define the list of database keys
    db_keys = ['EventManager1', 'EventManager2']
    connections = {}
    try:
        for key in db_keys:
            params = st.secrets[key]  # Fetching connection parameters from secrets
            connection = pymysql.connect(
                host=params['host'],
                user=params['user'],
                password=params['password'],
                database=params['database'],
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            connections[key] = connection
        if db_name:
            return connections[db_name]
        return connections
    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")

# Function to choose the database based on hash of the input string
def choose_database(input_string):
    hash_object = hashlib.sha256(input_string.encode())
    hash_digest = hash_object.hexdigest()
    return 'EventManager1' if int(hash_digest, 16) % 2 == 0 else 'EventManager2'

def add_venue(venue_name, city, capacity, price_per_hour):
    db_name = choose_database(venue_name)
    connection = connect_to_db(db_name)
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT ID FROM Venues WHERE Name = %s", (venue_name,))
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO Venues (Name, City, Capacity, Price_per_hour) VALUES (%s, %s, %s, %s)",
                    (venue_name, city, capacity, price_per_hour)
                )
                connection.commit()
                st.success(f"Venue '{venue_name}' added successfully.")
            else:
                st.warning(f"Venue '{venue_name}' already exists.")
    except Exception as e:
        st.error(f"An error occurred while adding the venue: {str(e)}")
    finally:
        if connection:
            connection.close()

def create_booking(client_name, date, start_time, end_time, venue_name):
    print(f"Attempting to create booking for {venue_name} at {date} from {start_time} to {end_time}")
    db_name = choose_database(venue_name)
    connection = connect_to_db(db_name)
    if connection is None:
        st.error("Failed to connect to the database.")
        return

    try:
        with connection.cursor() as cursor:
            # Ensure we are fetching the venue ID correctly
            cursor.execute("SELECT ID FROM Venues WHERE Name = %s", (venue_name,))
            venue_result = cursor.fetchone()
            if venue_result:
                venue_id = venue_result['ID']
                cursor.execute(
                    "INSERT INTO Bookings (Client_name, Date, Start_time, End_time) VALUES (%s, %s, %s, %s)",
                    (client_name, date, start_time, end_time)
                )
                booking_id = cursor.lastrowid
                cursor.execute(
                    "INSERT INTO VenueUsed (VenueID, BookingID) VALUES (%s, %s)",
                    (venue_id, booking_id)
                )
                connection.commit()
                st.success(f"Booking for '{client_name}' at '{venue_name}' has been successfully created for {date} from {start_time} to {end_time}.")
            else:
                st.error(f"Venue '{venue_name}' does not exist.")
    except Exception as e:
        st.error(f"An error occurred during booking: {e}")
    finally:
        if connection:
            connection.close()

def find_venue(search_keyword, city):
    connections = connect_to_db()  # Gets connections for both databases
    results = []
    try:
        for db_name, connection in connections.items():
            if connection:
                with connection.cursor() as cursor:
                    query = "SELECT Name, City, Capacity, Price_per_hour FROM Venues WHERE Name LIKE %s"
                    params = ['%' + search_keyword + '%']

                    if city and city != 'All':
                        query += " AND City = %s"
                        params.append(city)

                    cursor.execute(query, params)
                    results.extend(cursor.fetchall())
                connection.close()
    except Exception as e:
        st.error(f"An error occurred while searching for venues: {str(e)}")
    
    if results:
        return pd.DataFrame(results)
    else:
        st.info("No venues found matching the search criteria.")
        return pd.DataFrame()

def get_cities():
    connections = connect_to_db()  # This will get connections to both databases
    cities = set()  # Use a set to avoid duplicate city entries
    try:
        for db_name, connection in connections.items():
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT DISTINCT City FROM Venues ORDER BY City")
                    cities.update(row['City'] for row in cursor.fetchall())
                connection.close()
    except Exception as e:
        st.error(f"Failed to fetch cities: {str(e)}")
    return list(sorted(cities))

def get_all_venues():
    connections = connect_to_db()  # Make sure this returns a proper connection object
    venues = set()
        try:
            for db_name, connection in connections.items():
                if connection:
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT DISTINCT Name FROM Venues ORDER BY Name")
                        venues.update(row['Name'] for row in cursor.fetchall())
        except Exception as e:
            st.error(f"Failed to fetch venues: {str(e)}")
        finally:
            connection.close()  # Close the connection properly
    return list(sorted(venues))

def check_availability(venue_name, date, start_time, end_time):
    db_name = choose_database(venue_name)
    connection = connect_to_db(db_name)
    if connection is None:
        st.error("Failed to connect to the database.")
        return False

    try:
        with connection.cursor() as cursor:
            query = """
            SELECT COUNT(*) FROM Bookings
            JOIN VenueUsed ON Bookings.ID = VenueUsed.BookingID
            JOIN Venues ON VenueUsed.VenueID = Venues.ID
            WHERE Venues.Name = %s AND Bookings.Date = %s AND 
            NOT (%s >= Bookings.End_time OR %s <= Bookings.Start_time)
            """
            cursor.execute(query, (venue_name, date, start_time, end_time))
            overlapping_count = cursor.fetchone()['COUNT(*)']
            return overlapping_count == 0
    except Exception as e:
        st.error(f"An error occurred while checking availability: {str(e)}")
        return False
    finally:
        if connection:
            connection.close()

def create_booking_tab():
    st.header('Create a Booking')

    # Date selection at the top
    date = st.date_input('Date', key='date_book', min_value=datetime.today(), max_value=datetime.today() + timedelta(days=60))

    # Time slot selection, from 12 PM to 11 PM in one-hour increments
    time_slots = [datetime.combine(date, datetime.strptime(f"{hour}:00", "%H:%M").time()) for hour in range(12, 24)]
    selected_time_slot = st.selectbox('Select a Time Slot', time_slots, format_func=lambda x: x.strftime('%I:%M %p'))

    # Venue selection: Choose from a dropdown list or enter manually
    venue_selection_method = st.radio("Choose the venue by", ["Select from list", "Enter manually"])
    if venue_selection_method == "Select from list":
        all_venues = get_all_venues()
        venue_name = st.selectbox('Select a Venue', all_venues, key='venue_select_book')
    else:
        venue_name = st.text_input('Enter Venue Name', key='venue_name_book')

    # Check venue availability
    if st.button('Check Availability'):
        formatted_start_time = selected_time_slot.strftime('%H:%M:%S')
        formatted_end_time = (selected_time_slot + timedelta(hours=1)).strftime('%H:%M:%S')
        available = check_availability(venue_name, date, formatted_start_time, formatted_end_time)
        if available:
            st.success('The venue is available for booking.')
            st.session_state['booking_details'] = (venue_name, date, formatted_start_time, formatted_end_time)
            st.session_state['create_enabled'] = True
        else:
            st.error('The venue is not available at the selected time. Please try another time.')
            st.session_state['create_enabled'] = False

    # Prompt for client name and finalize booking if venue is available
    if st.session_state.get('create_enabled', False):
        client_name = st.text_input('Client Name', key='client_name_book')
        if st.button('Confirm Booking'):
            venue_name, date, formatted_start_time, formatted_end_time = st.session_state['booking_details']
            create_booking(client_name, venue_name, date, formatted_start_time, formatted_end_time)
            st.success("Booking created successfully!")
            del st.session_state['create_enabled']
            del st.session_state['booking_details']

# Streamlit user interface for the application
st.title('EventManager - Venue Booking Management System')

# Using tabs for better organization
tab1, tab3, tab2 = st.tabs(["Add Venue", "Find Venue", "Create Booking"])

with tab1:
    # Header for the form
    st.header('Add a New Venue')

    # Use session state to hold form values to prevent them from resetting on reruns
    if 'venue_name' not in st.session_state:
        st.session_state['venue_name'] = ''
        st.session_state['city'] = ''
        st.session_state['capacity'] = 1
        st.session_state['price_per_hour'] = 0

    # Create the form for adding a new venue
    with st.form("form_add_venue"):
        venue_name = st.text_input('Venue Name', value=st.session_state['venue_name'], key='venue_add')
        city = st.text_input('City', value=st.session_state['city'], key='city_add')
        capacity = st.number_input('Capacity', min_value=1, value=st.session_state['capacity'], key='capacity_add')
        price_per_hour = st.number_input('Price Per Hour', min_value=0, value=st.session_state['price_per_hour'], key='price_add')
        submit_button = st.form_submit_button('Add Venue')

    # Check if the submit button was pressed
    if submit_button:
        # Call the add_venue function to try adding the venue
        venue_added = add_venue(venue_name, city, capacity, price_per_hour)

        # If the venue was successfully added, reset the session state values
        if venue_added:
            st.session_state['venue_name'] = ''
            st.session_state['city'] = ''
            st.session_state['capacity'] = 1
            st.session_state['price_per_hour'] = 0
        else:
            # If there was a duplicate or error, keep the current input for the user to adjust
            st.session_state['venue_name'] = venue_name
            st.session_state['city'] = city
            st.session_state['capacity'] = capacity
            st.session_state['price_per_hour'] = price_per_hour

# find venue
with tab3:
    st.header('Find a Venue')
    
    cities = get_cities()  # Fetch list of cities from the databases

    with st.form("form_find_venue"):
        search_keyword = st.text_input('Keyword', key='keyword_find')
        location = st.selectbox('City', ['All'] + cities, key='location_find')
        search_button = st.form_submit_button('Search Venues')

        if search_button:
            results = find_venue(search_keyword, location)
            if not results.empty:
                st.dataframe(results)
            else:
                st.info('No venues found matching the search criteria.')

# Create Booking tab in Streamlit
with tab2:
    create_booking_tab()
