# PrepHive

PrepHive is a student resource sharing platform for Previous Year Question (PYQ) papers.

## What was added

- Flask backend application in `app.py`
- SQLite database setup (auto-initialized on first run)
- Student signup/login via `/signup.html` and `/login.html`
- Admin upload module via `/admin/login` and `/admin/upload`
- Paper listing and download via `/papers`
- PDF upload support with files stored in `uploads/`
- Templates preserve the current frontend UI and page structure

## Setup

1. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with admin credentials (optional):

   ```env
   ADMIN_EMAIL=admin@prephive.com
   ADMIN_PASSWORD=admin123
   FLASK_SECRET_KEY=super-secret-value
   ```

3. Run the app:

   ```powershell
   python app.py
   ```

4. Open in your browser:
   - **Home**: `http://127.0.0.1:5000/1.html`
   - **Admin Login**: `http://127.0.0.1:5000/admin/login`
   - Default admin: `admin@prephive.com` / `admin123`

## Render deployment

- Render requires the app to bind to `0.0.0.0` and the port supplied by the `PORT` environment variable.
- This app now supports `HOST` and `PORT` environment variables.
- For Render, you can use `python app.py` as the start command.

## Notes

- SQLite database (`prephive.db`) is auto-created on first run
- Existing static pages are preserved in the workspace
- PDF uploads are stored locally in the `uploads/` folder
- No MySQL setup required—everything works out of the box

