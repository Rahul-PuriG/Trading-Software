"""Download linked journal charts locally without Excel or extra packages."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
      "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships"}
REL = "http://schemas.openxmlformats.org/package/2006/relationships"


def workbook_links(path):
    with ZipFile(path) as z:
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            strings = ["".join(n.itertext()) for si in ET.fromstring(z.read("xl/sharedStrings.xml"))
                       for n in [si]]
        book = ET.fromstring(z.read("xl/workbook.xml"))
        relationships = {r.attrib["Id"]: r.attrib["Target"]
                         for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        sheet = next(s for s in book.findall("m:sheets/m:sheet", NS)
                     if s.attrib["name"].lower() == "trades")
        target = relationships[sheet.attrib[f"{{{NS['r']}}}id"]]
        sheet_path = target.lstrip("/") if target.startswith("/") else "xl/" + target
        root = ET.fromstring(z.read(sheet_path))
        hyperlinks = {}
        rel_path = str(Path(sheet_path).parent / "_rels" / (Path(sheet_path).name + ".rels")).replace("\\", "/")
        if rel_path in z.namelist():
            rels = {r.attrib["Id"]: r.attrib["Target"] for r in ET.fromstring(z.read(rel_path))}
            for link in root.findall("m:hyperlinks/m:hyperlink", NS):
                hyperlinks[link.attrib["ref"]] = rels.get(link.attrib.get(f"{{{NS['r']}}}id"), "")
        def value(cell):
            if cell is None:
                return ""
            if cell.attrib.get("t") == "inlineStr":
                return "".join(cell.find("m:is", NS).itertext())
            v = cell.find("m:v", NS)
            text = v.text if v is not None and v.text else ""
            return strings[int(text)] if cell.attrib.get("t") == "s" and text else text
        records = []
        for row in root.findall("m:sheetData/m:row", NS):
            number = int(row.attrib["r"])
            if number < 3:
                continue
            cells = {re.sub(r"\d+", "", c.attrib["r"]): c for c in row.findall("m:c", NS)}
            if not value(cells.get("A")):
                continue
            for column, label in [("P", "daily_4h"), ("Q", "one_hour"), ("R", "entry_15min")]:
                url = hyperlinks.get(f"{column}{number}") or value(cells.get(column))
                if url.startswith(("https://", "http://")):
                    records.append({"workbook": path.name, "row": number,
                                    "timeframe": label, "source_url": url})
        return records


class ImageMetadata(HTMLParser):
    def __init__(self):
        super().__init__()
        self.image = None

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "meta" and (data.get("property") or data.get("name")) in ("og:image", "twitter:image"):
            self.image = self.image or data.get("content")


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(10 * 1024 * 1024 + 1)
        if len(data) > 10 * 1024 * 1024:
            raise ValueError("Response exceeds 10 MiB")
        return data, response.headers.get("Content-Type", ""), response.url


def image_extension(data):
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    raise ValueError("Response was not a supported chart image")


def download(record, folder):
    result = dict(record)
    try:
        data, content_type, final_url = fetch(record["source_url"])
        if "html" in content_type or data.lstrip().startswith((b"<!DOCTYPE", b"<html")):
            parser = ImageMetadata()
            parser.feed(data.decode("utf-8", errors="replace"))
            if not parser.image:
                raise ValueError("Page has no downloadable image metadata")
            data, _, final_url = fetch(urllib.parse.urljoin(final_url, parser.image))
        extension = image_extension(data)
        stem = re.sub(r"[^a-zA-Z0-9_-]", "_", Path(record["workbook"]).stem)
        filename = f"{stem}_row{record['row']}_{record['timeframe']}{extension}"
        (folder / filename).write_bytes(data)
        result.update(status="downloaded", filename=filename, image_url=final_url)
    except Exception as exc:
        result.update(status="failed", error=f"{type(exc).__name__}: {exc}")
    return result


def package(results, folder):
    # Keep each package small enough for ordinary chat uploads. Include a manifest
    # in every part so images can be matched to the correct trade and timeframe.
    groups, group, size = [], [], 0
    for record in results:
        if record["status"] != "downloaded":
            continue
        length = (folder / record["filename"]).stat().st_size
        if group and size + length > 15 * 1024 * 1024:
            groups.append(group)
            group, size = [], 0
        group.append(record)
        size += length
    if group:
        groups.append(group)
    for index, records in enumerate(groups, 1):
        path = folder / f"journal_charts_part_{index:02d}.zip"
        with ZipFile(path, "w", ZIP_DEFLATED) as z:
            z.writestr("manifest.json", json.dumps(records, indent=2))
            for record in records:
                z.write(folder / record["filename"], record["filename"])
        print(f"Upload: {path}", flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input-dir", type=Path, default=Path.cwd())
    p.add_argument("--output", type=Path, default=Path.cwd() / "journal_charts")
    args = p.parse_args()
    files = sorted(args.input_dir.glob("Swing USDJPY Round *.xlsx"))
    if not files:
        p.exit(1, "No Swing USDJPY Round *.xlsx workbooks found in --input-dir\n")
    records = [r for path in files for r in workbook_links(path)]
    if not records:
        p.exit(1, "No chart links found\n")
    args.output.mkdir(parents=True, exist_ok=True)
    print(f"Found {len(records)} links in {len(files)} workbooks. No TWS connection or orders.", flush=True)
    results = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(lambda r: download(r, args.output), records):
            results.append(result)
            print(f"{len(results)}/{len(records)}: {result['status']} — {result['workbook']} row {result['row']} {result['timeframe']}", flush=True)
    (args.output / "download_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    package(results, args.output)
    count = sum(r["status"] == "downloaded" for r in results)
    print(f"Downloaded {count}/{len(records)}. Failures are listed in download_results.json.")
    return 0 if count == len(records) else 1


if __name__ == "__main__":
    raise SystemExit(main())
