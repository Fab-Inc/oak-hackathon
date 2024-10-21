from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

import constants
from .constants import *
import utils
from .utils import *
import embeddings
from .embeddings import *


# Load environment variables from .env file if it exists
load_dotenv()

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass
