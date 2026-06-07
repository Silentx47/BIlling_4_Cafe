from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import bcrypt
from flask import send_from_directory


app = Flask(__name__)
app.secret_key = 'cafe_secret_key_123'

# MySQL config — update these with your details
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'   # ← must be root
app.config['MYSQL_PASSWORD'] = ''   # ← leave empty if no password
app.config['MYSQL_DB'] = 'cafe_db'

mysql = MySQL(app)

@app.route('/coffee-shop.jpg')
def background():
    return send_from_directory('.', 'coffee-shop.jpg')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.checkpw(password, user[2].encode('utf-8')):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'Pending'")
    active_orders = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM inventory")
    inventory_items = cur.fetchone()[0]
     
    cur.execute("SELECT COUNT(*) FROM inventory WHERE quantity < 5")
    low_stock = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM orders WHERE status = 'Done'")
    completed_orders = cur.fetchone()[0]

    cur.execute("""SELECT item_name, category, quantity, unit FROM inventory""")
    inventory = cur.fetchall()

    cur.execute("""SELECT id, customer_name, total, status FROM orders""")
    orders_list = cur.fetchall()

    cur.execute("""SELECT id, product_name, price FROM products""")
    products = cur.fetchall()

    cur.execute("""SELECT product_name,quantity,total,payment_method,created_at FROM sales ORDER BY created_at DESC""")
    sales_list = cur.fetchall()

    cur.execute("""SELECT IFNULL(SUM(total), 0) FROM sales""")
    total_revenue = cur.fetchone()[0]

    cur.execute("""SELECT COUNT(*) FROM sales""")
    transactions = cur.fetchone()[0]

    cur.execute("""
    SELECT product_name,SUM(quantity) AS sold FROM sales WHERE product_name IS NOT NULL GROUP BY product_name ORDER BY sold DESC LIMIT 1""")
    top_product = cur.fetchone()

    if top_product:
        top_product = top_product[0]
    else:
        top_product = "N/A"
    cur.execute("""SELECT payment_method,COUNT(*) AS count FROM sales WHERE payment_method IS NOT NULL GROUP BY payment_method ORDER BY count DESC LIMIT 1""")
    payment = cur.fetchone()

    if payment:
        payment = payment[0]
    else:
        payment = "N/A"
    
    cur.execute("""
    SELECT product_name,
           SUM(quantity) AS sold

    FROM sales

    WHERE product_name IS NOT NULL

    GROUP BY product_name

    ORDER BY sold DESC

    LIMIT 1
""")

    top_item = cur.fetchone()

    if top_item:
            top_item_name = top_item[0]
            top_item_count = top_item[1]
    else:
            top_item_name = "N/A"
            top_item_count = 0
    cur.execute("""
    SELECT payment_method,
           COUNT(*) AS total

    FROM sales

    WHERE payment_method IS NOT NULL

    GROUP BY payment_method
""")
    payment_data = cur.fetchall()
    payments = {
    'UPI': 0,
    'Cash': 0,
    'Card': 0 }

    for method, count in payment_data:
        payments[method] = count
    max_payment = max(payments.values())
    if max_payment == 0:
        max_payment = 1

   
    cur.execute("""
    SELECT DAYNAME(created_at),
           SUM(total) AS revenue

    FROM sales

    GROUP BY DAYNAME(created_at)

    ORDER BY revenue DESC

    LIMIT 1
""")

    result = cur.fetchone()

    if result:
        best_day = result[0]
        best_day_revenue = result[1]
    else:
        best_day = "N/A"
        best_day_revenue = 0
    cur.execute("""
    SELECT DAYNAME(created_at),
           SUM(total)

    FROM sales

    GROUP BY DAYNAME(created_at)
""")

    weekly_sales = cur.fetchall()
    week_data = {
    'Monday': 0,
    'Tuesday': 0,
    'Wednesday': 0,
    'Thursday': 0,
    'Friday': 0,
    'Saturday': 0,
    'Sunday': 0
}

    for day, revenue in weekly_sales:
     week_data[day] = float(revenue)
    max_revenue = max(week_data.values())

    if max_revenue == 0:
        max_revenue = 1
    cur.execute("""
    SELECT HOUR(created_at),
           COUNT(*) AS orders_count

    FROM sales

    GROUP BY HOUR(created_at)

    ORDER BY orders_count DESC

    LIMIT 1
""")

    peak = cur.fetchone()

    if peak:
        start_hour = peak[0]
        end_hour = (start_hour + 1) % 24

        peak_hour = f"{start_hour:02d}:00 - {end_hour:02d}:00"
        peak_orders = peak[1]
    else:
        peak_hour = "N/A"
        peak_orders = 0
    cur.execute("""
    SELECT MONTH(created_at),
           SUM(total)

    FROM sales

    GROUP BY MONTH(created_at)

    ORDER BY MONTH(created_at) DESC

    LIMIT 2
""")

    months = cur.fetchall()

    if len(months) == 2:

        current = float(months[0][1])
        previous = float(months[1][1])

        if previous > 0:
            growth = ((current - previous) / previous) * 100
        else:
            growth = 100

    else:
        growth = 0
    cur.execute("""
    SELECT IFNULL(SUM(total), 0)

    FROM sales

    WHERE DATE(created_at) = CURDATE()
""")

    today_revenue = cur.fetchone()[0]
    cur.execute("""
    SELECT customer_name,
           total,
           status

    FROM orders

    ORDER BY id DESC

    LIMIT 5
""")

    recent_orders = cur.fetchall()
    cur.execute("""
    SELECT product_name,
           SUM(quantity) AS sold

    FROM sales

    WHERE product_name IS NOT NULL

    GROUP BY product_name

    ORDER BY sold DESC

    LIMIT 5
""")

    top_items = cur.fetchall()
    week_values = list(week_data.values())
    top_labels = [item[0] for item in top_items]
    top_counts = [item[1] for item in top_items]
    cur.execute("""
    SELECT name,
           role,
           status

    FROM staff
""")

    staff_list = cur.fetchall()
    cur.execute("SELECT COUNT(*) FROM staff")
    total_staff = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM staff WHERE status='On Duty'")
    on_duty = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM staff WHERE status='Absent'")
    absent = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM staff WHERE status='On Leave'")
    on_leave = cur.fetchone()[0]
    cur.execute("""
    SELECT id,
           product_name,
           price
    FROM products
""")

    products = cur.fetchall()
    cur.close()
    return render_template(
        'dashboard.html',
        username=session['username'],
        active_orders=active_orders,
        completed_orders=completed_orders,
        inventory_items=inventory_items,
        low_stock=low_stock,
        inventory=inventory,
        orders_list=orders_list,
        products=products,
        sales_list=sales_list,
        total_revenue=total_revenue,
        transactions=transactions,
        top_product=top_product,
        payment=payment,
        top_item_name=top_item_name,
        top_item_count=top_item_count,
        best_day_revenue=best_day_revenue,
        payments=payments,
        max_payment=max_payment,
        best_day=best_day,  
        week_data=week_data,
        max_revenue=max_revenue,
        peak_hour=peak_hour,
        peak_orders=peak_orders,
        growth=round(growth, 1),
        total_orders = active_orders + completed_orders,
        recent_orders = recent_orders,
         week_values=week_values,
        top_labels=top_labels,
        top_counts=top_counts,
        staff_list=staff_list,
        total_staff=total_staff,
        on_duty=on_duty,
        absent=absent,
        on_leave=on_leave, )

@app.route('/add_order', methods=['POST'])
def add_order():

    if 'username' not in session:
        return redirect(url_for('login'))

    customer_name = request.form['customer_name']
    total = request.form['total']
    status = request.form['status']

    cur = mysql.connection.cursor()

    cur.execute(
        """
        INSERT INTO orders
        (customer_name, total, status)

        VALUES (%s, %s, %s)
        """,

        (customer_name, total, "Pending")
    )

    mysql.connection.commit()
    

    cur.close()

    return redirect(url_for('dashboard'))
@app.route('/complete_order/<int:order_id>', methods=['POST'])
def complete_order(order_id):

    if 'username' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    cur.execute(
        """
        UPDATE orders
        SET status='Done'
        WHERE id=%s
        """,

        (order_id,)
    )

    mysql.connection.commit()

    cur.close()

    return redirect(url_for('dashboard'))
@app.route('/delete_order/<int:order_id>',
           methods=['POST'])

def delete_order(order_id):

    if 'username' not in session:
        return redirect(url_for('login'))

    cur = mysql.connection.cursor()

    cur.execute(
        """
        DELETE FROM orders
        WHERE id=%s
        """,

        (order_id,)
    )
    mysql.connection.commit()
    cur.close()
    return redirect(url_for('dashboard'))
@app.route('/create_bill', methods=['POST'])
def create_bill():

    if 'username' not in session:
        return redirect(url_for('login'))

    product_id = request.form['product_id']
    quantity = int(request.form['quantity'])
    payment_method = request.form['payment_method']

    cur = mysql.connection.cursor()

    cur.execute("""SELECT product_name, price FROM products WHERE id=%s""",(product_id,))
    product = cur.fetchone()

    total = product[1] * quantity
    cur.execute("""INSERT INTO sales (product_name, quantity, total, payment_method) VALUES (%s, %s, %s, %s)""",(product[0],quantity,total,payment_method))   

    mysql.connection.commit()

    cur.close()

    return redirect(url_for('dashboard'))
@app.route('/products')
def products():
    cursor = mysql.connection.cursor()

    cursor.execute("""
        SELECT id, product_name, price
        FROM products
    """)

    products = cursor.fetchall()

    cursor.close()

    return render_template(
        'products.html',
        products=products
    )
@app.route('/add_product', methods=['POST'])
def add_product():

    product_name = request.form['product_name']

    price = request.form['price']

    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        INSERT INTO products (
            product_name,
            price
        )
        VALUES (%s, %s)
        """,
        (product_name, price)
    )

    mysql.connection.commit()

    cursor.close()

    return redirect(url_for('dashboard'))
@app.route('/edit_product/<int:id>', methods=['POST'])
def edit_product(id):

    product_name = request.form['product_name']
    price = request.form['price']
    print("EDIT ROUTE HIT")
    print(request.form)
    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        UPDATE products
        SET product_name = %s,
            price = %s
        WHERE id = %s
        """,
        (product_name, price, id)
    )

    mysql.connection.commit()

    cursor.close()

    return redirect(url_for('dashboard'))

@app.route('/delete_product/<int:id>', methods=['POST'])
def delete_product(id):
    print(f"Deleting product ID: {id}")
    cursor = mysql.connection.cursor()

    cursor.execute(
        """
        DELETE FROM products
        WHERE id = %s
        """,
        (id,)
    )

    mysql.connection.commit()

    cursor.close()

    return redirect(url_for('dashboard')) 
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
