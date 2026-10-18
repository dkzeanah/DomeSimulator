"""Open the Book Studio: the composer's local server, at /studio.

    py -3.12 -m books.studio                 # opens http://127.0.0.1:8765/studio in the browser
    py -3.12 -m books.studio --no-browser --port 8765
    py -3.12 -m books.studio --selftest
"""

from __future__ import annotations

import argparse
import webbrowser


def selftest() -> None:
    from books.studio import doc as D
    from books.studio import library as lib

    d = D.import_kids_book()
    assert len(d["pages"]) >= 18, len(d["pages"])
    n = len(d["pages"])
    D.apply(d, "add_page", {"after": 1, "copy_of": 3})
    assert len(d["pages"]) == n + 1
    f = D.apply(d, "add_frame", {"page": 2, "kind": "text", "x": 1, "y": 1, "w": 3, "h": 1, "text": "Quokkaword {{dome.long_in}}"})["frame"]
    D.apply(d, "update_frame", {"frame": f, "style": "verse", "x": 2})
    assert D.apply(d, "find_replace", {"find": "Quokkaword", "replace": "Hi"})["replaced"] == 1
    D.apply(d, "delete_page", {"page": 2})
    assert len(d["pages"]) == n
    for bad in ({"frame": "nope", "x": 1}, {"frame": f, "style": "no-such-style"}):
        try:
            D.apply(d, "update_frame", bad)
            raise AssertionError(f"should have refused {bad}")
        except ValueError:
            pass
    html = D.render_html(d)
    assert html.count('class="page"') == n
    clean = lib.clean_svg('<svg viewBox="0 0 10 10"><script>alert(1)</script><rect onclick="x()" width="5" height="5" href="http://x"/></svg>')
    assert "script" not in clean and "onclick" not in clean and "http://x" not in clean, clean
    print("books.studio selftest OK")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="books.studio", description="The Book Studio: lay out, illustrate and edit the books.")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--no-browser", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return 0
    from books.composer import server
    httpd = server.serve(a.port, browser=False)
    url = f"http://127.0.0.1:{httpd.server_address[1]}/studio"
    print(f"The Book Studio is at {url}  (Ctrl+C to stop)")
    if not a.no_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0
