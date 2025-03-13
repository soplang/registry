#!/usr/bin/env python3
"""
daily_check.py - Checks all packages in registry.json to verify they're still valid.

For each package, this script:
1. Attempts to fetch the package's sop.toml
2. Verifies the entry file exists
3. Compares remote metadata with local registry data
4. Sets package["valid"] = true/false based on results
5. Commits changes if any valid status changed
"""

import json
import sys
import requests
import toml
import subprocess
import os
from typing import Dict, Any, List, Set

# Fields to compare between registry.json and remote sop.toml
FIELDS_TO_COMPARE = [
    "name",
    "version",
    "status",
    "license",
    "author",
    "repository",
    "homepage",
    "entry",
    "keywords",
    "categories"
]


def fetch_sop_toml(repo_url: str) -> Dict[str, Any]:
    """Fetch and parse sop.toml from a repository URL."""
    raw_url = repo_url.replace(
        "github.com", "raw.githubusercontent.com").rstrip("/") + "/main/sop.toml"

    try:
        response = requests.get(raw_url)
        response.raise_for_status()
        return toml.loads(response.text)
    except Exception as e:
        print(f"Error fetching sop.toml from {raw_url}: {e}")
        return {}


def check_entry_file(repo_url: str, entry_path: str) -> bool:
    """Check if the entry file exists in the repository."""
    if not entry_path:
        return False

    raw_url = repo_url.replace("github.com", "raw.githubusercontent.com").rstrip(
        "/") + "/main/" + entry_path.lstrip("/")

    try:
        response = requests.get(raw_url)
        return response.status_code == 200
    except Exception:
        return False


def compare_metadata(registry_package: Dict[str, Any], sop_data: Dict[str, Any]) -> bool:
    """Compare metadata between registry.json and sop.toml."""
    if not sop_data or "package" not in sop_data:
        return False

    package_info = sop_data["package"]

    # Check each field that exists in both
    for field in FIELDS_TO_COMPARE:
        # Skip fields that don't exist in sop.toml
        if field not in package_info:
            continue

        # If field exists in registry but doesn't match sop.toml
        if field in registry_package and registry_package[field] != package_info[field]:
            print(
                f"Field '{field}' mismatch: registry has '{registry_package[field]}', sop.toml has '{package_info[field]}'")
            return False

    return True


def run_git_command(command, error_message=None):
    """Run a git command and handle errors gracefully."""
    try:
        result = subprocess.run(command, check=True,
                                capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        msg = error_message or f"Git command failed: {' '.join(command)}"
        print(f"❌ {msg}")
        print(f"Error details: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        return None


def main():
    """Main function to check all packages in registry.json."""
    registry_path = "registry.json"

    # Load registry.json
    try:
        with open(registry_path, "r", encoding="utf-8") as f:
            registry_data = json.load(f)
    except Exception as e:
        print(f"Error loading registry.json: {e}", file=sys.stderr)
        sys.exit(1)

    packages = registry_data.get("packages", [])
    if not packages:
        print("No packages found in registry.json")
        sys.exit(0)

    changes_made = False

    # Check each package
    for i, package in enumerate(packages):
        repo_url = package.get("repository", "")
        if not repo_url:
            print(
                f"Package at index {i} has no repository URL, marking as invalid")
            package["valid"] = False
            changes_made = True
            continue

        print(
            f"Checking package: {package.get('name', f'[unnamed at index {i}]')}")

        # Fetch sop.toml
        sop_data = fetch_sop_toml(repo_url)

        # Check if entry file exists
        entry_exists = False
        if sop_data and "package" in sop_data and "entry" in sop_data["package"]:
            entry_exists = check_entry_file(
                repo_url, sop_data["package"]["entry"])

        # Compare metadata
        metadata_matches = compare_metadata(package, sop_data)

        # Determine if package is valid
        is_valid = bool(sop_data and entry_exists and metadata_matches)

        # Update valid status if it changed
        if package.get("valid", True) != is_valid:
            print(
                f"Changing valid status from {package.get('valid', True)} to {is_valid}")
            package["valid"] = is_valid
            changes_made = True
        elif "valid" not in package:
            # If valid field doesn't exist yet, add it
            package["valid"] = is_valid
            changes_made = True

    # Save changes if any were made
    if changes_made:
        # Update registry.json
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(registry_data, f, indent=2)

        # Commit changes
        pat = os.getenv("GH_PAT")
        if not pat:
            print("❌ Error: GH_PAT environment variable is not set.", file=sys.stderr)
            sys.exit(1)

        # Configure Git
        run_git_command(["git", "config", "user.name", "sharafdin"],
                        "Failed to configure Git username")
        run_git_command(["git", "config", "user.email", "isasharafdin@gmail.com"],
                        "Failed to configure Git email")

        # Use the repository URL from the GitHub environment if available
        repo_url = os.getenv("GITHUB_REPOSITORY", "soplang/registry")
        remote_url = f"https://x-access-token:{pat}@github.com/{repo_url}.git"
        run_git_command(["git", "remote", "set-url", "origin", remote_url],
                        "Failed to set Git remote URL")

        # Add, commit, and push changes
        if not run_git_command(["git", "add", registry_path],
                               "Failed to stage changes"):
            sys.exit(1)

        if not run_git_command(["git", "commit", "-m", "chore: update 'valid' status for packages"],
                               "Failed to commit changes"):
            sys.exit(1)

        # Get current branch
        branch_name = run_git_command(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                                      "Failed to determine current branch")
        if not branch_name:
            branch_name = "main"  # Default to main if we can't determine the branch

        # Try to push changes
        print(f"Pushing changes to {branch_name} branch...")
        if run_git_command(["git", "push", "origin", branch_name],
                           f"Failed to push changes to {branch_name}"):
            print("✅ Successfully updated and committed package validity status")
        else:
            print(
                "⚠️ Changes were made locally but could not be pushed to the repository")
            sys.exit(1)
    else:
        print("✅ No changes to package validity status")


if __name__ == "__main__":
    main()
