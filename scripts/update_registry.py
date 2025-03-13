#!/usr/bin/env python3
import json
import sys
import requests
import toml
import subprocess

FIELDS_TO_COPY = [
    "name",
    "version",
    "status",
    "description",
    "license",
    "author",
    "repository",
    "homepage",
    "entry",
    "keywords",
    "categories"
]

def main(pr_registry_path):
    # 1. Load the PR registry.json
    with open(pr_registry_path, "r", encoding="utf-8") as f:
        registry_data = json.load(f)

    packages = registry_data.get("packages", [])
    new_package = packages[-1]  # The newly appended package
    repo_url = new_package["repository"]

    # 2. Fetch sop.toml again
    raw_url = repo_url.replace("github.com", "raw.githubusercontent.com").rstrip("/") + "/main/sop.toml"
    response = requests.get(raw_url)
    response.raise_for_status()  # throws an error if not 200
    sop_data = toml.loads(response.text)
    package_info = sop_data.get("package", {})

    # 3. Overwrite fields in new_package with data from sop.toml
    for field in FIELDS_TO_COPY:
        if field in package_info:
            new_package[field] = package_info[field]

    # Reassign updated package
    packages[-1] = new_package
    registry_data["packages"] = packages

    # 4. Write updated registry.json
    with open(pr_registry_path, "w", encoding="utf-8") as f:
        json.dump(registry_data, f, indent=2)

    # 5. Build dynamic commit message using the new package's "name"
    package_name = package_info.get("name", "unknown-package")
    commit_message = f"feat: add validated package '{package_name}'"

    # 6. Commit & push changes
    subprocess.run(["git", "config", "user.name", "soplang-bot"], check=True)
    subprocess.run(["git", "config", "user.email", "actions@soplang.org"], check=True)
    subprocess.run(["git", "add", pr_registry_path], check=True)
    subprocess.run(["git", "commit", "-m", commit_message], check=True)
    subprocess.run(["git", "push"], check=True)

    print(f"update_registry.py: registry.json updated and committed with message: '{commit_message}'")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python update_registry.py <pr_registry.json>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1])
