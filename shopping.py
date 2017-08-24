from flask import Flask, request, render_template, flash, redirect, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)

#Config MySQL
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = "Yardie12"
app.config["MYSQL_DB"] = "shoppingapp"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
#init MySQL
mysql = MySQL(app)

def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("unauthorized, Please login", "danger")
            return redirect(url_for("login"))
    return wrap

@app.route("/")
def homepage():
    return render_template("home.html")

@app.route("/items")
def items():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM items")

    items = cur.fetchall()

    if result > 0:
        return render_template("items.html", items=items)
    else:
        msg = "No Items Found"
        return render_template("items.html", msg=msg)

    cur.close()

@app.route("/item/<string:id>/")
def item(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM items WHERE id = %s", [id])

    item = cur.fetchone()

    return render_template("item.html", item=item)

class RegisterForm(Form):
    name = StringField("Name", [validators.Length(min=1, max=50)])
    username = StringField("Username", [validators.Length(min=4, max=25)])
    email = StringField("Email", [validators.Length(min=6, max=50)])
    password = PasswordField("Password", [
        validators.DataRequired(),
        validators.EqualTo("confirm", message="passwords do not match")
    ])
    confirm = PasswordField("Confirm Password")

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #Create cursor
        cur = mysql.connection.cursor()

        #Execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash("You are now registered and can log in", "success")

        return redirect(url_for("login"))
    return render_template("register.html", form=form)


@app.route("/dashboard")
@is_logged_in
def dashboard():
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM items")

    items = cur.fetchall()

    if result > 0:
        return render_template("dashboard.html", items=items)
    else:
        msg = "No Items Found"
        return render_template("dashboard.html", msg=msg)

    cur.close()

@app.route("/shopping")
@is_logged_in
def shopping():
    food = ["Bread", "Milk", "Water", "Juice",
            "Rice", "Papaya", "Chicken", "Tuna"]
    return render_template("shopping.html", food=food)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password_candidate = request.form["password"]

        cur = mysql.connection.cursor()
        result = cur.execute(
            "SELECT * FROM users WHERE username = %s", [username])

        if result > 0:
            data = cur.fetchone()
            password = data["password"]

            if sha256_crypt.verify(password_candidate, password):
                session["logged_in"] = True
                session["username"] = username

                flash("You are now logged in", "success")
                return redirect(url_for("dashboard"))
            else:
                error = "Invalid login"
                return render_template("login.html", error=error)
            cur.close()
        else:
            error = "Username not found"
            return render_template("login.html", error=error)

    return render_template("login.html")

@app.route("/logout")
@is_logged_in
def logout():
    session.clear()
    return redirect(url_for("login"))


class ItemForm(Form):
    item = StringField("Item", [validators.Length(min=1, max=200)])
    price = TextAreaField("Price", [validators.Length(min=0, max=5)])

@app.route("/add_item", methods=["GET", "POST"])
@is_logged_in
def add_item():
    form = ItemForm(request.form)
    if request.method == "POST" and form.validate():
        item = form.item.data
        price = form.price.data

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO items(item, price, author) VALUES(%s, %s, %s)", (item, price, session["username"]))

        # Commit to db
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash("Item Created", "success")

        return redirect(url_for("dashboard"))

    return render_template("add_item.html", form=form)


@app.route("/edit_item/<string:id>", methods=["GET", "POST"])
@is_logged_in
def edit_item(id):
    cur = mysql.connection.cursor()

    result = cur.execute("SELECT * FROM items WHERE id = %s", [id])

    item = cur.fetchone()

    form = ItemForm(request.form)

    form.item.data = item["item"]
    form.price.data = item["price"]

    if request.method == "POST" and form.validate():
        item = request.form["item"]
        price = request.form["price"]

        # Create cursor
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("UPDATE items SET item=%s, price=%s WHERE id = %s", (item, price, id))

        # Commit to db
        mysql.connection.commit()

        # Close connection
        cur.close()

        flash("Item Updated", "success")

        return redirect(url_for("dashboard"))

    return render_template("edit_item.html", form=form)


@app.route("/delete_item/<string:id>", methods=["POST"])
@is_logged_in
def delete_item(id):

    cur = mysql.connection.cursor()

    cur.execute("DELETE FROM items WHERE id = %s", [id])

    # Commit to db
    mysql.connection.commit()

    # Close connection
    cur.close()

    flash("Item Deleted", "success")

    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.secret_key = "secret123"
    app.run(debug=True)
