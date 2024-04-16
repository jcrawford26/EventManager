# IMPORT LIBRARIES
import sys
import pymysql
from pymysql.err import OperationalError
import hashlib

# Replace the placeholders with the actual database connection details
EventManager1_Connection_Params = {
    'host': 'localhost',
    'user': 'dsci551',
    'password': 'Dsci-551',
    'database': 'Event_Manager1'
}

EventManager2_Connection_Params = {
    'host': 'localhost',
    'user': 'dsci551',
    'password': 'Dsci-551',
    'database': 'Event_Manager2'
}

# List of connection parameters for easy iteration
connections_params = [EventManager1_Connection_Params, EventManager2_Connection_Params]


# Generic hash function to choose the database based on any string input
def choose_database(input_string):
    # Create a hash of the input string
    hash_object = hashlib.sha256(input_string.encode())
    hash_digest = hash_object.hexdigest()
    # Determine the target database using the hash value
    if int(hash_digest, 16) % 2 == 0:
        return EventManager1_Connection_Params
    else:
        return EventManager2_Connection_Params


def create_booking(client_name, date, start_time, end_time, venue_name):
    # Determine the database to use based on the venue name
    connection_params = choose_database(venue_name)

    try:
        # Connect to the database
        connection = pymysql.connect(host=connection_params['host'],
                                     user=connection_params['user'],
                                     password=connection_params['password'],
                                     database=connection_params['database'],
                                     cursorclass=pymysql.cursors.DictCursor)

        with connection.cursor() as cursor:
            # Check if the venue exists
            cursor.execute("SELECT ID FROM Venues WHERE Name = %s", (venue_name,))
            venue_result = cursor.fetchone()

            if venue_result:
                venue_id = venue_result['ID']

                # Check for overlapping bookings
                cursor.execute("""
                SELECT b.* FROM Bookings b
                JOIN VenueUsed vu ON b.ID = vu.BookingID
                WHERE vu.VenueID = %s AND b.Date = %s
                AND (
                    (b.Start_time < %s AND b.End_time > %s)
                    OR (b.Start_time < %s AND b.End_time > %s)
                    OR (b.Start_time >= %s AND b.End_time <= %s)
                )
                """, (venue_id, date, start_time, end_time, end_time, start_time, start_time, end_time))

                if cursor.fetchone():
                    # An overlapping booking exists
                    print(f"Venue '{venue_name}' is already booked for the requested time.")
                else:
                    # Proceed with booking
                    cursor.execute(
                        "INSERT INTO Bookings (Client_name, Date, Start_time, End_time) VALUES (%s, %s, %s, %s)",
                        (client_name, date, start_time, end_time))
                    booking_id = cursor.lastrowid

                    # Link the booking to the venue
                    cursor.execute("INSERT INTO VenueUsed (VenueID, BookingID) VALUES (%s, %s)", (venue_id, booking_id))
                    connection.commit()
                    print(f"Booking for '{client_name}' added successfully and linked to venue '{venue_name}'.")
            else:
                print(f"Venue '{venue_name}' does not exist.")

    except pymysql.err.OperationalError as e:
        print(f"An error occurred: {e}")
    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    if len(sys.argv) == 6:
        # Extracting command line arguments
        client_name, date, start_time, end_time, venue_name = sys.argv[1:5]
        venue_name = ' '.join(sys.argv[5:])
        # Call the create_booking function with the provided arguments
        create_booking(client_name, date, start_time, end_time, venue_name)
    else:
        print("Usage: python3 create_booking.py 'client_name' 'date' 'start_time' 'end_time' 'venue_name'")

