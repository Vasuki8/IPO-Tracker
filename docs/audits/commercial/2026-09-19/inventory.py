"""Offline rights-scope inventory; stdout only, no collectors or canonical writes.

Run from the repository root with uv run --frozen python <this file>.
URL mentions include historical evidence and rejected proposals, not license grants.
"""
import ast
import hashlib
import importlib.metadata as metadata
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

BASE = "11a62c47f64506fb3fbccdec8ba7f88e43d8c468"
INPUTS = ["data/ipos.json", "data/ipos-summary.json", "data/pending_updates.json",
          "scripts/issuer_offer_registry.py", "scripts/run_priority_subscriptions_v3.py"]
PACKAGES = ["pypdf", "fonttools", "beautifulsoup4", "requests", "tzdata", "certifi",
            "charset-normalizer", "idna", "soupsieve", "typing-extensions", "urllib3"]
URL = re.compile(r"https?://[^\s\"'<>]+")


def strings(value, path=""):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from strings(item, path + "/" + str(key))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            yield from strings(item, path + "/" + str(i))
    elif isinstance(value, str):
        yield path, value


def main():
    inputs = []
    hosts = defaultdict(lambda: {"mentionsByFile": Counter(), "examples": set()})
    for name in INPUTS:
        raw = Path(name).read_bytes()
        # Bind this frozen research cohort to immutable input bytes.
        expected = subprocess.check_output(["git", "show", f"{BASE}:{name}"])
        if raw != expected:
            raise SystemExit(f"Input changed since assessed commit: {name}")
        text = raw.decode("utf-8")
        if name.endswith(".json"):
            values = strings(json.loads(text))
        else:
            values = ((f"line:{node.lineno}", node.value) for node in ast.walk(ast.parse(text))
                      if isinstance(node, ast.Constant) and isinstance(node.value, str))
        count = 0
        for path, value in values:
            for url in URL.findall(value):
                host = urlsplit(url).hostname
                if not host:
                    continue
                count += 1
                hosts[host]["mentionsByFile"][name] += 1
                hosts[host]["examples"].add((name, path, url))
        inputs.append({"path": name, "sha256": hashlib.sha256(raw).hexdigest(),
                       "bytes": len(raw), "urlMentions": count})
    packages = []
    for name in PACKAGES:
        try:
            dist = metadata.distribution(name)
        except metadata.PackageNotFoundError:
            packages.append({"name": name, "installed": False})
            continue
        notices = []
        for path in dist.files or []:
            if any(s in str(path).lower() for s in ("license", "copying", "notice")):
                raw = dist.locate_file(path).read_bytes()
                notices.append({"path": str(path), "bytes": len(raw),
                                "sha256": hashlib.sha256(raw).hexdigest()})
        packages.append({"name": name, "version": dist.version,
                         "licenseDeclaration": dist.metadata.get("License-Expression") or dist.metadata.get("License"),
                         "releaseUrl": f"https://pypi.org/project/{name}/{dist.version}/",
                         "notices": notices})
    master = json.loads(Path(INPUTS[0]).read_text(encoding="utf-8"))
    subscriptions = [{"id": row["id"], "status": row.get("status"),
                      "source": row.get("subscriptionSource"),
                      "sourceUrl": row.get("subscriptionSourceUrl")}
                     for row in master["ipos"] if "secondary" in row.get("subscriptionSource", "").lower()]
    report = {"formatVersion": 1, "assessedDateUtc": "2026-09-19", "baseCommit": BASE,
              "scope": "Exact named inputs only; URL mentions include history, notes and unresolved proposals. Host counts are not accepted-fact counts or rights clearance. Three examples per host; all counts retained.",
              "inputs": inputs, "uniqueHosts": len(hosts),
              "hosts": [{"host": h, "mentionsByFile": dict(sorted(v["mentionsByFile"].items())),
                         "examples": [{"file": f, "pointerOrLine": p, "url": u} for f, p, u in sorted(v["examples"])[:3]]}
                        for h, v in sorted(hosts.items())],
              "canonicalSecondarySubscriptionLabels": subscriptions,
              "software": packages}
    print(json.dumps(report, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()
