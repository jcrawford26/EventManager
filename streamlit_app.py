import streamlit as st
import pymysql
import pandas as pd
import hashlib

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
                st.success(f"Booking for '{client_name}' added successfully and linked to venue '{venue_name}'.")
            else:
                st.error(f"Venue '{venue_name}' does not exist.")
    except Exception as e:
        st.error(f"An error occurred during booking: {str(e)}")
    finally:
        if connection:
            connection.close()

def find_venue(search_keyword):
    connections = connect_to_db()
    results = []
    try:
        for db_name, connection in connections.items():
            if connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "SELECT Name, City, Capacity, Price_per_hour FROM Venues WHERE Name LIKE %s",
                        ('%' + search_keyword + '%',)
                    )
                    results.extend(cursor.fetchall())
                connection.close()
    except Exception as e:
        st.error(f"An error occurred while searching for venues: {str(e)}")
    if results:
        return pd.DataFrame(results)
    else:
        st.info("No venues found matching the search criteria.")
        return pd.DataFrame()

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

# Streamlit user interface for the application
st.title('EventManager - Venue Booking Management System')

# Using tabs for better organization
tab1, tab2, tab3 = st.tabs(["Add Venue", "Create Booking", "Find Venue"])

with tab1:
    st.header('Add a New Venue')
    venue_name = st.text_input('Venue Name', key='venue_name')
    city = st.text_input('City', key='city')
    capacity = st.number_input('Capacity', min_value=1, value=1, key='capacity')
    price_per_hour = st.number_input('Price Per Hour', min_value=0, format='%d', key='price_per_hour')
    if st.button('Add Venue', key='add_venue'):
        add_venue(venue_name, city, capacity, price_per_hour)  # Assuming add_venue function handles exceptions and messages

with tab2:
    st.header('Create a Booking')

    # Using columns to layout input fields more elegantly
    col1, col2, col3 = st.columns(3)
    with col1:
        client_name = st.text_input('Client Name', key='client_name', help='Enter the full name of the client making the booking.')
    with col2:
        date = st.date_input('Date', key='date', help='Select the date for the booking.')
    with col3:
        venue_name = st.text_input('Venue Name', key='booking_venue_name', help='Enter the name of the venue you want to book.')

    col4, col5 = st.columns([1, 1])
    with col4:
        start_time = st.time_input('Start Time', key='start_time', help='Select the start time for the event.')
    with col5:
        end_time = st.time_input('End Time', key='end_time', help='Select the end time for the event.')

    # Check availability button with a success or error message
    if st.button('Check Availability', key='check_availability'):
        available = check_availability(venue_name, date, start_time, end_time)
        if available:
            st.success('The venue is available for booking. You can now create the booking.')
            # Show create booking button only if the venue is available
            if st.button('Create Booking', key='create_booking'):
                create_booking(client_name, date, start_time, end_time, venue_name)
        else:
            st.error('The venue is not available at the selected time. Please try another time.')

with tab3:
    st.header('Find a Venue')
    search_keyword = st.text_input('Enter search keyword', key='search')
    if st.button('Search Venues', key='search_venues'):
        results = find_venue(search_keyword)
        if not results.empty:
            st.dataframe(results)
        else:
            st.info('No venues found matching the search criteria.')
