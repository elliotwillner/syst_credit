from pathlib import Path
import yaml


def load_config(path: str | Path) -> dict:
    """
    Load configuration from a YAML file.

    Parameters
    ----------
    path : str | Path
        Path to the YAML config file.

    Returns
    -------
    dict
        Loaded configuration as a dictionary.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r") as f:
        config = yaml.safe_load(f)

    required_sections = ["paths", "data", "features", "regime", "portfolio"]
    missing = [s for s in required_sections if s not in config]

    if missing:
        raise ValueError(f"Missing config sections: {missing}")

    return config