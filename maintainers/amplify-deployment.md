# Amplify Deployment

This repository is set up so the docs can be hosted as a static site on AWS Amplify.

## Recommended setup

Use two deployment paths:

- a production Amplify app connected to the published docs branch
- an optional preview Amplify app connected to `main` for branch-preview builds

This split keeps production versioned docs stable while still allowing preview environments for in-progress documentation changes.

## Build behavior

The root `amplify.yml` builds the docs site with `mkdocs build --strict` and publishes the generated `site/` directory.

## Production branch options

The simplest production flow is:

1. publish versioned docs from GitHub Actions into a dedicated branch such as `docs-site`
2. connect Amplify to that branch
3. let Amplify serve the built static files

If you prefer Amplify to build from source directly, connect it to `main` and accept that production release versioning must still be handled by your publish workflow.

## Operational notes

- Amplify hosting works well for the static MkDocs output.
- `mike` is responsible for constructing the versioned site structure.
- Always deploy mike aliases with `--alias-type=redirect`. Amplify/S3 does not follow
  git symlinks, so the default `symlink` aliases make `/stable/` unusable (missing
  assets / broken navigation). Redirect aliases send `/stable/` to `/0.1.0/` (etc.).
- The site default version is `latest` so the homepage never depends on an alias path.
- release tags should remain the source of truth for immutable documentation versions.
