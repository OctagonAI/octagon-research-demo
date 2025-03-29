from dotenv import load_dotenv
import os
import pathlib
from openai import AsyncOpenAI

load_dotenv()  # Load environment variables from .env file

# === API KEYS ===
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OCTAGON_API_KEY = os.getenv("OCTAGON_API_KEY")
OCTAGON_API_BASE_URL = os.getenv("OCTAGON_API_BASE_URL", "https://api.octagonagents.com/v1")

# === TEMPLATE PATHS ===
BASE_DIR = pathlib.Path(__file__).resolve().parent
BASE_DIR_CSV = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_PATH = BASE_DIR / "templates" / "template.md"
# Default CSV path - use CLI argument to override
CSV_PATH = os.path.join(BASE_DIR_CSV, "input", "companies.csv")
REPORTS_DIR = os.environ.get("REPORTS_DIR", str(BASE_DIR / "reports"))

# === Clients ===
octagon_client = AsyncOpenAI(
    api_key=OCTAGON_API_KEY,
    base_url=OCTAGON_API_BASE_URL,
)
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)