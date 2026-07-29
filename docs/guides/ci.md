# CI with GitHub Actions

Treat pipeline Python as application code: validate on every PR, export Fabric item folders when merging to the branch that Fabric syncs (or that your deploy tool consumes).

## Pattern

1. **On pull request** — install the library, import your pipeline modules, and run tests. Calling `Pipeline.to_json()` / `save()` runs graph validation (duplicate names, unknown dependencies, cycles, cross-scope edges).
2. **On merge to main** (or a release job) — run the same modules with `save_item()` / `save_workspace()`, commit or upload the generated `*.DataPipeline/` folders, then let Fabric Git sync or [fabric-cicd](deploy.md#pair-with-fabric-cicd) pick them up.

## Example workflow

Illustrative only — adapt paths and Python version to your repo:

```yaml
name: Pipelines

on:
  pull_request:
  push:
    branches: [main]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.12"
      - name: Install
        run: |
          uv venv
          uv pip install fabric-data-pipelines pytest
          # uv pip install -e ./pipelines   # if pipelines live in-repo
      - name: Validate graphs
        run: |
          uv run pytest tests/
          # Importing modules that call to_json()/save() also validates:
          # uv run python -c "import my_pipelines.daily_load"

  export:
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: validate
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
        with:
          python-version: "3.12"
      - name: Install
        run: |
          uv venv
          uv pip install fabric-data-pipelines
      - name: Export item folders
        run: uv run python scripts/export_workspace.py
        # export_workspace.py should call save_workspace(...) into e.g. fabric/
      - name: Commit exported items
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add fabric/
          git diff --staged --quiet || git commit -m "chore: export Fabric pipeline items"
          git push
```

Whether you commit exported folders back to the same repo, push them to a dedicated Git-connected repo, or hand them to fabric-cicd is a team choice. See [Deploy to Fabric](deploy.md) for the sync and promotion options.
