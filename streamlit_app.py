import streamlit as st

# Ensure this function is defined in your streamlit_app.py
def connect_to_db():
    db_info = st.secrets["connections"]["mysql"]
    return pymysql.connect(
        host=db_info["host"],
        user=db_info["username"],
        password=db_info["password"],
        database=db_info["database"],
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# This function depends on the above connect_to_db function
def fetch_data():
    connection = connect_to_db()
    with connection.cursor() as cursor:
        query = "SELECT * FROM your_table_name"  # Replace with your actual table name
        cursor.execute(query)
        result = cursor.fetchall()
    connection.close()
    return pd.DataFrame(result)

# Displaying data in the Streamlit app
if st.button('Show Data'):
    st.write('Fetching data from database...')
    data_df = fetch_data()
    if not data_df.empty:
        st.write(data_df)
    else:
        st.write("No data found.")

