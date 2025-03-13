#!/usr/bin/env python3
import json
import sys
import requests
import toml

REQUIRED_FIELDS = [
    "name",
    "version",
    "status",
    "license",
    "author",
    "repository",
    "entry"
]

def main(pr_registry_path):
    """
    Load the new package's `repository` from the end of the PR's registry.json,
    fetch its sop.toml, and validate required fields + entry file existence.
    """
    # 1. Load the PR's registry.json
    with open(pr_registry_path, "r", encoding="utf-8") as f:
        pr_data = json.load(f)

    packages = pr_data.get("packages", [])
    if not packages:
        print("No packages found in registry.json", file=sys.stderr)
        sys.exit(1)

    # 2. The newly added package is at the end
    new_package = packages[-1]
    repo_url = new_package["repository"]

    # 3. Construct raw GitHub URL for sop.toml
    # e.g. https://raw.githubusercontent.com/<user>/<repo>/main/sop.toml
    raw_url = repo_url.replace("github.com", "raw.githubusercontent.com").rstrip("/") + "/main/sop.toml"

    # Fetch sop.toml
    response = requests.get(raw_url)
    if response.status_code != 200:
        print(f"Error fetching sop.toml from {raw_url}: HTTP {response.status_code}", file=sys.stderr)
        sys.exit(1)

    try:
        sop_data = toml.loads(response.text)
    except Exception as e:
        print(f"Error parsing sop.toml: {e}", file=sys.stderr)
        sys.exit(1)

    package_info = sop_data.get("package", {})

    # 4. Check required fields
    for field in REQUIRED_FIELDS:
        if field not in package_info:
            print(f"Missing required field '{field}' in sop.toml [package] section.", file=sys.stderr)
            sys.exit(1)

    # 5. Check that the entry file actually exists
    entry_path = package_info["entry"]
    # Transform raw URL from sop.toml to the entry file
    entry_url = raw_url.replace("sop.toml", entry_path.lstrip("/"))
    entry_resp = requests.get(entry_url)
    if entry_resp.status_code != 200:
        print(f"Entry file '{entry_path}' not found in the repository.", file=sys.stderr)
        sys.exit(1)

    print("validate_sop_toml.py: sop.toml validation passed successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python validate_sop_toml.py <pr_registry.json>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
