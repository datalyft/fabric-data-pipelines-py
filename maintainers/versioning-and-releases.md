# Versioning And Releases

Package version is defined once in `pyproject.toml` (`[project].version`).
`fabric_data_pipelines.__version__` reads that value via `importlib.metadata` after install.

The docs site uses `mike` so published documentation versions follow the package release tags.

## Version model

- Package version lives only in `pyproject.toml`.
- Git tags use a `v` prefix (`v0.1.0` for package `0.1.0`).
- Docs: `latest` tracks `main`; numbered versions come from `v*` tags; `stable` is a
  redirect alias to the newest numbered release.
- Site default is `latest` (Amplify-friendly; full asset tree at the homepage).
- Public docs: https://fabric-data-pipelines.datalyft.io/

## Local commands

Preview the docs locally:

```bash
uv sync --group docs
uv run mkdocs serve
```

Build a strict local site:

```bash
uv run mkdocs build --strict
```

Publish an unreleased docs build as `latest`:

```bash
uv run mike deploy latest --alias-type=redirect --update-aliases
uv run mike set-default latest
```

Publish a release version from a tag checkout:

```bash
uv run mike deploy 0.1.0 stable --alias-type=redirect --update-aliases
uv run mike set-default latest
```

Use `--alias-type=redirect` (not the default `symlink`) so Amplify/S3 can serve
alias paths like `/stable/` by redirecting to the real version directory.
Keep the site default on `latest` so the homepage always has a full asset tree.

## PyPI release process

1. Bump `[project].version` in `pyproject.toml` and update `CHANGELOG.md`.
2. Merge to `main` and wait for CI to pass.
3. Ensure GitHub Environment `pypi` exists and PyPI Trusted Publishing is configured for:
   - Repository: `datalyft/fabric-data-pipelines`
   - Workflow: `release.yml`
   - Environment: `pypi`
4. Tag and push:

   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

5. The **Release** workflow:
   - runs lint, typecheck, and tests
   - asserts the tag matches `pyproject.toml`
   - builds the sdist/wheel
   - smoke-imports the wheel
   - publishes to PyPI via OIDC (no API token)
6. The **Publish Docs** workflow deploys mike version `${TAG#v}` and aliases `stable`.
7. Verify:

   ```bash
   pip install fabric-data-pipelines==0.2.0
   python -c "from fabric_data_pipelines import Pipeline, __version__; print(__version__)"
   ```

## CI and automation

Repository CI always runs a strict docs build on PRs and `main`. Docs publish deploys `latest` from `main` and numbered versions from `v*` tags.
