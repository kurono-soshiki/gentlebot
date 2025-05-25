from dotenv import load_dotenv

load_dotenv()

import os
# import sys
# sys.path.append(os.getcwd())
import logging

logger = logging.getLogger(__name__)

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')