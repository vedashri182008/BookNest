from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from pathlib import Path
import sqlite3, re

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "booknest.db"

app = Flask(__name__)
app.secret_key = "booknest-dev-secret-change-this"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        author TEXT NOT NULL,
        category TEXT NOT NULL,
        price REAL NOT NULL,
        original_price REAL NOT NULL,
        rating REAL DEFAULT 4.5,
        review_count INTEGER DEFAULT 0,
        description TEXT NOT NULL,
        image TEXT NOT NULL,
        stock INTEGER DEFAULT 10,
        publisher TEXT DEFAULT 'BookNest Publishing',
        language TEXT DEFAULT 'English',
        pages INTEGER DEFAULT 200,
        isbn TEXT DEFAULT ''
    );
    CREATE TABLE IF NOT EXISTS cart_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        UNIQUE(user_id, book_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS wishlist_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        UNIQUE(user_id, book_id),
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total REAL NOT NULL,
        status TEXT DEFAULT 'Placed',
        address TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        book_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY(order_id) REFERENCES orders(id) ON DELETE CASCADE,
        FOREIGN KEY(book_id) REFERENCES books(id)
    );
    CREATE TABLE IF NOT EXISTS contacts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        message TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        conn.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                     ("BookNest Admin","admin@booknest.com",generate_password_hash("Admin@123"),"admin"))
        conn.execute("INSERT INTO users(name,email,password,role) VALUES(?,?,?,?)",
                     ("BookNest Reader","reader@booknest.com",generate_password_hash("Reader@123"),"user"))
    if conn.execute("SELECT COUNT(*) FROM books").fetchone()[0] == 0:
        books = [
            ("Atomic Habits","James Clear","Self Help",499,699,4.8,12450,"An easy and proven framework for building good habits and breaking bad ones.","https://covers.openlibrary.org/b/isbn/9780735211292-L.jpg",18,"Avery","English",320,"9780735211292"),
            ("The Psychology of Money","Morgan Housel","Finance",399,599,4.7,9820,"Timeless lessons on wealth, greed, risk and making better financial decisions.","https://covers.openlibrary.org/b/isbn/9780857197689-L.jpg",22,"Harriman House","English",256,"9780857197689"),
            ("Rich Dad Poor Dad","Robert T. Kiyosaki","Finance",349,499,4.6,8500,"A personal finance classic about money, assets, liabilities and financial education.","https://covers.openlibrary.org/b/isbn/9781612680194-L.jpg",15,"Plata Publishing","English",336,"9781612680194"),
            ("Think Like a Monk","Jay Shetty","Self Help",429,599,4.5,6340,"Train your mind for peace and purpose with practical lessons inspired by monk wisdom.","https://covers.openlibrary.org/b/isbn/9781982134488-L.jpg",17,"Simon & Schuster","English",352,"9781982134488"),
            ("Clean Code","Robert C. Martin","Programming",699,899,4.8,5210,"A practical guide to writing readable, maintainable and professional software.","https://covers.openlibrary.org/b/isbn/9780132350884-L.jpg",12,"Prentice Hall","English",464,"9780132350884"),
            ("Dune","Frank Herbert","Fiction",449,699,4.7,11800,"An epic science-fiction novel of politics, ecology, power and destiny.","https://covers.openlibrary.org/b/isbn/9780441172719-L.jpg",20,"Ace","English",688,"9780441172719"),
            ("The Alchemist","Paulo Coelho","Fiction",299,399,4.6,10400,"A philosophical journey about following dreams, purpose and personal discovery.","https://covers.openlibrary.org/b/isbn/9780062315007-L.jpg",25,"HarperOne","English",208,"9780062315007"),
            ("Ikigai","Hector Garcia","Lifestyle",329,499,4.5,7800,"A gentle exploration of purpose, longevity and everyday meaning.","https://covers.openlibrary.org/b/isbn/9780143130727-L.jpg",16,"Penguin","English",208,"9780143130727"),
            ("Deep Work","Cal Newport","Productivity",449,599,4.7,6950,"Rules for focused success in a distracted world.","https://covers.openlibrary.org/b/isbn/9781455586691-L.jpg",14,"Grand Central","English",304,"9781455586691"),
            ("The 7 Habits of Highly Effective People","Stephen R. Covey","Self Help",499,699,4.7,9100,"A principle-centered approach to personal and professional effectiveness.","https://covers.openlibrary.org/b/isbn/9781982137274-L.jpg",10,"Simon & Schuster","English",464,"9781982137274"),
            ("Introduction to Algorithms","Thomas H. Cormen","Programming",899,1199,4.6,4200,"A comprehensive introduction to modern algorithms and algorithmic problem solving.","https://covers.openlibrary.org/b/isbn/9780262046305-L.jpg",8,"MIT Press","English",1312,"9780262046305"),
            ("Python Crash Course","Eric Matthes","Programming",649,799,4.8,6100,"A hands-on introduction to Python programming with practical projects.","https://covers.openlibrary.org/b/isbn/9781593279288-L.jpg",13,"No Starch Press","English",544,"9781593279288"),
            ("The Midnight Library","Matt Haig","Fiction",379,499,4.4,7300,"A novel about choices, possibilities and the lives we might have lived.","https://covers.openlibrary.org/b/isbn/9780525559474-L.jpg",19,"Viking","English",304,"9780525559474"),
            ("Sapiens","Yuval Noah Harari","History",499,699,4.7,9900,"A sweeping story of human history from the Stone Age to the modern world.","https://covers.openlibrary.org/b/isbn/9780062316097-L.jpg",11,"Harper","English",464,"9780062316097"),
            ("The Silent Patient","Alex Michaelides","Thriller",359,499,4.5,8700,"A psychological mystery centered on a famous painter and a shocking silence.","https://covers.openlibrary.org/b/isbn/9781250301697-L.jpg",21,"Celadon Books","English",336,"9781250301697"),
            ("Start With Why","Simon Sinek","Business",429,599,4.6,5500,"Discover how inspiring leaders communicate purpose and create lasting impact.","https://covers.openlibrary.org/b/isbn/9781591846444-L.jpg",9,"Portfolio","English",256,"9781591846444")
        ]
        conn.executemany("""INSERT INTO books
        (title,author,category,price,original_price,rating,review_count,description,image,stock,publisher,language,pages,isbn)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", books)
    conn.commit()
    conn.close()

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please login to continue.", "info")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper

def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            abort(403)
        return f(*args, **kwargs)
    return wrapper

@app.context_processor
def globals():
    cart_count = 0
    wishlist_count = 0
    if session.get("user_id"):
        conn = get_db()
        cart_count = conn.execute("SELECT COALESCE(SUM(quantity),0) FROM cart_items WHERE user_id=?", (session["user_id"],)).fetchone()[0]
        wishlist_count = conn.execute("SELECT COUNT(*) FROM wishlist_items WHERE user_id=?", (session["user_id"],)).fetchone()[0]
        conn.close()
    return {"cart_count": cart_count, "wishlist_count": wishlist_count}

@app.route("/")
def home():
    conn = get_db()
    books = conn.execute("SELECT * FROM books ORDER BY rating DESC LIMIT 8").fetchall()
    categories = conn.execute("SELECT category, COUNT(*) count FROM books GROUP BY category ORDER BY category").fetchall()
    conn.close()
    return render_template("home.html", books=books, categories=categories)

@app.route("/books")
def books():
    q = request.args.get("q","").strip()
    category = request.args.get("category","").strip()
    sort = request.args.get("sort","featured")
    min_price = request.args.get("min_price","").strip()
    max_price = request.args.get("max_price","").strip()
    rating = request.args.get("rating","").strip()
    sql = "SELECT * FROM books WHERE 1=1"
    params=[]
    if q:
        sql += " AND (title LIKE ? OR author LIKE ? OR category LIKE ?)"
        params += [f"%{q}%",f"%{q}%",f"%{q}%"]
    if category:
        sql += " AND category=?"; params.append(category)
    if min_price:
        try: sql += " AND price>=?"; params.append(float(min_price))
        except ValueError: pass
    if max_price:
        try: sql += " AND price<=?"; params.append(float(max_price))
        except ValueError: pass
    if rating:
        try: sql += " AND rating>=?"; params.append(float(rating))
        except ValueError: pass
    order = {"price_low":"price ASC","price_high":"price DESC","rating":"rating DESC","name":"title ASC"}.get(sort,"rating DESC")
    sql += f" ORDER BY {order}"
    conn=get_db()
    rows=conn.execute(sql,params).fetchall()
    cats=conn.execute("SELECT DISTINCT category FROM books ORDER BY category").fetchall()
    conn.close()
    return render_template("books.html", books=rows, categories=cats, q=q, category=category, sort=sort, min_price=min_price, max_price=max_price, rating=rating)

@app.route("/book/<int:book_id>")
def book_detail(book_id):
    conn=get_db()
    book=conn.execute("SELECT * FROM books WHERE id=?", (book_id,)).fetchone()
    related=conn.execute("SELECT * FROM books WHERE category=? AND id!=? LIMIT 4",(book["category"],book_id)).fetchall() if book else []
    conn.close()
    if not book: abort(404)
    return render_template("book_detail.html", book=book, related=related)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        name=request.form.get("name","").strip()
        email=request.form.get("email","").strip().lower()
        password=request.form.get("password","")
        if not name or not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$",email) or len(password)<6:
            flash("Enter a valid name, email and password (6+ characters).","error")
            return render_template("register.html")
        conn=get_db()
        try:
            conn.execute("INSERT INTO users(name,email,password) VALUES(?,?,?)",(name,email,generate_password_hash(password)))
            conn.commit()
            flash("Registration successful. Please login.","success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Email is already registered.","error")
        finally: conn.close()
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip().lower()
        password=request.form.get("password","")
        conn=get_db(); user=conn.execute("SELECT * FROM users WHERE email=?",(email,)).fetchone(); conn.close()
        if user and check_password_hash(user["password"],password):
            session.update(user_id=user["id"], user_name=user["name"], role=user["role"])
            flash("Welcome back!","success")
            return redirect(request.args.get("next") or url_for("home"))
        flash("Invalid email or password.","error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear(); flash("You have been logged out.","success"); return redirect(url_for("home"))

@app.route("/profile")
@login_required
def profile():
    conn=get_db()
    user=conn.execute("SELECT id,name,email,role,created_at FROM users WHERE id=?",(session["user_id"],)).fetchone()
    orders=conn.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC",(session["user_id"],)).fetchall()
    conn.close()
    return render_template("profile.html", user=user, orders=orders)

@app.route("/cart")
@login_required
def cart():
    conn=get_db()
    items=conn.execute("""SELECT c.quantity,b.*,(c.quantity*b.price) subtotal
                          FROM cart_items c JOIN books b ON b.id=c.book_id
                          WHERE c.user_id=?""",(session["user_id"],)).fetchall()
    conn.close()
    return render_template("cart.html", items=items, total=sum(i["subtotal"] for i in items))

@app.route("/cart/add/<int:book_id>", methods=["POST"])
@login_required
def add_cart(book_id):
    conn=get_db(); book=conn.execute("SELECT * FROM books WHERE id=?",(book_id,)).fetchone()
    if not book: abort(404)
    conn.execute("""INSERT INTO cart_items(user_id,book_id,quantity) VALUES(?,?,1)
                    ON CONFLICT(user_id,book_id) DO UPDATE SET quantity=quantity+1""",(session["user_id"],book_id))
    conn.commit(); conn.close()
    flash("Book added to cart.","success")
    return redirect(request.referrer or url_for("books"))

@app.route("/cart/update/<int:item_id>", methods=["POST"])
@login_required
def update_cart(item_id):
    try: qty=max(1,int(request.form.get("quantity",1)))
    except ValueError: qty=1
    conn=get_db(); conn.execute("UPDATE cart_items SET quantity=? WHERE id=? AND user_id=?",(qty,item_id,session["user_id"])); conn.commit(); conn.close()
    return redirect(url_for("cart"))

@app.route("/cart/remove/<int:item_id>", methods=["POST"])
@login_required
def remove_cart(item_id):
    conn=get_db(); conn.execute("DELETE FROM cart_items WHERE id=? AND user_id=?",(item_id,session["user_id"])); conn.commit(); conn.close()
    flash("Item removed from cart.","success"); return redirect(url_for("cart"))

@app.route("/wishlist")
@login_required
def wishlist():
    conn=get_db()
    items=conn.execute("""SELECT b.* FROM wishlist_items w JOIN books b ON b.id=w.book_id
                          WHERE w.user_id=? ORDER BY w.id DESC""",(session["user_id"],)).fetchall()
    conn.close()
    return render_template("wishlist.html", items=items)

@app.route("/wishlist/toggle/<int:book_id>", methods=["POST"])
@login_required
def wishlist_toggle(book_id):
    conn=get_db()
    exists=conn.execute("SELECT id FROM wishlist_items WHERE user_id=? AND book_id=?",(session["user_id"],book_id)).fetchone()
    if exists:
        conn.execute("DELETE FROM wishlist_items WHERE id=?",(exists["id"],)); msg="Removed from wishlist."
    else:
        conn.execute("INSERT INTO wishlist_items(user_id,book_id) VALUES(?,?)",(session["user_id"],book_id)); msg="Added to wishlist."
    conn.commit(); conn.close(); flash(msg,"success")
    return redirect(request.referrer or url_for("books"))

@app.route("/checkout", methods=["GET","POST"])
@login_required
def checkout():
    conn=get_db()
    items=conn.execute("""SELECT c.book_id,c.quantity,b.title,b.price,b.stock
                          FROM cart_items c JOIN books b ON b.id=c.book_id WHERE c.user_id=?""",(session["user_id"],)).fetchall()
    if not items:
        conn.close(); flash("Your cart is empty.","info"); return redirect(url_for("cart"))
    total=sum(i["quantity"]*i["price"] for i in items)
    if request.method=="POST":
        address=request.form.get("address","").strip()
        if len(address)<10:
            flash("Please enter a complete delivery address.","error"); conn.close()
            return render_template("checkout.html",items=items,total=total)
        for i in items:
            if i["quantity"] > i["stock"]:
                flash(f"Not enough stock for {i['title']}.","error"); conn.close()
                return render_template("checkout.html",items=items,total=total)
        cur=conn.execute("INSERT INTO orders(user_id,total,address) VALUES(?,?,?)",(session["user_id"],total,address))
        order_id=cur.lastrowid
        for i in items:
            conn.execute("INSERT INTO order_items(order_id,book_id,quantity,price) VALUES(?,?,?,?)",(order_id,i["book_id"],i["quantity"],i["price"]))
            conn.execute("UPDATE books SET stock=stock-? WHERE id=?",(i["quantity"],i["book_id"]))
        conn.execute("DELETE FROM cart_items WHERE user_id=?",(session["user_id"],))
        conn.commit(); conn.close()
        flash(f"Order #{order_id} placed successfully!","success")
        return redirect(url_for("profile"))
    conn.close()
    return render_template("checkout.html",items=items,total=total)

@app.route("/contact", methods=["GET","POST"])
def contact():
    if request.method=="POST":
        name=request.form.get("name","").strip(); email=request.form.get("email","").strip(); message=request.form.get("message","").strip()
        if not name or not email or not message:
            flash("Please fill all contact fields.","error")
        else:
            conn=get_db(); conn.execute("INSERT INTO contacts(name,email,message) VALUES(?,?,?)",(name,email,message)); conn.commit(); conn.close()
            flash("Thanks! Your message has been received.","success"); return redirect(url_for("contact"))
    return render_template("contact.html")

@app.route("/admin")
@admin_required
def admin():
    conn=get_db()
    stats={
        "books":conn.execute("SELECT COUNT(*) FROM books").fetchone()[0],
        "users":conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "orders":conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "contacts":conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0],
    }
    books=conn.execute("SELECT * FROM books ORDER BY id DESC").fetchall()
    orders=conn.execute("""SELECT o.*,u.name,u.email FROM orders o JOIN users u ON u.id=o.user_id ORDER BY o.id DESC""").fetchall()
    contacts=conn.execute("SELECT * FROM contacts ORDER BY id DESC").fetchall()
    conn.close()
    return render_template("admin.html",stats=stats,books=books,orders=orders,contacts=contacts)

@app.route("/admin/book/new", methods=["GET","POST"])
@admin_required
def admin_book_new():
    if request.method=="POST":
        data=request.form
        conn=get_db()
        conn.execute("""INSERT INTO books(title,author,category,price,original_price,rating,review_count,description,image,stock,publisher,language,pages,isbn)
                        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                     (data["title"],data["author"],data["category"],float(data["price"]),float(data["original_price"]),
                      float(data.get("rating",4.5)),int(data.get("review_count",0)),data["description"],data["image"],
                      int(data.get("stock",10)),data.get("publisher","BookNest Publishing"),data.get("language","English"),
                      int(data.get("pages",200)),data.get("isbn","")))
        conn.commit(); conn.close(); flash("Book added.","success"); return redirect(url_for("admin"))
    return render_template("book_form.html", book=None)

@app.route("/admin/book/<int:book_id>/edit", methods=["GET","POST"])
@admin_required
def admin_book_edit(book_id):
    conn=get_db(); book=conn.execute("SELECT * FROM books WHERE id=?",(book_id,)).fetchone()
    if not book: conn.close(); abort(404)
    if request.method=="POST":
        d=request.form
        conn.execute("""UPDATE books SET title=?,author=?,category=?,price=?,original_price=?,rating=?,review_count=?,description=?,image=?,stock=?,publisher=?,language=?,pages=?,isbn=? WHERE id=?""",
                     (d["title"],d["author"],d["category"],float(d["price"]),float(d["original_price"]),float(d.get("rating",4.5)),
                      int(d.get("review_count",0)),d["description"],d["image"],int(d.get("stock",10)),d.get("publisher",""),
                      d.get("language","English"),int(d.get("pages",200)),d.get("isbn",""),book_id))
        conn.commit(); conn.close(); flash("Book updated.","success"); return redirect(url_for("admin"))
    conn.close(); return render_template("book_form.html",book=book)

@app.route("/admin/book/<int:book_id>/delete", methods=["POST"])
@admin_required
def admin_book_delete(book_id):
    conn=get_db(); conn.execute("DELETE FROM books WHERE id=?",(book_id,)); conn.commit(); conn.close()
    flash("Book deleted.","success"); return redirect(url_for("admin"))

@app.errorhandler(403)
def forbidden(e): return render_template("error.html",code=403,message="You do not have permission to view this page."),403

@app.errorhandler(404)
def not_found(e): return render_template("error.html",code=404,message="The page you are looking for does not exist."),404

@app.errorhandler(500)
def server_error(e): return render_template("error.html",code=500,message="Something went wrong on the server."),500

init_db()

if __name__ == "__main__":
    app.run(debug=True)
