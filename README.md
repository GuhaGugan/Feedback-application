# Feedback Application

A web application for collecting user feedback with QR code and link access, featuring a dashboard that consolidates and displays feedback categorized by rating (positive, negative, medium).
CI/CD test gugan Testing CI/CD pipeline.
## Features

- 📝 User feedback collection via web form
- 🔗 Access via direct link or QR code scan
- ⭐ Star-based rating system (1-5 stars)
- 📊 **Admin-only dashboard** with consolidated feedback statistics
- 🔒 Password-protected admin access
- 📈 Categorization: Positive (4-5 stars), Medium (3 stars), Negative (1-2 stars)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python app.py
```

3. Access the application:
- **Feedback form** (public): http://localhost:5000/feedback
- **Admin login**: http://localhost:5000/login
- **Dashboard** (admin only): http://localhost:5000/dashboard
- **QR code**: http://localhost:5000/qr

## Usage

1. Share the feedback link or QR code with users
2. Users submit feedback with star ratings and comments
3. **Admin access**: Login at `/login` to view the dashboard
   - Default password: `admin123` (change in `app.py` or set `ADMIN_PASSWORD` environment variable)
4. View consolidated feedback statistics on the dashboard

## Security

- The dashboard and API endpoints are protected and require admin login
- Change the default admin password in production by:
  - Setting the `ADMIN_PASSWORD` environment variable, or
  - Modifying the `ADMIN_PASSWORD` variable in `app.py`
- Change the `SECRET_KEY` in production for session security





