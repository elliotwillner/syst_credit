import logging
from pathlib import Path


def setup_logging(log_dir: str = "logs", level: int = logging.INFO):
    """
    Set up logging to file and console with a standardized format.
    """
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    log_file = Path(log_dir) / "pipeline.log"

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ],
    )