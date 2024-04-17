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

def create_booking_tab():
    st.header('Create a Booking')

    # Date selection at the top
    date = st.date_input('Date', key='date_book', min_value=datetime.today(), max_value=datetime.today() + timedelta(days=60))

    # Generating time options from 1 PM to 11 PM
    time_options = [datetime.strptime(f"{hour}:00 PM", "%I:%M %p").time() for hour in range(1, 12)]
    
    # Setting default start and end times based on typical business logic
    default_start_index = time_options.index(datetime.strptime("01:00 PM", "%I:%M %p").time())
    default_end_index = time_options.index(datetime.strptime("02:00 PM", "%I:%M %p").time())

    # Selectboxes for start and end times
    start_time = st.selectbox('Start Time', time_options, index=default_start_index, format_func=lambda x: x.strftime('%I:%M %p'), key='start_time_book')
    end_time = st.selectbox('End Time', time_options, index=default_end_index, format_func=lambda x: x.strftime('%I:%M %p'), key='end_time_book')

    # Ensure start time is before end time
    if start_time >= end_time:
        st.error('End time must be later than start time.')
        return  # Early return to prevent further processing

    # Venue selection from a dropdown list of available venues
    all_venues = get_all_venues()  # Fetch the list of venues from your function
    venue_name = st.selectbox('Select a Venue', all_venues, key='venue_select_book')

    # Check venue availability
    if st.button('Check Availability'):
        formatted_start_time = start_time.strftime('%H:%M:%S')
        formatted_end_time = end_time.strftime('%H:%M:%S')
        available = check_availability(venue_name, date, formatted_start_time, formatted_end_time)
        if available:
            st.success('The venue is available for booking.')
            hourly_rate = get_venue_hourly_rate(venue_name)  # Fetch the hourly rate
            hours_diff = (end_time.hour - start_time.hour) + ((end_time.minute - start_time.minute) / 60)
            total_cost = float(hourly_rate) * hours_diff
            st.session_state['booking_details'] = (venue_name, date, formatted_start_time, formatted_end_time, total_cost)
            st.session_state['create_enabled'] = True
            st.write(f"Estimated total cost: ${total_cost:.2f}")
        else:
            st.error('The venue is not available at the selected time. Please try another time.')
            st.session_state['create_enabled'] = False

    # Proceed to confirm booking if available
    if st.session_state.get('create_enabled', False):
        client_name = st.text_input('Client Name', key='client_name_book')
        if st.button('Confirm Booking'):
            venue_name, date, formatted_start_time, formatted_end_time, total_cost = st.session_state['booking_details']
            # st.write(f"Debug: Venue Name - '{venue_name}'")  # Debug print to check the actual venue name being used
            create_booking(client_name, date, formatted_start_time, formatted_end_time, venue_name)
            st.write(f"The total cost of the booking was: ${total_cost:.2f}")
            del st.session_state['create_enabled']
            del st.session_state['booking_details']

def fetch_crm_data():
    connections = connect_to_db()  # This should return a dictionary of connections for all databases
    results = []
    try:
        for db_name, connection in connections.items():
            if connection:
                with connection.cursor(pymysql.cursors.DictCursor) as cursor:
                    cursor.execute("""
                        SELECT 
                            b.Client_name AS Name,
                            COUNT(*) AS Booking_Count,
                            SUM(v.Price_per_hour * TIMESTAMPDIFF(HOUR, b.Start_time, b.End_time)) AS Total_Spend,
                            (SELECT v2.Name FROM Venues v2 
                             JOIN VenueUsed vu ON v2.ID = vu.VenueID
                             JOIN Bookings b2 ON vu.BookingID = b2.ID
                             WHERE b2.Client_name = b.Client_name
                             GROUP BY v2.Name
                             ORDER BY COUNT(*) DESC
                             LIMIT 1) AS Most_Frequent_Venue
                        FROM 
                            Bookings b
                        JOIN 
                            VenueUsed vu ON b.ID = vu.BookingID
                        JOIN 
                            Venues v ON vu.VenueID = v.ID
                        GROUP BY 
                            b.Client_name
                    """)
                    results.extend(cursor.fetchall())
    except Exception as e:
        st.error(f"Failed to fetch CRM data across databases: {str(e)}")
    finally:
        for connection in connections.values():
            if connection:
                connection.close()

    if results:
        return pd.DataFrame(results)
    else:
        return pd.DataFrame()  # Return an empty DataFrame if there are issues or no data


def mass_add_venues(venues):
    """
    Accepts a list of dictionaries, each representing a venue with keys:
    'venue_name', 'city', 'capacity', 'price_per_hour'
    """
    # Group venues by target database based on the hash of the venue_name
    db_venues = {'EventManager1': [], 'EventManager2': []}
    for venue in venues:
        db_name = choose_database(venue['venue_name'])
        db_venues[db_name].append(venue)

    # Connect to each database and perform the inserts
    results = {}
    for db_name, venues_list in db_venues.items():
        if venues_list:  # Only connect if there are venues to add
            connection = connect_to_db(db_name)
            try:
                with connection.cursor() as cursor:
                    # Prepare batch insert query
                    insert_query = "INSERT INTO Venues (Name, City, Capacity, Price_per_hour) VALUES (%s, %s, %s, %s)"
                    # Prepare values to be inserted
                    insert_values = [(v['venue_name'], v['city'], v['capacity'], v['price_per_hour']) for v in venues_list]
                    # Execute the batch insertion
                    cursor.executemany(insert_query, insert_values)
                    connection.commit()
                    results[db_name] = f"{len(venues_list)} venues added successfully to {db_name}."
            except Exception as e:
                results[db_name] = f"Failed to add venues to {db_name}: {str(e)}"
            finally:
                if connection:
                    connection.close()


# Streamlit user interface for the application
st.title('EventManager - Venue Booking Management System')

# Using tabs for better organization
tab1, tab2, tab3 = st.tabs(["Find Venue", "Create Booking", "Admin"])

# find venue
with tab1:
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

# Admin tab in Streamlit
with tab3:
    st.header('Add a venue')
    
    # Venue adding form under Admin
    with st.form("form_add_venue"):
        venue_name = st.text_input('Venue Name', key='venue_add')
        city = st.text_input('City', key='city_add')
        capacity = st.number_input('Capacity', min_value=1, key='capacity_add')
        price_per_hour = st.number_input('Price Per Hour', min_value=0, key='price_add')
        submit_button = st.form_submit_button('Add Venue')

        if submit_button:
            add_venue(venue_name, city, capacity, price_per_hour)

    # Additional administrative functionalities here
