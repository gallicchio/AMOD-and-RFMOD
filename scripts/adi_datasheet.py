#!/usr/bin/env python3
"""Download Analog Devices datasheets straight from their PDF store into ../datasheets/, with a pdftotext copy in
../docs/datasheets/txt/.

    python3 tools/adi_datasheet.py ad9238 ad9763_9765_9767 adl5511

The PDFs live at https://www.analog.com/media/en/technical-documentation/data-sheets/<name>.pdf and a plain
download works (Jason, 2026-10-08); the product pages that link to them refuse scripts (HTTP 403).  The name is the
datasheet's, not always the part's: the AD9767 is in ad9763_9765_9767.pdf, and AD9767.pdf is a 404.  Case does not
matter.  On a 404, ask Jason for the link he would click, and read the name off it."""
import os, sys, subprocess, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PDF_DIR = os.path.join(ROOT, "datasheets")
TXT_DIR = os.path.join(ROOT, "docs", "datasheets", "txt")
URL = "https://www.analog.com/media/en/technical-documentation/data-sheets/%s.pdf"


def fetch(name):
    name = name.lower().removesuffix(".pdf")
    url = URL % name
    req = urllib.request.Request(url, headers={"User-Agent": "Wget/1.21"})
    try:
        data = urllib.request.urlopen(req, timeout=60).read()
    except Exception as e:
        print("%s: %s -- %s (the datasheet may be filed under its family's name: ask for the link)" % (name, url, e))
        return False
    if not data.startswith(b"%PDF"):
        print("%s: %s did not return a PDF" % (name, url))
        return False
    os.makedirs(PDF_DIR, exist_ok=True); os.makedirs(TXT_DIR, exist_ok=True)
    pdf = os.path.join(PDF_DIR, name + ".pdf")
    open(pdf, "wb").write(data)
    txt = os.path.join(TXT_DIR, name + ".txt")
    subprocess.call(["pdftotext", "-layout", pdf, txt])
    print("%s: %d kB -> %s, %s" % (name, len(data) // 1024, os.path.relpath(pdf, ROOT), os.path.relpath(txt, ROOT)))
    return True


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    ok = [fetch(n) for n in sys.argv[1:]]
    sys.exit(0 if all(ok) else 1)
