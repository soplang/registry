# Soplang Registry

The official package registry for Soplang Hub. Stores and serves Soplang packages for seamless integration and distribution. 🚀📦

## About

This repository maintains a central registry of Soplang packages. Each package entry contains metadata about the package, including its name, version, repository URL, and other relevant information.

## How to Add Your Package

1. **Fork this repository**
2. **Add your package to the registry**:
   - Edit `registry.json` (this is the ONLY file you should modify)
   - Add a new entry at the end of the `packages` array with only the `repository` field:
     ```json
     {
       "repository": "https://github.com/yourusername/your-package"
     }
     ```
3. **Open a Pull Request**
   - Our automated validation will:
     - Verify you've only modified the registry.json file
     - Verify you've only added one new package
     - Fetch and validate your `sop.toml` file
     - Update the registry with complete metadata from your package

## Requirements

Your package repository must contain:
- A valid `sop.toml` file in the root directory with the following required fields:
  - `name`: Package name
  - `version`: Package version
  - `status`: Package status (e.g., "stable", "beta", "alpha")
  - `license`: Package license
  - `author`: Package author
  - `repository`: Repository URL
  - `entry`: Path to the entry file
- The entry file specified in `sop.toml`

## Validation Process

When you submit a PR, our GitHub Actions workflow will:
1. Verify that you've only modified the registry.json file
2. Verify that you've only appended one new package
3. Fetch and validate your `sop.toml` file
4. Update the registry with complete metadata
5. Commit the changes back to your PR branch

## Package Validity Monitoring

All packages in the registry are checked daily to ensure they remain valid:

- Each package's repository is checked to ensure:
  - The `sop.toml` file is still accessible
  - The entry file specified in `sop.toml` exists
  - The metadata in `sop.toml` matches what's in the registry

- Packages have a `valid` field that indicates their current status:
  - `true`: The package is valid and up-to-date
  - `false`: The package has issues (missing files or metadata mismatch)

- If a package becomes invalid, it will be automatically marked as such
- If a previously invalid package is fixed, it will be automatically marked as valid again

## Important Notes

- Only modify the registry.json file in your PR
- Only add one new package at a time
- Only include the repository URL in your initial submission
- The rest of the metadata will be automatically populated from your sop.toml file
- Keep your package's sop.toml file up-to-date to maintain validity

## License

This registry is maintained by the Soplang team. 
