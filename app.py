from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import bcrypt
from flask import send_from_directory


app = Flask(__name__)
app.secret_key = 'cafe_secret_key_123'

# MySQL config — update these with your details
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'   # ← must be root, not test
app.config['MYSQL_PASSWORD'] = 'ezra4427'   # ← leave empty if no password
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
           COUNT(*) AS count

    FROM sales

    WHERE payment_method IS NOT NULL

    GROUP BY payment_method

    ORDER BY count DESC

    LIMIT 1
""")

    payment = cur.fetchone()

    if payment:
        favorite_payment = payment[0]
        payment_count = payment[1]
    else:
        favorite_payment = "N/A"
        payment_count = 0
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
        favorite_payment=favorite_payment,
        payment_count=payment_count,
        weekly_sales=weekly_sales
        )

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

        (customer_name, total, status)
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
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)