import streamlit as st

# Access secrets
mysql_secrets = st.secrets["connections"]["mysql"]

dialect = mysql_secrets["dialect"]
host = mysql_secrets["host"]
port = mysql_secrets["port"]
database = mysql_secrets["database"]
username = mysql_secrets["username"]
password = mysql_secrets["password"]

# Use these variables to set up your database connection