"""Video Review workbench. Start from the launcher or run py -3.12 video_review.py."""
from pathlib import Path
import argparse
import sys
import webbrowser

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action")
    serve = sub.add_parser("serve", help="Open the local video review workbench")
    serve.add_argument("--port", type=int, default=0)
    serve.add_argument("--no-browser", action="store_true")
    render = sub.add_parser("render", help="Explicitly render a saved handoff and attach the next round")
    render.add_argument("--packet", type=Path, required=True)
    render.add_argument("--output", type=Path)
    render.add_argument("--size")
    render.add_argument("--fps", type=int)
    args = parser.parse_args()
    try:
        if args.action == "render":
            from video_review.render_bridge import render_packet
            return render_packet(args.packet, ROOT, args.output, args.size, args.fps)
        if args.action is None:
            import launcher_common
            launcher_common.consume_config("video_review")
        from video_review.server import make_server
        server = make_server(ROOT, getattr(args, "port", 0))
        url = f"http://127.0.0.1:{server.server_port}/"
        print(f"Video Review: {url}\nReviews are saved under {ROOT / 'video_reviews'}\nKeep this process running while reviewing. Ctrl+C stops it.", flush=True)
        if not getattr(args, "no_browser", False):
            webbrowser.open(url)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.server_close()
        return 0
    except (OSError, ValueError, ImportError) as exc:
        print(f"Video Review: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
