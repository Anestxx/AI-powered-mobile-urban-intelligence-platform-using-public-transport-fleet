"""Start the alert API from any working directory."""

import argparse
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    import uvicorn

    app_dir = Path(__file__).resolve().parent / "03_backend_database"
    sys.path.insert(0, str(app_dir))
    uvicorn.run("app.main:app", host=args.host, port=args.port, reload=args.reload,
                reload_dirs=[str(app_dir)] if args.reload else None)


if __name__ == "__main__":
    main()
