# dsci551_project

## File Structure:
- README.md
- requirements.txt
- streamlit_app.py
- Functions
  - add_venue.py
  - create_booking.py
  - create_databases.py
  - create_tables.py
 



## Command Line Usage:

### 1. Login to EC2 Instance and use sftp to transfer put necessary files to EC2. Then,

    Start your MySQL server: sudo service mysql start

### 2. Before calling ```create_tables.py```, make sure to grant all privileges to local host and then flush privileges.
```
GRANT ALL PRIVILEGES ON database_name.* TO 'username'@'hostname';
FLUSH PRIVILEGES;
```
### 3. Use Functions
   
   **Create Tables**: ```python3 create_tables.py```
   
   **Add Venue**: ```python3 add_venue.py 'venue_name' 'city' 'capacity' 'price_per_hour'```
   
   **Create Booking**: ```python3 create_booking.py 'client_name' 'date' 'start_time' 'end_time' 'venue_name'```

   Test by logging into MySQL: ```mysql -u root -p``` and enter password

### 4. Launch Streamlit App

   **Running Streamlit App**: Go to [Streamlit Cloud](https://eventmanager-dsci551-s24.streamlit.app/) or ```streamlit run your_script.py``` on command line.



