"""Initialize a fresh multiprocess directory before importing the application."""
import os
import sys
from pathlib import Path


def main():
    folder = Path(os.environ["PROMETHEUS_MULTIPROC_DIR"])
    for path in folder.glob("*.db"):
        path.unlink()
    os.execvp(sys.argv[1], sys.argv[1:])


if __name__ == "__main__":
    main()
