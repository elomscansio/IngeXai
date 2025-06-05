import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/ingexai")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
