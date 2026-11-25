"""Build the technical report: docs/report/EarIQ_Technical_Report.md -> .pdf (via Chrome) and .docx (via pandoc)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pypandoc

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "docs/report/EarIQ_Technical_Report.md"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
CSS = """
@page { size: A4; margin: 18mm 17mm 18mm 17mm; }
body { font-family: Inter, -apple-system, "Segoe UI", Roboto, sans-serif; color: #10152a; font-size: 10.4pt; line-height: 1.5; }
h1 { font-size: 21pt; letter-spacing: -.02em; margin: 0 0 4pt; page-break-before: always; }
h1:first-of-type { page-break-before: avoid; }
h1.title { display: none; }
h2 { font-size: 14pt; margin: 18pt 0 6pt; letter-spacing: -.01em; color: #2b2f8f; }
h3 { font-size: 11.5pt; margin: 12pt 0 4pt; }
p { margin: 5pt 0; }
table { border-collapse: collapse; width: 100%; margin: 8pt 0 10pt; font-size: 9.2pt; page-break-inside: avoid; }
th { background: #f0eeff; color: #2b2f8f; text-align: left; padding: 5pt 6pt; border-bottom: 1.5pt solid #c9c2ff; }
td { padding: 4pt 6pt; border-bottom: .5pt solid #e5e7f0; vertical-align: top; }
img { max-width: 100%; display: block; margin: 8pt auto; page-break-inside: avoid; }
figure { margin: 8pt 0; page-break-inside: avoid; }
figcaption { font-size: 8.8pt; color: #6b7290; text-align: center; }
code { font-family: Menlo, monospace; font-size: 8.8pt; background: #f4f5f9; padding: 0 3pt; border-radius: 3pt; }
pre { background: #f4f5f9; padding: 8pt; border-radius: 6pt; font-size: 8.4pt; white-space: pre-wrap; page-break-inside: avoid; }
blockquote { border-left: 3pt solid #5b4cf0; margin: 8pt 0; padding: 4pt 10pt; background: #f7f6ff; color: #2b2f55; }
.cover { height: 250mm; display: flex; flex-direction: column; justify-content: center; }
.cover .tag { color: #5b4cf0; font-weight: 700; font-size: 11pt; }
.cover h1 { font-size: 34pt; page-break-before: avoid; margin: 8pt 0; }
.cover .sub { font-size: 14pt; color: #4a5270; }
.cover .meta { margin-top: 30pt; font-size: 10.5pt; line-height: 1.8; }
"""


def main():
    html = pypandoc.convert_file(str(SRC), "html5", extra_args=["--standalone", "--metadata", "title=EarIQ Technical Report",
                                                              f"--resource-path={SRC.parent}"])
    html = html.replace("</head>", f"<style>{CSS}</style></head>")
    out_html = SRC.with_suffix(".html")
    out_html.write_text(html, encoding="utf-8")
    pdf = SRC.with_suffix(".pdf")
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf}", out_html.as_uri()], check=True, capture_output=True)
    pypandoc.convert_file(str(SRC), "docx", outputfile=str(SRC.with_suffix(".docx")),
                          extra_args=[f"--resource-path={SRC.parent}"])
    out_html.unlink()
    print("wrote", pdf, SRC.with_suffix(".docx"))


if __name__ == "__main__":
    main()
