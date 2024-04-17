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
    db_name = choose_database(venue_name)
    connection = connect_to_db(db_name)
    try:
        with connection.cursor() as cursor:
            # Ensure we are fetching the venue ID correctly
            cursor.execute("SELECT ID FROM Venues WHERE LOWER(Name) = LOWER(%s)", (venue_name,))
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
        st.error(f"An error occurred during booking: {str(e)}")
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
                    connection.close()  # Close the connection properly
    except Exception as e:
        st.error(f"Failed to fetch venues: {str(e)}")
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

def get_venue_hourly_rate(venue_name):
    # Fetch all venues that match the venue_name (assuming exact match isn't necessary)
    venue_details = find_venue(venue_name, "")
    if not venue_details.empty:
        # Assuming the venue name is unique and we take the first match
        return venue_details.iloc[0]['Price_per_hour']
    return 0


# Streamlit user interface for the application
st.title('EventManager - Venue Booking Management System')

# Define two main tabs: User and Admin
tabs = st.tabs(["User", "Admin"])

# User tab with sub-tabs for finding venues and creating bookings
with tabs[0]:
    user_tabs = st.tabs(["Find Venue", "Create Booking"])

    # Find Venue tab
    with user_tabs[0]:
        st.header('Find a Venue')
        cities = get_cities()  # Fetch list of cities from the databases
        
        with st.form("find_venue_form"):
            search_keyword = st.text_input('Keyword', key='keyword_find')
            location = st.selectbox('City', ['All'] + cities, key='location_find')
            search_button = st.form_submit_button('Search Venues')

            if search_button:
                results = find_venue(search_keyword, location)
                if not results.empty:
                    st.dataframe(results)
                else:
                    st.info('No venues found matching the search criteria.')

    # Create Booking tab
    with user_tabs[1]:
        st.header('Create a Booking')
        create_booking_tab()  # This function encapsulates the booking creation logic

# Admin tab for adding new venues
with tabs[1]:
    st.header('Add a New Venue')
    
    # Session state to hold form values to prevent them from resetting on reruns
    if 'venue_name' not in st.session_state:
        st.session_state.venue_name = ''
        st.session_state.city = ''
        st.session_state.capacity = 1
        st.session_state.price_per_hour = 0

    with st.form("add_venue_form"):
        venue_name = st.text_input('Venue Name', value=st.session_state.venue_name, key='venue_name')
        city = st.text_input('City', value=st.session_state.city, key='city')
        capacity = st.number_input('Capacity', min_value=1, value=st.session_state.capacity, key='capacity')
        price_per_hour = st.number_input('Price Per Hour', min_value=0, value=st.session_state.price_per_hour, key='price_per_hour')
        submit_button = st.form_submit_button('Add Venue')

        if submit_button:
            add_venue(venue_name, city, capacity, price_per_hour)
            st.session_state.venue_name = ''
            st.session_state.city = ''
            st.session_state.capacity = 1
            st.session_state.price_per_hour = 0
