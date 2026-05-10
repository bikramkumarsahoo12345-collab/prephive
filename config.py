import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, "prephive.db")

ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@prephive.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf"}
