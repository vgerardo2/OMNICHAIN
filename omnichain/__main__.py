"""Run with python -m omnichain; no installation or downloaded dependencies."""
import argparse
import json
from pathlib import Path
from .server import AppServer


def main():
    parser = argparse.ArgumentParser(description="Local synthetic OmniChain assessment")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).resolve().parent.parent / "runtime")
    parser.add_argument("--verify-export", type=Path, help="Verify a saved JSON bundle without starting the server")
    parser.add_argument('--backup-to',type=Path,help='Back up a stopped-server data directory into a new folder')
    args = parser.parse_args()
    if args.backup_to:
        from .evidence import Ledger
        print(json.dumps(Ledger(args.data_dir).backup(args.backup_to)))
        return
    if args.verify_export:
        from .evidence import verify_export
        try:
            check = verify_export(json.loads(args.verify_export.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            check = {"integrity":False,"complete":False,"errors":["Cannot read export"]}
        print(json.dumps(check))
        raise SystemExit(0 if check["integrity"] and check["complete"] else 1)
    server = AppServer(args.port, args.data_dir)
    print("OmniChain: " + server.origin, flush=True)
    print("SIMULATED ENVIRONMENT. Live model requests disabled unless explicitly configured.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
