import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://root:root@localhost/ingexai")
SECRET_KEY = os.getenv("SECRET_KEY", "supersecret")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
