import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )

    # Third-party libraries are noisy at INFO; keep them at WARNING unless
    # we're specifically debugging network/SDK behavior.
    for noisy_logger in ("botocore", "boto3", "urllib3", "httpx"):
        logging.getLogger(noisy_logger).setLevel(logging.WARNING)
