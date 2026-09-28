# 📚 BookNest — Flask + SQLite E-commerce Bookstore

A complete college-project-friendly online bookstore built with:

- HTML5
- CSS3
- Vanilla JavaScript
- Python Flask
- SQLite
- Jinja2 templates

## Features

1. 16 seeded books
2. Home, Books and Book Details pages
3. Search, category, price, rating and sorting filters
4. Cart with quantity updates
5. Wishlist
6. Registration, login and logout
7. Password hashing
8. Checkout and order history
9. User profile
10. Admin dashboard
11. Admin add/edit/delete books
12. Contact form stored in SQLite
13. Responsive desktop/tablet/mobile design
14. Remote book covers with fallback
15. ₹ INR pricing
16. 403/404/500 error pages
17. Automatic SQLite database creation and seed data

## Demo accounts

**Admin**
- Email: `admin@booknest.com`
- Password: `Admin@123`

**User**
- Email: `reader@booknest.com`
- Password: `Reader@123`

## Run on Windows

Open PowerShell in this folder:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open:

`http://127.0.0.1:5000`

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Or skip activation and use:

```powershell
py -m pip install -r requirements.txt
py app.py
```

The `booknest.db` SQLite database is created automatically on first run.

## Important

This project uses demo data and remote Open Library cover URLs. An internet connection helps book covers load; a placeholder is shown if a remote cover is unavailable.

For a real production deployment, change `app.secret_key`, enable HTTPS, add CSRF protection, use environment variables for secrets, and configure a production WSGI server.
