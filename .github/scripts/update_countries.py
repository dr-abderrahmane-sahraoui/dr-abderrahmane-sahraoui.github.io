"""Refresh data/countries.json from the site's public Flag Counter page."""
import datetime
import html
import json
import pathlib
import re
import sys
import urllib.request

URL = "https://s05.flagcounter.com/countries/DqDd/"
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else "data/countries.json")


def fetch():
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", "replace")


def parse(page):
    found = {}
    for row in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S | re.I):
        code = re.search(r"expand_country\((?:&quot;|\")([a-z]{2})(?:&quot;|\")\)", row)
        if not code:
            continue
        cells = [html.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                 for c in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S | re.I)]
        count = next((c for c in cells if re.fullmatch(r"\d[\d,]*", c)), None)
        if count:
            found[code.group(1)] = int(count.replace(",", ""))
    return found


def main():
    try:
        counts = parse(fetch())
    except Exception as e:
        print("Could not read the counter, keeping current data:", e)
        return
    if not counts:
        print("No countries found, keeping current data.")
        return
    countries = [{"code": c, "visitors": v}
                 for c, v in sorted(counts.items(), key=lambda x: (-x[1], x[0]))]
    try:
        old = json.loads(OUT.read_text(encoding="utf-8")).get("countries", [])
    except (OSError, ValueError):
        old = []
    if sorted(old, key=lambda x: x["code"]) == sorted(countries, key=lambda x: x["code"]):
        print("No change.")
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    OUT.write_text(json.dumps({"updated": now, "countries": countries}, ensure_ascii=False, indent=1) + "\n",
                   encoding="utf-8")
    print("Updated:", countries)


if __name__ == "__main__":
    main()
