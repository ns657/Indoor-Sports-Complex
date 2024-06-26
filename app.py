import mysql.connector
import streamlit as st
import datetime

# Establishing connection with the MySQL database
try:
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        password="mysql@123",
        database="ISC"
    )
    mycursor = mydb.cursor()
except mysql.connector.Error as e:
    st.error(f"Error connecting to MySQL database: {e}")
    st.stop()

# Session state management
class SessionState:
    def _init_(self, **kwargs):
        self._dict_.update(kwargs)

def get():
    if not hasattr(st, 'session_state'):
        st.session_state = SessionState()
    return st.session_state

# Supervisor Login Function
def supervisor_login():
    if not st.session_state.logged_in:
        st.subheader("Supervisor Login")
        email = st.text_input("Enter Email")
        password = st.text_input("Enter Password", type="password")

        if st.button("Login"):
            try:
                # Autheticate supervisor credentials with the database
                sql = "SELECT * FROM supervisor WHERE email = %s AND password = %s"
                val = (email, password)
                mycursor.execute(sql, val)
                result = mycursor.fetchone()

                if result:
                    st.success("Login Successful!")
                    st.session_state.logged_in = True
                    supervisor_portal()
                else:
                    st.error("Invalid Credentials. Please try again.")

            except mysql.connector.Error as e:
                st.error(f"Error during login: {e}")
    else:
        supervisor_portal()

# Function to navigate to supervisor portal
def supervisor_portal():
    st.title("Supervisor Portal")
    option = st.sidebar.selectbox("What do you have in mind?", ("Manage Booking Requests", "View Bookings", "Manage Blacklist"))
    if option == "Manage Booking Requests":
        manage_booking_requests()  # Implement manage_booking_requests function
    elif option == "View Bookings":
        supervisor_view()  # Implement supervisor_view function
    elif option == "Manage Blacklist":
        manage_blacklist()  # Implement manage_blacklist function
        
# Function to manage booking requests by supervisor
def manage_booking_requests():
    st.subheader("Manage Booking Requests")
    mycursor.callproc('get_pending_bookings')
    bookings = next(mycursor.stored_results()).fetchall()

    for booking in bookings:
        with st.expander(f"Booking ID {booking[0]} - Date: {booking[2]}, Time: {booking[3]}"):
            st.write(f"Room ID: {booking[1]}")
            st.write(f"Student ID: {booking[4]}")
            st.write(f"Current Status: {booking[5]}")
            new_status = st.selectbox("Update Status", ["Accepted", "Denied"], key=f"status_{booking[0]}")
            if st.button("Update", key=f"update_{booking[0]}"):
                update_status(booking[0], new_status)

# Function to update booking request status
def update_status(booking_id, new_status):
    mycursor.callproc('update_booking_request', [booking_id, new_status])
    mydb.commit()
    st.success(f"Booking ID {booking_id} status updated to {new_status}")

#Function to display all approved/denied bookings for supervisor
def supervisor_view():
    st.subheader("View Bookings")

    # Fetching accepted and denied bookings
    query = """
    SELECT id, room_id, booked_date, booked_time, student_id, status 
    FROM booking 
    WHERE status IN ('Accepted', 'Denied')
    ORDER BY status DESC, booked_date ASC, booked_time ASC
    """
    mycursor.execute(query)
    bookings = mycursor.fetchall()

    if not bookings:
        st.write("There are no accepted or denied bookings to display.")
        return

    # Displaying bookings grouped by status
    current_status = None
    for booking in bookings:
        if booking[5] != current_status:
            if current_status is not None:
                st.markdown("---")
            st.subheader(f"{booking[5]} Bookings")
            current_status = booking[5]

        with st.expander(f"Booking ID {booking[0]} - Date: {booking[2]}, Time: {booking[3]}"):
            st.text(f"Room ID: {booking[1]}")
            st.text(f"Student ID: {booking[4]}")
            st.text(f"Status: {booking[5]}")

#Function to manage blacklisted students
def manage_blacklist():
    st.subheader("Manage Student Blacklist")

    # Form to add a student to the blacklist
    with st.form("blacklist_form"):
        bl_roll_no = st.text_input("Enter Student Roll Number to blacklist")
        bl_reason = st.text_area("Reason for blacklisting")
        submit_bl = st.form_submit_button("Blacklist Student")
    
    if submit_bl:
        if bl_roll_no and bl_reason:
            try:
                sql = "INSERT INTO blacklist (roll_no, reason) VALUES (%s, %s)"
                mycursor.execute(sql, (bl_roll_no, bl_reason))
                mydb.commit()
                st.success("Student blacklisted successfully.")
            except mysql.connector.Error as e:
                st.error(f"Error blacklisting student: {e}")

    # Option to unblacklist a student
    with st.form("unblacklist_form"):
        ub_roll_no = st.text_input("Enter Student Roll Number to unblacklist")
        submit_ub = st.form_submit_button("Unblacklist Student")

    if submit_ub:
        if ub_roll_no:
            try:
                sql = "DELETE FROM blacklist WHERE roll_no = %s"
                mycursor.execute(sql, (ub_roll_no,))
                mydb.commit()
                if mycursor.rowcount > 0:
                    st.success("Student unblacklisted successfully.")
                else:
                    st.error("No such student found in blacklist.")
            except mysql.connector.Error as e:
                st.error(f"Error unblacklisting student: {e}")

    # Viewing all blacklisted students
    st.subheader("Current Blacklist")
    try:
        mycursor.execute("SELECT roll_no, reason, timestamp FROM blacklist")
        results = mycursor.fetchall()
        if results:
            for result in results:
                st.write(f"Roll No: {result[0]}, Reason: {result[1]}, Timestamp: {result[2]}")
        else:
            st.write("No students are currently blacklisted.")
    except mysql.connector.Error as e:
        st.error(f"Error retrieving blacklist: {e}")

def create_booking():
    st.subheader("Create Booking")
    room_type = st.selectbox("Select Room Type", ["Badminton Court", "Yoga Room", "Basketball Court", "Gym"])
    booking_date = st.date_input("Select Booking Date")

    # Define the time range from 6 am to 7 pm and create a list of 1-hour time slots
    start_time = datetime.time(6, 0)
    end_time = datetime.time(19, 0) 
    time_slots = []

    current_time = datetime.datetime.combine(booking_date, start_time)
    end_datetime = datetime.datetime.combine(booking_date, end_time)

    while current_time <= end_datetime:
        time_slots.append(current_time.time())
        current_time += datetime.timedelta(hours=1)

    booking_time = st.selectbox("Select Booking Time", time_slots)

    if st.button("Book"):
        if not st.session_state.logged_in:
            st.error("Please login to book slots.")
            return  # Exit the function if not logged in
        
        student_id = st.session_state.student_id

        try:
            # Check for existing booking clash
            clash_sql = """
            SELECT COUNT(*) FROM booking 
            WHERE student_id = %s AND booked_date = %s AND booked_time = %s
            """
            mycursor.execute(clash_sql, (student_id, booking_date, booking_time))
            clash_count = mycursor.fetchone()[0]

            if clash_count > 0:
                st.error("You already have a booking at this time. Please choose a different time.")
                return

            # Call the stored procedure to search for available rooms
            mycursor.callproc("search_room", (room_type, booking_date, booking_time))
            results = mycursor.stored_results()
            if results:
                result = next(results)
                rows = result.fetchall() 
                if rows:
                    room_id = rows[0][0]  # Get the first available room
                    # Insert the booking details into the 'booking' table
                    sql = "INSERT INTO booking (room_id, booked_date, booked_time, student_id) VALUES (%s, %s, %s, %s)"
                    val = (room_id, booking_date, booking_time, student_id)
                    mycursor.execute(sql, val)
                    mydb.commit()
                    st.success("Booking Successful! See you at ISC!")
                else:
                    st.error("No available rooms.")
            else:
                st.error("No results returned from the stored procedure.")
        except mysql.connector.Error as e:
            st.error(f"Error creating booking: {e}")
# Function to view bookings
def view_bookings():
    if not st.session_state.logged_in:
        st.error("Please login to view your bookings.")
        return

    st.subheader("Your Bookings")
    student_id = st.session_state.student_id
    try:
        sql = """
        SELECT b.id, s.Type, b.booked_date, b.booked_time, b.status
        FROM booking b
        JOIN sport s ON b.room_id = s.id
        WHERE b.student_id = %s
        ORDER BY b.booked_date DESC, b.booked_time DESC;
        """
        mycursor.execute(sql, (student_id,))
        results = mycursor.fetchall()

        if results:
            for result in results:
                st.write(f"Booking ID: {result[0]}, Room Type: {result[1]}, Date: {result[2]}, Time: {result[3]}, Status: {result[4]}")
        else:
            st.write("You have no bookings.")
    except mysql.connector.Error as e:
        st.error(f"Database error: {e}")

# Function to delete bookings
def delete_booking():
    if not st.session_state.logged_in:
        st.error("Please login to delete bookings.")
        return

    st.subheader("Delete Booking")
    student_id = st.session_state.student_id
    try:
        sql = "SELECT id, CONCAT('ID: ', id, ', Date: ', booked_date, ', Time: ', booked_time) AS label FROM booking WHERE student_id = %s"
        mycursor.execute(sql, (student_id,))
        bookings = mycursor.fetchall()

        if bookings:
            booking_labels = [booking[1] for booking in bookings]
            booking_to_delete = st.selectbox("Which booking do you want to delete?", booking_labels)

            if st.button("Delete"):
                booking_id = next(booking[0] for booking in bookings if booking[1] == booking_to_delete)
                delete_sql = "DELETE FROM booking WHERE id = %s"
                delete_val = (booking_id,)
                mycursor.execute(delete_sql, delete_val)
                mydb.commit()
                st.success("Booking deleted successfully.")
                st.experimental_rerun()
        else:
            st.write("You don't have any bookings to delete")
    except mysql.connector.Error as e:
        st.error(f"Database error: {e}")

# Function for student login
def student_login():
    if not st.session_state.logged_in:
        st.subheader("Student Login")
        name = st.text_input("Enter Name")
        roll_number = st.text_input("Enter Roll Number", max_chars=10)
        email = st.text_input("Enter Email")
        password = st.text_input("Enter Password", type="password")

        if st.button("Login"):
            try:
                # Autheticate student credentials with the database
                sql = "SELECT * FROM student WHERE Name = %s AND roll_no = %s AND Email = %s AND password = %s"
                val = (name, roll_number, email, password)
                mycursor.execute(sql, val)
                result = mycursor.fetchone()

                if result:
                    st.success("Login Successful!")
                    st.session_state.logged_in = True
                    st.session_state.student_id = result[0]
                    student_portal()
                else:
                    st.error("Invalid Credentials. Please try again.")

            except mysql.connector.Error as e:
                st.error(f"Error during login: {e}")
    else:
        student_portal()
        
# Function to navigate to student portal
def student_portal():
    st.title("Student Portal")
    option = st.sidebar.selectbox("What do you have in mind?", ("Create Booking", "Your Bookings", "Delete Booking"))
    if option == "Create Booking":
        create_booking()
    elif option == "Your Bookings":
        view_bookings()
    elif option == "Delete Booking":
        delete_booking()
    
# Main function
def main():
    st.title("Indoor Sports Complex")

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if 'student_id' not in st.session_state:
        st.session_state.student_id = None
                
    user_type = st.sidebar.selectbox("Who are you?", ("Student", "Supervisor"))
    
    if user_type == "Student":
        student_login()   # Implement student_login function
    elif user_type == "Supervisor":
        supervisor_login()  # Implement supervisor_login function

if __name__ == "__main__":
    main()
