from flask import Flask, render_template, request, redirect, session, flash ,url_for
import mysql.connector as myconn
import uuid

app = Flask(__name__, template_folder='templates')

app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Database connection parameters
db_config = {
    "host": "localhost",
    "user": "root",
    "password": "root",
    "database": "petrol"
}

def signup_user(username, password, confirmpassword):
    try:
        connection = myconn.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO user (username, password, confirmpassword) VALUES (%s, %s, %s)", (username, password, confirmpassword))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except myconn.Error as error:
        print("Error while saving user data:", error)
        return False

def signup_admin(username, password, confirmpassword, hyderabad_places):
    try:
        connection = myconn.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO admin (username, password, confirmpassword, hyderabad_places) VALUES (%s, %s, %s, %s)", (username, password, confirmpassword, hyderabad_places))
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except myconn.Error as error:
        print("Error while saving admin data:", error)
        return False

def authenticate_user(username, password):
    try:
        connection = myconn.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM user WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return user is not None
    except myconn.Error as error:
        print("Error while authenticating user:", error)
        return False

def authenticate_admin(username, password):
    try:
        connection = myconn.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM admin WHERE username = %s AND password = %s", (username, password))
        admin = cursor.fetchone()
        cursor.close()
        connection.close()
        return admin is not None
    except myconn.Error as error:
        print("Error while authenticating admin:", error)
        return False

def get_hyderabad_places():
    try:
        connection = myconn.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT hyderabad_places FROM admin")
        places = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return places
    except myconn.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return []

def get_providers_for_place():
    try:
        connection = myconn.connect(**db_config)
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT provider FROM admin")
        providers = [row[0] for row in cursor.fetchall()]
        cursor.close()
        connection.close()
        return providers
    except myconn.Error as e:
        print(f"Error connecting to MySQL: {e}")
        return []

def save_buyer_data(name, phone_number, address, nearby_landmark, admin_place, provider, spd, liters, total_price):
    try:
        connection = myconn.connect(**db_config)
        cursor = connection.cursor()

        # Generate a unique order number
        order_number = str(uuid.uuid4())

        # Insert buyer data into buyers table
        insert_buyer_query = """
            INSERT INTO buyers (order_number, name, phone_number, address, nearby_landmark, admin_place, provider, spd, liters, total_price, status, username)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        buyer_data = (order_number, name, phone_number, address, nearby_landmark, admin_place, provider, spd, liters, total_price, 'Ordered', session['username'])
        cursor.execute(insert_buyer_query, buyer_data)

        # Insert the same order into previous_orders table
        insert_previous_query = """
            INSERT INTO previous_orders 
            (order_number, name, phone_number, address, nearby_landmark, admin_place, provider, spd, liters, total_price, status, username) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        previous_data = (order_number, name, phone_number, address, nearby_landmark, admin_place, provider, spd, liters, total_price, 'Ordered', session['username'])
        cursor.execute(insert_previous_query, previous_data)

        connection.commit()  # Commit changes to the database
        cursor.close()
        connection.close()
        
        return order_number  # Return the generated order number if successful

    except myconn.Error as error:
        print("Error while saving buyer data:", error)
        return None  # Return None to indicate failure
    except KeyError as key_error:
        print("Session username not found:", key_error)
        return None  # Handle missing session username gracefully
    except Exception as ex:
        print("Unexpected error:", ex)
        return None  # Handle any unexpected errors




def update_previous_order_status(order_number, new_status, username):
    try:
        connection = myconn.connect(**db_config)
        cursor = connection.cursor()

        # Update the status of the order in the previous_orders table
        update_query = "UPDATE previous_orders SET status = %s WHERE order_number = %s AND username = %s"
        update_params = (new_status, order_number, username)
        cursor.execute(update_query, update_params)

        connection.commit()  # Commit changes to the database
        cursor.close()
        connection.close()
        return True
    except myconn.Error as error:
        print("Error while updating previous order status:", error)
        return False





def update_order_status(order_number, new_status):
    try:
        connection = myconn.connect(**db_config)
        cursor = connection.cursor()

        cursor.execute(
            "UPDATE buyers SET status = %s WHERE order_number = %s",
            (new_status, order_number)
        )
        connection.commit()

        cursor.close()
        connection.close()
        return True
    except myconn.Error as error:
        print("Error while updating order status:", error)
        return False

@app.route('/home', methods=['GET'])
def home():
    return render_template('home.html')

@app.route('/admin', methods=['GET'])
def admin():
    if 'logged_in' in session and session.get('user_type') == 'admin':
        username = session.get('username')
        search_query = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'asc')
        
        try:
            connection = myconn.connect(**db_config)
            cursor = connection.cursor()

            # Find the admin's details
            cursor.execute("SELECT hyderabad_places FROM admin WHERE username = %s", (username,))
            admin_data = cursor.fetchone()
            admin_place = admin_data[0]

            # Base query
            query = "SELECT order_number, name, phone_number, address, nearby_landmark, admin_place, provider, spd, liters, total_price, status, created_at FROM buyers WHERE admin_place = %s"
            params = [admin_place]

            # Modify query for search
            if search_query:
                query += " AND (name LIKE %s OR order_number LIKE %s)"
                search_param = f"%{search_query}%"
                params.extend([search_param, search_param])

            # Add sorting
            if sort_by == 'asc':
                query += " ORDER BY created_at ASC"
            else:
                query += " ORDER BY created_at DESC"

            cursor.execute(query, tuple(params))
            buyers = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return render_template('admin.html', buyers=buyers, search_query=search_query, sort_by=sort_by)
        except myconn.Error as error:
            print("Error while fetching buyers data:", error)
            return redirect('/admin')
    else:
        return redirect('/login')

    

@app.route('/services', methods=['GET', 'POST'])
def services():
    if request.method == 'POST':
        if 'username' not in session:
            flash("Please login first to order petrol/diesel", "error")
            return redirect('/login')

        name = request.form['name']
        phone_number = request.form['phone_number']
        address = request.form['address']
        nearby_landmark = request.form['nearby_landmark']
        admin_place = request.form['admin_place']
        provider = request.form['provider']
        spd = request.form['spd']  # Get the selected petrol/diesel
        liters = request.form['liters']  # Get selected amount of petrol/diesel

        # Calculate price based on liters and fuel type
        if spd.lower() == 'petrol':
            price_per_liter = 120  # Price per liter for petrol
        elif spd.lower() == 'diesel':
            price_per_liter = 100  # Price per liter for diesel
        else:
            flash("Invalid fuel type selected.", "error")
            return redirect('/services')

        total_price = int(liters) * price_per_liter

        order_number = save_buyer_data(name, phone_number, address, nearby_landmark, admin_place, provider, spd, liters, total_price)
        if order_number:
            return render_template('success.html', total_price=total_price, order_number=order_number)
        else:
            flash("Error in placing the order. Please try again.", "error")
            return redirect('/services')

    hyderabad_places = get_hyderabad_places()
    providers = get_providers_for_place()
    return render_template('services.html', hyderabad_places=hyderabad_places, providers=providers)




@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirmpassword = request.form['confirmpassword']
        hyderabad_places = request.form.get('hyderabad_places')
        user_type = request.form['user_type']
        
        if password != confirmpassword:
            return render_template("signup.html", error="Passwords do not match.")
        
        if user_type == 'user':
            if signup_user(username, password, confirmpassword):
                session['username'] = username
                session['user_type'] = 'user'
                session['logged_in'] = True
                return redirect('/login')
            else:
                return render_template("signup.html", error="Failed to save user data.")
        elif user_type == 'admin':
            if signup_admin(username, password, confirmpassword, hyderabad_places):
                session['username'] = username
                session['user_type'] = 'admin'
                session['logged_in'] = True
                return redirect('/login')
            else:
                return render_template("signup.html", error="Failed to save admin data or username exists.")
        
        return render_template("signup.html", error="Failed to save data. Please try again later.")
    
    return render_template("signup.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_type = request.form['user_type']
        
        if user_type == 'user' and authenticate_user(username, password):
            session['username'] = username
            session['user_type'] = 'user'
            session['logged_in'] = True
            return redirect('/home')
        elif user_type == 'admin' and authenticate_admin(username, password):
            session['username'] = username
            session['user_type'] = 'admin'
            session['logged_in'] = True
            return redirect('/admin')
        else:
            return render_template("login.html", error="Invalid username, password, or user type.")
    
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/success')
def success():
    return redirect('/success')


@app.route('/check_status', methods=['GET', 'POST'])
def check_status():
    if request.method == 'POST':
        order_number = request.form['order_number']
        name = request.form['name']
        

        try:
            connection = myconn.connect(**db_config)
            cursor = connection.cursor()

            # Fetch order details based on name, phone number, and provider
            cursor.execute(
                "SELECT * FROM buyers WHERE order_number = %s AND name = %s",
                (order_number, name)
            )
            orders = cursor.fetchall()

            cursor.close()
            connection.close()

            return render_template('status.html', orders=orders)
        except myconn.Error as error:
            print("Error while fetching order status:", error)
            return redirect('/check_status')
    
    return render_template('check_status.html')

@app.route('/update_status', methods=['POST'])
def update_status():
    if 'logged_in' in session and session.get('user_type') == 'admin':
        try:
            order_number = request.form['order_number']
            new_status = request.form['new_status']

            if update_order_status(order_number, new_status):
                flash("Order status updated successfully!", "success")
            else:
                flash("Failed to update order status. Please try again later.", "error")

            return redirect('/admin')  # Redirect to admin page after update
        except Exception as e:
            flash(f"Error updating order status: {str(e)}", "error")
            return redirect('/admin')  # Redirect to admin page on error
    else:
        return redirect('/login')  # Redirect to login if not logged in as admin





@app.route('/previous_orders', methods=['GET'])
def previous_orders():
    if 'logged_in' in session and session.get('user_type') == 'user':
        username = session.get('username')
        search_query = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'asc')

        print(f"User: {username}, Search: {search_query}, Sort: {sort_by}")  # Debugging line
        
        try:
            connection = myconn.connect(**db_config)
            cursor = connection.cursor()
            
            query = "SELECT * FROM previous_orders WHERE username = %s"
            params = [username]

            # Modify query for search
            if search_query:
                query += " AND (name LIKE %s OR order_number LIKE %s)"
                search_param = f"%{search_query}%"
                params.extend([search_param, search_param])

            # Add sorting
            if sort_by == 'asc':
                query += " ORDER BY order_date ASC"
            else:
                query += " ORDER BY order_date DESC"

            print(f"Executing query: {query} with params: {params}")  # Debugging line
            cursor.execute(query, tuple(params))
            orders = cursor.fetchall()
            
            print(f"Fetched orders: {orders}")  # Debugging line
            cursor.close()
            connection.close()
            return render_template('user_orders.html', orders=orders)
        except myconn.Error as error:
            print(f"Error while fetching user orders: {error}")  # Debugging line
            if cursor:
                cursor.close()
            if connection:
                connection.close()
            return redirect('/login')
    else:
        print("User not logged in or not a user.")  # Debugging line
        return redirect('/login')

    

@app.route('/contact_support', methods=['GET', 'POST'])
def contact_support():
    if request.method == 'POST':
        if 'order_number' in request.form:
            order_number = request.form['order_number']
            name = request.form['name']
            return redirect(url_for('check_status', order_number=order_number, name=name))
        elif 'support_name' in request.form:
            if 'logged_in' in session and session['logged_in']:
                support_name = request.form['support_name']
                email = request.form['email']
                problem = request.form['problem']
                # Handle the problem submission, e.g., save to the database or send an email
                flash('Your problem has been submitted successfully.', 'success')
                return redirect('/contact_support')
            else:
                flash('You need to log in to submit a problem.', 'danger')
                return redirect(url_for('login'))
    return render_template('contact_support.html')




@app.route('/submit_problem', methods=['POST'])
def submit_problem():
    # Check if the user is logged in
    if 'logged_in' not in session or not session['logged_in']:
        flash('You need to log in to submit a problem.', 'danger')
        return redirect(url_for('login'))  # Redirect to login page if not logged in

    # Proceed with problem submission if logged in
    support_name = request.form['support_name']
    email = request.form['email']
    problem = request.form['problem']

    try:
        connection = myconn.connect(**db_config)
        cursor = connection.cursor()

        # Insert the problem data into the problems table
        cursor.execute(
            "INSERT INTO problems (support_name, email, problem) VALUES (%s, %s, %s)",
            (support_name, email, problem)
        )

        connection.commit()
        cursor.close()
        connection.close()

        flash('Your problem has been submitted successfully.', 'success')
    except myconn.Error as error:
        print("Error while saving the problem:", error)
        flash('There was an issue submitting your problem. Please try again later.', 'danger')

    return redirect('/contact_support')




@app.route('/admin_contact', methods=['GET'])
def admin_contact():
    return render_template('admin_contact.html')

@app.route('/submit_problem_admin', methods=['GET', 'POST'])
def submit_problem_admin():
    support_name = request.form['support_name']
    email = request.form['email']
    problem = request.form['problem']

    try:
        connection = myconn.connect(**db_config)
        cursor = connection.cursor()

        # Insert the problem data into the problems table
        cursor.execute(
            "INSERT INTO admin_problems (support_name, email, problem) VALUES (%s, %s, %s)",
            (support_name, email, problem)
        )

        connection.commit()
        cursor.close()
        connection.close()

        flash('Your problem has been submitted successfully.', 'success')
    except myconn.Error as error:
        print("Error while saving the problem:", error)
        flash('There was an issue submitting your problem. Please try again later.', 'danger')

    return redirect('/admin_contact')



@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html')
@app.route('/admin_faq', methods=['GET'])
def admin_faq():
    return render_template('admin_faq.html')

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html')
@app.route('/admin_about', methods=['GET'])
def admin_about():
    return render_template('admin_about.html')

if __name__ == '__main__':
    app.run(debug=True)