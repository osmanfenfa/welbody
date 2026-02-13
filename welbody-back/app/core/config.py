from dotenv import load_dotenv
import os
from pathlib import Path

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

class Settings:
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_this_later")

settings = Settings()
print("DATABASE_URL loaded:", settings.DATABASE_URL is not None)
