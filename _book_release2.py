"""One-shot release build: markdown, html, pdf, outline. Versions, never overwrites."""
from two_v_demo import book_manuscript as bm
from two_v_demo import book_export as be

print("== markdown")
md = bm.export_markdown(strict=True)
print("  ", md)

print("== html")
html = be.export_html(strict=True)
print("  ", html.summary)

print("== pdf")
pdf = be.export_pdf(strict=True)
print("  ", pdf.summary)

print("== outline")
outline = bm.export_outline()
print("  ", outline)
print("DONE")
