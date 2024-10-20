from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

from .utils import (
    get_programmes_by_ks,
    get_programmes_by_subject,
    load_oak_lessons,
    load_oak_lessons_df,
    DATA_DIR,
    PROJ_ROOT
)
# from .embeddings import BM25, get_embeddings

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
