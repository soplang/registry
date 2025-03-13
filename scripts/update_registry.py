#!/usr/bin/env python3
import json
import sys
import requests
import toml
import subprocess
import os

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


def main():
    """
    Updates registry.json with complete metadata from the package's sop.toml
    and commits the changes with a dynamic message.
    """
    pr_registry_path = "registry.json"

    # 1. Load registry.json
    with open(pr_registry_path, "r", encoding="utf-8") as f:
        registry_data = json.load(f)

    packages = registry_data.get("packages", [])
    if not packages:
        print("Error: No packages found in registry.json", file=sys.stderr)
        sys.exit(1)

    new_package = packages[-1]  # The newly added package
    repo_url = new_package["repository"]

    # 2. Fetch sop.toml again
    raw_url = repo_url.replace(
        "github.com", "raw.githubusercontent.com").rstrip("/") + "/main/sop.toml"
    try:
        response = requests.get(raw_url)
        response.raise_for_status()
        sop_data = toml.loads(response.text)
    except Exception as e:
        print(f"Error fetching or parsing sop.toml: {e}", file=sys.stderr)
        sys.exit(1)

    package_info = sop_data.get("package", {})

    # 3. Overwrite fields in new_package with validated data from sop.toml
    for field in FIELDS_TO_COPY:
        if field in package_info:
            new_package[field] = package_info[field]

    # 4. Update the last entry in the packages list
    packages[-1] = new_package
    registry_data["packages"] = packages

    # 5. Save the updated registry.json
    with open(pr_registry_path, "w", encoding="utf-8") as f:
        json.dump(registry_data, f, indent=2)

    # 6. Dynamic commit message using the package name
    package_name = package_info.get("name", "unknown-package")
    commit_message = f"feat: add validated package '{package_name}'"

    # 7. Get GitHub PAT for authentication
    pat = os.getenv("GH_PAT")
    if not pat:
        print("❌ Error: GH_PAT environment variable is not set.", file=sys.stderr)
        sys.exit(1)

    # 8. Configure Git with the PAT
    subprocess.run(["git", "config", "user.name", "soplang-bot"], check=True)
    subprocess.run(["git", "config", "user.email",
                   "actions@soplang.org"], check=True)

    # Use the repository URL from the GitHub environment if available
    repo_url = os.getenv("GITHUB_REPOSITORY", "soplang/registry")
    subprocess.run(["git", "remote", "set-url", "origin",
                   f"https://x-access-token:{pat}@github.com/{repo_url}.git"], check=True)

    # 9. Add, commit, and push changes to the PR branch
    subprocess.run(["git", "add", pr_registry_path], check=True)
    subprocess.run(["git", "commit", "-m", commit_message], check=True)

    # Detect PR branch dynamically
    branch_name = subprocess.check_output(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"]).strip().decode()
    subprocess.run(["git", "push", "origin", branch_name], check=True)

    print(
        f"✅ Successfully updated {pr_registry_path} and committed: '{commit_message}'")


if __name__ == "__main__":
    main()
