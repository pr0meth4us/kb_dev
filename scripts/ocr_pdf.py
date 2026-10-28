#!/usr/bin/env python3
"""OCR a PDF page by page with the local Khmer Document Parser API.

Follows the CLAUDE.md OCR lessons:
- one page at a time (split with qpdf), so the job can be resumed and every
  page gets a <!-- page N --> marker;
- a page is rendered to PNG first (pdftoppm -scale-to 2000), wrapped in a
  small one-page PDF and sent to /parse-pdf when the single-page PDF is over
  ~1 MB or larger than 1200 pt, because the server stalls on huge pages.
  Never send whole pages to /ocr-image: it recognises a single line only;
- only `full_text` is kept.

Usage:
  python3 scripts/ocr_pdf.py <input.pdf> <output.md> [--pages 1-5,9] [--note "..."]

Per-page results are cached in .ocr_cache/<pdf-md5>/ so a rerun skips pages
already done. Needs qpdf and pdftoppm (poppler), and the API at
http://localhost:8000 (check GET /health first).
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
import uuid

API = os.environ.get("KHMER_OCR_API", "http://localhost:8000")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIG_BYTES = 1_000_000
BIG_POINTS = 1200


def page_count(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("Pages:"):
            return int(line.split()[1])
    raise SystemExit(f"cannot read page count of {pdf}")


def page_size_points(pdf):
    out = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("Page size:"):
            parts = line.split()
            return float(parts[2]), float(parts[4])
    return 0.0, 0.0


def post_file(endpoint, field, path, content_type):
    boundary = uuid.uuid4().hex
    with open(path, "rb") as f:
        data = f.read()
    body = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; "
        f"filename=\"{os.path.basename(path)}\"\r\nContent-Type: {content_type}\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{API}{endpoint}", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read())


def ocr_page(pdf, n, tmp):
    single = os.path.join(tmp, f"p{n}.pdf")
    r = subprocess.run(["qpdf", pdf, "--pages", ".", str(n), "--", single], capture_output=True)
    if r.returncode not in (0, 3):  # 3 = success with warnings
        raise RuntimeError(r.stderr.decode()[:300])
    w, h = page_size_points(single)
    if os.path.getsize(single) > BIG_BYTES or max(w, h) > BIG_POINTS:
        # Render the page and wrap the image in a small one-page PDF. /ocr-image
        # is a single-LINE recogniser and returns garbage for a whole page, so
        # every page must go through /parse-pdf.
        from PIL import Image  # Pillow
        prefix = os.path.join(tmp, f"img{n}")
        subprocess.run(["pdftoppm", "-png", "-scale-to", "2000", "-singlefile", single, prefix], check=True)
        small = os.path.join(tmp, f"img{n}.pdf")
        Image.open(prefix + ".png").convert("RGB").save(small, "PDF", resolution=200)
        single = small
    res = post_file("/parse-pdf", "files", single, "application/pdf")
    return (res.get("full_text") or "").strip()


def parse_pages(spec, total):
    if not spec:
        return list(range(1, total + 1))
    pages = []
    for part in spec.split(","):
        if "-" in part:
            a, b = part.split("-")
            pages.extend(range(int(a), int(b) + 1))
        else:
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= total]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("out")
    ap.add_argument("--pages", default="")
    ap.add_argument("--note", default="")
    args = ap.parse_args()

    total = page_count(args.pdf)
    pages = parse_pages(args.pages, total)
    md5 = hashlib.md5(open(args.pdf, "rb").read()).hexdigest()
    cache = os.path.join(ROOT, ".ocr_cache", md5)
    os.makedirs(cache, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        for n in pages:
            cfile = os.path.join(cache, f"{n}.txt")
            if os.path.exists(cfile):
                continue
            t0 = time.time()
            try:
                text = ocr_page(args.pdf, n, tmp)
            except Exception as e:  # keep going; a rerun retries failed pages
                print(f"page {n}: FAILED {e}", file=sys.stderr)
                continue
            with open(cfile, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"page {n}/{total}: {len(text)} chars, {time.time() - t0:.1f}s", file=sys.stderr)

    parts = [
        f"<!-- OCR of {os.path.basename(args.pdf)} by the local Khmer Document Parser API "
        f"({API}), page by page, {time.strftime('%Y-%m-%d')}. Unreviewed: check figures "
        f"against the page images.{(' ' + args.note) if args.note else ''} -->",
        "",
    ]
    missing = []
    for n in pages:
        cfile = os.path.join(cache, f"{n}.txt")
        if not os.path.exists(cfile):
            missing.append(n)
            continue
        parts.append(f"<!-- page {n} -->")
        parts.append("")
        parts.append(open(cfile, encoding="utf-8").read())
        parts.append("")
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"wrote {args.out}: {len(pages) - len(missing)}/{len(pages)} pages"
          + (f"; missing {missing}" if missing else ""))


if __name__ == "__main__":
    main()
