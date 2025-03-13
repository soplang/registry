#!/usr/bin/env python3
import json
import sys

def main(base_registry_path, pr_registry_path):
    """
    Ensures the PR's registry.json is the same as base_registry.json
    except for exactly ONE new package appended to the 'packages' array,
    containing only 'repository'.
    """

    # 1. Load the base (main) registry.json
    with open(base_registry_path, "r", encoding="utf-8") as f:
        base_data = json.load(f)

    # 2. Load the PR's registry.json
    with open(pr_registry_path, "r", encoding="utf-8") as f:
        pr_data = json.load(f)

    if "packages" not in base_data or "packages" not in pr_data:
        print("Error: 'packages' array is missing in registry.json files.", file=sys.stderr)
        sys.exit(1)

    base_packages = base_data["packages"]
    pr_packages = pr_data["packages"]

    # 3. The PR must have exactly 1 additional package
    if len(pr_packages) != len(base_packages) + 1:
        print(
            f"Error: Exactly one new package must be appended. "
            f"Found a difference of {len(pr_packages) - len(base_packages)}.",
            file=sys.stderr
        )
        sys.exit(1)

    # 4. All existing packages in base must match exactly
    for i in range(len(base_packages)):
        if base_packages[i] != pr_packages[i]:
            print(f"Error: Existing package at index {i} was modified.", file=sys.stderr)
            sys.exit(1)

    # 5. The new package is appended at the end
    new_package = pr_packages[-1]

    # 6. The new package must ONLY have the 'repository' field
    allowed_fields = {"repository"}
    new_package_fields = set(new_package.keys())
    extra_fields = new_package_fields - allowed_fields
    if extra_fields:
        print(
            f"Error: New package has extra fields {extra_fields}. "
            f"Only {allowed_fields} is allowed at PR submission.",
            file=sys.stderr
        )
        sys.exit(1)

    # 7. Make sure "repository" is not empty
    repo_url = new_package.get("repository", "").strip()
    if not repo_url:
        print("Error: 'repository' field is empty or missing.", file=sys.stderr)
        sys.exit(1)

    print("verify_append.py: The PR correctly appends one new package with only the 'repository' field.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python verify_append.py <base_registry.json> <pr_registry.json>", file=sys.stderr)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
