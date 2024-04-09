import sys
import pymysql
from pymysql.err import OperationalError
import hashlib
from datetime import datetime, time, timedelta

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


# Generic hash function to choose the database based on any string input
def choose_database(input_string):
    hash_object = hashlib.sha256(input_string.encode())
    hash_digest = hash_object.hexdigest()
    if int(hash_digest, 16) % 2 == 0:
        return EventManager1_Connection_Params
    else:
        return EventManager2_Connection_Params


def list_booking_times(venue_name, input_date):
    connection_params = choose_database(venue_name)
    try:
        connection = pymysql.connect(**connection_params, cursorclass=pymysql.cursors.DictCursor)
        with connection.cursor() as cursor:
            cursor.execute("SELECT ID FROM Venues WHERE Name = %s", (venue_name,))
            venue_result = cursor.fetchone()

            if venue_result:
                venue_id = venue_result['ID']
                cursor.execute("""
                SELECT b.Start_time, b.End_time FROM Bookings b
                JOIN VenueUsed vu ON b.ID = vu.BookingID
                WHERE vu.VenueID = %s AND b.Date = %s
                ORDER BY b.Start_time ASC
                """, (venue_id, input_date))

                bookings = cursor.fetchall()

                if bookings:
                    print(f"Bookings for {venue_name} on {input_date}:")
                    for booking in bookings:
                        # Directly outputting SQL results
                        print(f"Start: {booking['Start_time']}, End: {booking['End_time']}")
                else:
                    print(f"No bookings found for {venue_name} on {input_date}.")
            else:
                print(f"Venue '{venue_name}' does not exist.")
    except OperationalError as e:
        print(f"An error occurred: {e}")
    finally:
        if connection:
            connection.close()

if __name__ == "__main__":
    if len(sys.argv) == 3:
        venue_name = sys.argv[1]
        input_date = sys.argv[2]
        try:
            datetime.strptime(input_date, "%Y-%m-%d")  # Validate the input date format
            list_booking_times(venue_name, input_date)
        except ValueError as e:
            print(f"Error: Invalid date format. Please use YYYY-MM-DD. {e}")
    else:
        print("Usage: python3 script_name.py 'venue_name' 'YYYY-MM-DD'")
