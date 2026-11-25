"""Check every decimal number in paper_v2_en.md against the logs and tables it was typed from.

A paper number with d decimals passes if some number in a source file rounds to it at d decimals (absolute values;
half-up or half-even). Integers with thousands separators (event counts) are checked the same way with d = 0.
Numbers that do not pass are listed for a manual look (dates, section numbers, thresholds and definitions are expected).
Run: python check_numbers.py
"""
import re
from decimal import ROUND_HALF_EVEN, ROUND_HALF_UP, Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
LOGS = REPO / "docs" / "v2" / "logs"
SOURCES = sorted(LOGS.rglob("*.txt")) + [REPO / "docs" / "v2" / n for n in ("SEARCH_LOG.md", "CANDIDATES.md")]
SOURCES += [HERE / "make_tables.log.txt"] + sorted((HERE / "tables").glob("*.csv"))
SOURCES += [HERE.parent / "archive_v1" / "paper_v1_en.md"]          # numbers quoted from the earlier version (Appendix B)
NUM = re.compile(r"(?<![\w.])[-+−]?\d[\d,]*\.?\d*(?:e[-+]?\d+)?", re.I)


def norm(s):
    return s.replace("−", "-").replace(",", "").rstrip(".")


src = set()
for f in SOURCES:
    for m in NUM.findall(f.read_text(encoding="utf-8", errors="replace")):
        try:
            x = abs(Decimal(norm(m)))
            if x < Decimal(10) ** 12:          # skip hashes and other long digit strings in the logs
                src.add(x)
        except Exception:
            pass
rounded = {}
for d in (0, 1, 2, 3):
    q = Decimal(1).scaleb(-d)
    rounded[d] = {x.quantize(q, rounding=r) for x in src for r in (ROUND_HALF_UP, ROUND_HALF_EVEN)}

text = (HERE.parent / "paper_v2_en.md").read_text(encoding="utf-8")
body = text.split("# References")[0] + text.split(":::")[-1]
missing, total = [], 0
for line_no, line in enumerate(body.split("\n"), 1):
    for m in NUM.finditer(line):
        tok = norm(m.group(0))
        if not re.search(r"\d", tok):
            continue
        dec = len(tok.split(".")[1]) if "." in tok else 0
        if dec == 0 and "," not in m.group(0):
            continue                      # plain integers (years, section numbers, counts below 1,000) are not checked
        total += 1
        if abs(Decimal(tok)) not in rounded[min(dec, 3)]:
            missing.append((line_no, m.group(0), line.strip()[:110]))
print(f"numbers checked: {total}; not found in the sources: {len(missing)}")
for ln, tok, ctx in missing:
    print(f"  line {ln}: {tok}   | {ctx}")
