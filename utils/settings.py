import os

import dotenv

dotenv.load_dotenv()

URL = os.getenv("POKE_URL")
ABILITY_URL = os.getenv("ABILITY_URL")

DB_URL = os.getenv("DB_URL")

PROJECT_ID = os.getenv("PROJECT_ID")
BUCKET_NAME = os.getenv("BUCKET_NAME")

POKE_GCS_URL = os.getenv("POKE_GCS_URL")
HOME = os.getenv("HOME")
