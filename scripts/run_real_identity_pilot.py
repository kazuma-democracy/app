from __future__ import annotations

import csv
import hashlib
import http.cookiejar
import io
import json
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from wa_commons.identity.enrich import enrich_entity_batch, strong_id
from wa_commons.identity.jpx import from_jpx_row
from wa_commons.identity.jpx_snapshot import domestic_company_rows, read_jpx_rows
from wa_commons.identity.models import SourceRef

JPX_URL = "https://www.jpx.co.jp/markets/statistics-equities/misc/tvdivq0000001vg2-att/data_j.xls"
EDINET_URL = "https://disclosure2dl.edinet-fsa.go.jp/searchdocument/codelist/Edinetcode.zip"
NTA_PAGE = "https://www.houjin-bangou.nta.go.jp/download/zenken/index.html"
GLEIF_API = "https://api.gleif.org/api/v1/lei-records"
NTA_TOKEN_FIELD = "jp.go.nta.houjin_bangou.framework.web.common.CNSFWTokenProcessor.request.token"


def download(url: str, path: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "wa-commons-m1/0.1"})
    with urllib.request.urlopen(req, timeout=600) as resp, path.open("wb") as out:
        print(f"download {url} -> {resp.geturl()} [{resp.headers.get('Content-Type', '')}]")
        while chunk := resp.read(1024 * 1024):
            out.write(chunk)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while chunk := fh.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def read_edinet_zip(path: Path) -> list[dict[str, str]]:
    """Read the official EDINET code list.

    The first CSV row is download metadata and the second row is the actual header.
    """
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not names:
            raise RuntimeError("EDINET code-list zip contained no CSV")
        raw = zf.read(names[0])
    text = None
    for enc in ("cp932", "utf-8-sig", "utf-8"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if text is None:
        raise RuntimeError("could not decode EDINET code-list CSV")
    rows = list(csv.reader(io.StringIO(text)))
    if len(rows) < 3:
        raise RuntimeError("EDINET code list did not contain metadata + header + data")
    header = rows[1]
    return [dict(zip(header, row)) for row in rows[2:] if row]


def nta_download_unicode_full(path: Path) -> tuple[str, str]:
    """Download the nationwide Unicode CSV ZIP using NTA's official form POST."""
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    req = urllib.request.Request(NTA_PAGE, headers={"User-Agent": "wa-commons-m1/0.1"})
    with opener.open(req, timeout=60) as resp:
        html = resp.read().decode("utf-8", errors="ignore")

    token_match = re.search(re.escape(NTA_TOKEN_FIELD) + r'"\s+value="([^"]+)"', html)
    if not token_match:
        raise RuntimeError("NTA CSRF token not found")
    section_match = re.search(r'id="csv-unicode".*?id="xml-unicode"', html, re.DOTALL)
    if not section_match:
        raise RuntimeError("NTA CSV Unicode section not found")
    file_match = re.search(r"doDownload\((\d+)\)", section_match.group(0))
    if not file_match:
        raise RuntimeError("NTA nationwide Unicode file number not found")
    file_no = file_match.group(1)

    data = urllib.parse.urlencode(
        {NTA_TOKEN_FIELD: token_match.group(1), "event": "download", "selDlFileNo": file_no}
    ).encode("utf-8")
    post = urllib.request.Request(
        NTA_PAGE,
        data=data,
        headers={"User-Agent": "wa-commons-m1/0.1"},
        method="POST",
    )
    with opener.open(post, timeout=1800) as resp, path.open("wb") as out:
        print(f"NTA POST file_no={file_no} [{resp.headers.get('Content-Type', '')}]")
        while chunk := resp.read(1024 * 1024):
            out.write(chunk)
    if not zipfile.is_zipfile(path):
        raise RuntimeError(f"NTA POST did not return a ZIP (file_no={file_no})")
    return file_no, NTA_PAGE


def nta_rows_for_targets(zip_path: Path, targets: set[str]) -> list[dict[str, str]]:
    """Stream the full official NTA dataset and retain only requested corporate numbers."""
    found: dict[str, dict[str, str]] = {}
    if not targets:
        return []
    with zipfile.ZipFile(zip_path) as zf:
        csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
        if not csv_names:
            raise RuntimeError("NTA ZIP contained no CSV")
        for name in csv_names:
            with zf.open(name) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
                for row in csv.reader(text):
                    if len(row) < 12:
                        continue
                    number = row[1].strip()
                    if number not in targets:
                        continue
                    found[number] = {
                        "法人番号": number,
                        "商号又は名称": row[6].strip(),
                        "国内所在地（都道府県市区町村）": "".join(x.strip() for x in row[9:12]),
                    }
                    if len(found) == len(targets):
                        return list(found.values())
    return list(found.values())


def read_gleif_golden_copy_zip(zip_path: Path, targets: set[str]) -> list[dict[str, str]]:
    """Read Level 1 Golden Copy CSV rows by exact Japanese registration ID."""
    if not targets:
        return []
    output: list[dict[str, str]] = []
    authority_key = "Entity.RegistrationAuthority.RegistrationAuthorityID"
    entity_id_key = "Entity.RegistrationAuthority.RegistrationAuthorityEntityID"
    with zipfile.ZipFile(zip_path) as zf:
        csv_names = [name for name in zf.namelist() if name.lower().endswith(".csv")]
        if not csv_names:
            raise RuntimeError("GLEIF Golden Copy ZIP contained no CSV")
        for name in csv_names:
            with zf.open(name) as raw:
                text = io.TextIOWrapper(raw, encoding="utf-8-sig", newline="")
                for row in csv.DictReader(text):
                    number = str(row.get(entity_id_key, "")).strip()
                    authority = str(row.get(authority_key, "")).strip()
                    lei = str(row.get("LEI", "")).strip()
                    if authority != "RA001075" or number not in targets or not lei:
                        continue
                    output.append(
                        {
                            "LEI": lei,
                            authority_key: authority,
                            entity_id_key: number,
                        }
                    )
    return output


def gleif_rows_for_targets(targets: set[str]) -> list[dict[str, str]]:
    """Resolve LEIs only by exact Japanese corporate-number registration IDs."""
    out: list[dict[str, str]] = []
    for number in sorted(targets):
        query = urllib.parse.urlencode({"filter[entity.registeredAs]": number})
        req = urllib.request.Request(
            f"{GLEIF_API}?{query}",
            headers={"User-Agent": "wa-commons-m1/0.1", "Accept": "application/vnd.api+json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                payload = json.load(resp)
        except Exception as exc:
            print(f"GLEIF lookup failed for {number}: {exc}")
            continue
        matches = []
        for item in payload.get("data", []):
            attrs = item.get("attributes", {})
            entity = attrs.get("entity", {})
            authority = entity.get("registrationAuthority", {})
            if entity.get("registeredAs") == number and authority.get("id") == "RA001075":
                lei = attrs.get("lei") or item.get("id")
                if lei:
                    matches.append(lei)
        if len(set(matches)) == 1:
            out.append(
                {
                    "LEI": matches[0],
                    "Entity.RegistrationAuthority.RegistrationAuthorityEntityID": number,
                }
            )
    return out


def semantic_payload(entities: list[dict]) -> list[dict]:
    """Remove run-time retrieval timestamps before reproducibility hashing."""
    payload = json.loads(json.dumps(entities, ensure_ascii=False))
    for entity in payload:
        for identifier in entity.get("identifiers", []):
            source = identifier.get("source", {})
            source.pop("retrieved_at", None)
    return payload


def main(out_dir: str) -> None:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    jpx_path = out / "jpx_data_j.xls"
    edinet_zip = out / "Edinetcode.zip"
    nta_zip = out / "nta_all_unicode.zip"
    download(JPX_URL, jpx_path)
    download(EDINET_URL, edinet_zip)

    jpx_rows = sorted(
        domestic_company_rows(read_jpx_rows(jpx_path)),
        key=lambda r: str(r.get("コード", "")),
    )[:100]
    if len(jpx_rows) != 100:
        raise RuntimeError(f"expected 100 domestic JPX issuers, got {len(jpx_rows)}")

    jpx_snapshot = str(int(float(jpx_rows[0]["日付"])))
    jpx_source = SourceRef("JPX", jpx_path.name, jpx_snapshot, JPX_URL, now, "0.3")
    entities = [from_jpx_row(row, jpx_source) for row in jpx_rows]

    edinet_rows = read_edinet_zip(edinet_zip)
    edinet_source = SourceRef("EDINET", edinet_zip.name, "2026-08-21", EDINET_URL, now, "0.3")
    entities = enrich_entity_batch(entities, edinet_rows=edinet_rows, edinet_source=edinet_source)
    corp_numbers = {n for e in entities if (n := strong_id(e, "JP_CORPORATE_NUMBER"))}
    print(f"EDINET matched {len(corp_numbers)} corporate numbers for 100 issuers")

    nta_file_no, nta_url = nta_download_unicode_full(nta_zip)
    nta_rows = nta_rows_for_targets(nta_zip, corp_numbers)
    nta_source = SourceRef("NTA", f"file_no:{nta_file_no}", "2026-07-31", nta_url, now, "0.2")

    gleif_rows = gleif_rows_for_targets(corp_numbers)
    gleif_source = SourceRef("GLEIF", "api-v1", "2026-08-21", GLEIF_API, now, "0.2")
    entities = enrich_entity_batch(
        entities,
        edinet_rows=edinet_rows,
        edinet_source=edinet_source,
        nta_rows=nta_rows,
        nta_source=nta_source,
        gleif_rows=gleif_rows,
        gleif_source=gleif_source,
    )

    def has(entity, scheme: str) -> bool:
        return strong_id(entity, scheme) is not None

    canonical = [e.to_dict() for e in entities]
    semantic = semantic_payload(canonical)
    stable_blob = json.dumps(semantic, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    report = {
        "generated_at": now,
        "jpx_snapshot": jpx_snapshot,
        "entity_count": len(entities),
        "edinet_count": sum(has(e, "EDINET_CODE") for e in entities),
        "corporate_number_count": sum(has(e, "JP_CORPORATE_NUMBER") for e in entities),
        "nta_validated_count": len({r["法人番号"] for r in nta_rows}),
        "lei_count": sum(has(e, "LEI") for e in entities),
        "disputed_count": sum(e.review_state == "DISPUTED" for e in entities),
        "unresolved_corporate_number_count": sum(not has(e, "JP_CORPORATE_NUMBER") for e in entities),
        "semantic_payload_sha256": hashlib.sha256(stable_blob).hexdigest(),
        "sources": {
            "jpx": {"url": JPX_URL, "sha256": sha256(jpx_path)},
            "edinet": {"url": EDINET_URL, "sha256": sha256(edinet_zip)},
            "nta": {"url": nta_url, "file_no": nta_file_no, "sha256": sha256(nta_zip)},
            "gleif": {"url": GLEIF_API, "registration_authority": "RA001075"},
        },
    }
    (out / "entities.json").write_text(json.dumps(canonical, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))

    if report["entity_count"] != 100:
        raise RuntimeError("pilot did not contain exactly 100 entities")
    if report["corporate_number_count"] < 90:
        raise RuntimeError(f"corporate-number coverage unexpectedly low: {report['corporate_number_count']}")
    if report["nta_validated_count"] != report["corporate_number_count"]:
        raise RuntimeError(
            f"NTA validation incomplete: {report['nta_validated_count']}/{report['corporate_number_count']}"
        )


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "artifacts/real-identity-pilot")
