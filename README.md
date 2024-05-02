# dsci551_project

File Structure:

main:
|-- README.md
|-- requirements.txt
|-- streamlit_app.py
|-- Functions
|---- add_venue.py
|---- create_booking.py
|---- create_databases.py
|---- create_tables.py


Before calling ```create_tables.py```, make sure you grant all privileges to local host and then flush privileges.

**Create Tables**: ```python3 create_tables.py```

**Add Venue**: ```python3 add_venue.py 'venue_name' 'city' 'capacity' 'price_per_hour'```

**Create Booking**: ```python3 create_booking.py 'client_name' 'date' 'start_time' 'end_time' 'venue_name'```

**Running Streamlit App**: Go to ```https://eventmanager-dsci551-s24.streamlit.app/``` or ```streamlit run your_script.py```



