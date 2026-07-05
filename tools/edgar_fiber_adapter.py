#!/usr/bin/env python3
"""SP-ADAPT-TREE-001, real edition: turn a live SEC 10-K into a Crystal Atlas fiber fragment.

Fetches a company's latest 10-K from EDGAR, extracts its Item-level table of contents (the
document tree `descend` navigates), and emits a fragment `fiber_projection.project` consumes —
document root ⊑ Item sections, with the registrant as an anchored entity under Item 1. This is
what moves fibered retrieval from fixtures onto real documents; no model or datastore needed.

Honesty: the Item extractor is a heuristic over the filing HTML (strip tags → match
`Item N. Title` headings, dedup). It reliably recovers the standard Part I–IV items but is not a
production-grade parser (messy filings, exhibits, XBRL R-files are out of scope). It emits ONLY
what the filing structurally states — no ownership percentages or subsidiary edges are invented;
cross-fiber ownership (Exhibit 21 → GLEIF → E_R) is the documented follow-up.

Network only in the fetch path; parsing + fragment emission are pure and offline-testable.

    python3 tools/edgar_fiber_adapter.py --cik 320193 --out aapl.fragment.json   # live fetch
    python3 tools/edgar_fiber_adapter.py --html saved.htm --cik 320193 --company "Apple Inc."
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request

_UA = "SocioProphet fibered-retrieval research contact@socioprophet.com"
_ITEM = re.compile(
    r"Item\s+(\d+[A-Z]?)\.\s+([A-Za-z][A-Za-z ,\-&/]+?)(?=\s+\d|\s+Item\b|\s+Part\b)"
)


def _get(url: str, accept_json: bool = False) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (fixed SEC hosts)
        return resp.read().decode("utf-8", errors="replace")


def latest_10k(cik: str) -> dict:
    """Resolve the most recent 10-K's primary-document URL + metadata via data.sec.gov."""
    cik10 = str(cik).zfill(10)
    data = json.loads(_get(f"https://data.sec.gov/submissions/CIK{cik10}.json"))
    company = data.get("name", "")
    r = data["filings"]["recent"]
    for i, form in enumerate(r["form"]):
        if form == "10-K":
            acc_nodash = r["accessionNumber"][i].replace("-", "")
            doc = r["primaryDocument"][i]
            return {
                "cik": str(int(cik)),
                "company": company,
                "accession": r["accessionNumber"][i],
                "filing_date": r["filingDate"][i],
                "url": f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc_nodash}/{doc}",
            }
    raise LookupError(f"no 10-K found for CIK {cik}")


def _text(html: str) -> str:
    t = re.sub(r"<[^>]+>", " ", html)
    t = re.sub(r"&#160;|&nbsp;|&#821[6789];|&#822[01];|&amp;", " ", t)
    return re.sub(r"\s+", " ", t)


def extract_items(html: str) -> list[tuple[str, str]]:
    """Extract `(item_id, title)` pairs from a 10-K, first clean occurrence wins, in order."""
    seen: dict[str, str] = {}
    for m in _ITEM.finditer(_text(html)):
        iid, title = m.group(1), m.group(2).strip()
        if iid not in seen and 3 <= len(title) <= 70:
            seen[iid] = title
    return list(seen.items())


def _node(node_id, kind, display, *, attrs=None, anchor=None, source=None):
    entry = {
        "graph_node": {
            "node_id": node_id, "tenant_id": "edgar", "node_kind": kind,
            "display_name": display,
        }
    }
    if attrs:
        entry["graph_node"]["attributes"] = attrs
    entry["confidentiality_class"] = "public"  # SEC filings are public
    if anchor:
        entry["evidence"] = {
            "evidence_id": f"ev-{node_id}", "tenant_id": "edgar", "source_ref": source or node_id,
            "anchor_ref": anchor,
        }
    return entry


def to_fragment(meta: dict, items: list[tuple[str, str]]) -> dict:
    """Build a Crystal Atlas fiber fragment: document root ⊑ Item sections; the registrant is an
    anchored organization under Item 1 (Business)."""
    cik, company, url = meta["cik"], meta["company"], meta["url"]
    root = f"{cik}/10-K"
    nodes = [_node(root, "document", f"{company} — Form 10-K ({meta['filing_date']})")]
    edges = []
    item1 = None
    for iid, title in items:
        nid = f"{cik}/item-{iid}"
        if iid == "1":
            item1 = nid
        nodes.append(_node(nid, "clause", f"Item {iid} — {title}"))
        edges.append({"class": "containment", "parent": root, "child": nid})
    entity = f"entity/{cik}"
    nodes.append(_node(
        entity, "organization", company,
        attrs={"cik": cik},
        anchor=f"{url}#item-1", source=meta["accession"],
    ))
    # the registrant is described in Item 1 (Business); fall back to the document root.
    edges.append({"class": "containment", "parent": item1 or root, "child": entity})
    return {"tenant_id": "edgar", "_source": url, "nodes": nodes, "edges": edges}


def build(cik: str, html: str | None = None, company: str | None = None) -> dict:
    if html is not None:
        meta = {"cik": str(int(cik)), "company": company or f"CIK {int(cik)}",
                "accession": "local", "filing_date": "", "url": "local"}
    else:
        meta = latest_10k(cik)
        html = _get(meta["url"])
    return to_fragment(meta, extract_items(html))


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Emit a Crystal Atlas fiber fragment from a 10-K.")
    p.add_argument("--cik", required=True, help="SEC CIK (e.g. 320193 for Apple).")
    p.add_argument("--html", help="Parse a local filing HTML file instead of fetching (offline).")
    p.add_argument("--company", help="Company name when using --html.")
    p.add_argument("--out", help="Write the fragment JSON here (default: stdout).")
    args = p.parse_args(argv)
    html = open(args.html, encoding="utf-8", errors="replace").read() if args.html else None
    fragment = build(args.cik, html=html, company=args.company)
    text = json.dumps(fragment, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"wrote {args.out}: {len(fragment['nodes'])} nodes, {len(fragment['edges'])} edges",
              file=sys.stderr)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
