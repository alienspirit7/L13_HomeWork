"""
Configuration loader for Weather Data Agent
Loads environment variables and validates required credentials
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

def _load_api_key(env_var_name: str) -> str:
    """
    Load API key from environment variable or file.
    If the env var points to a file path, read from that file.
    Otherwise, return the env var value directly.
    """
    value = os.getenv(env_var_name)
    if not value:
        return None

    # Check if it's a file path
    if os.path.isfile(value):
        try:
            with open(value, 'r') as f:
                return f.read().strip()
        except Exception as e:
            print(f"Warning: Could not read API key from file {value}: {e}")
            return None

    # Otherwise, treat it as the key itself
    return value

class Config:
    """Configuration class for the Weather Data Agent"""

    # LLM Provider Configuration
    LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'gemini').lower()  # 'gemini' or 'anthropic'

    # Gemini API Configuration
    GEMINI_API_KEY = _load_api_key('GEMINI_API_KEY')

    # Anthropic API Configuration (optional)
    ANTHROPIC_API_KEY = _load_api_key('ANTHROPIC_API_KEY')

    # Google Cloud Configuration
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

    # BigQuery Configuration
    BIGQUERY_PROJECT = 'bigquery-public-data'
    BIGQUERY_DATASET = 'noaa_gsod'
    BIGQUERY_TABLE = 'gsod2024'

    # Output Configuration
    OUTPUT_DIR = Path(__file__).parent / 'outputs'
    PROMPTS_DIR = Path(__file__).parent / 'prompts'

    # Query Limits (for POC)
    MAX_QUERY_ROWS = 10000

    @classmethod
    def validate(cls):
        """Validate that all required configuration is present"""
        errors = []

        # Validate LLM provider
        if cls.LLM_PROVIDER not in ['gemini', 'anthropic']:
            errors.append(f"LLM_PROVIDER must be 'gemini' or 'anthropic', got '{cls.LLM_PROVIDER}'")

        # Check for appropriate API key based on provider
        if cls.LLM_PROVIDER == 'gemini':
            if not cls.GEMINI_API_KEY:
                errors.append("GEMINI_API_KEY not found in environment variables (required for gemini provider)")
        elif cls.LLM_PROVIDER == 'anthropic':
            if not cls.ANTHROPIC_API_KEY:
                errors.append("ANTHROPIC_API_KEY not found in environment variables (required for anthropic provider)")

        # Google credentials are optional if using Application Default Credentials
        if not cls.GOOGLE_APPLICATION_CREDENTIALS:
            print("Warning: GOOGLE_APPLICATION_CREDENTIALS not set. Will attempt to use Application Default Credentials.")

        # Create output directory if it doesn't exist
        cls.OUTPUT_DIR.mkdir(exist_ok=True)

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

        return True

    @classmethod
    def get_bigquery_table_path(cls):
        """Get the full BigQuery table path"""
        return f"{cls.BIGQUERY_PROJECT}.{cls.BIGQUERY_DATASET}.{cls.BIGQUERY_TABLE}"


# Validate configuration on import
if __name__ != "__main__":
    try:
        Config.validate()
        print("✓ Configuration loaded successfully")
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("\nPlease create a .env file with the following variables:")
        print("  LLM_PROVIDER=gemini  # or 'anthropic'")
        print("  GEMINI_API_KEY=your_gemini_api_key_here  # if using gemini")
        print("  ANTHROPIC_API_KEY=your_anthropic_api_key_here  # if using anthropic")
        print("  GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json (optional)")
