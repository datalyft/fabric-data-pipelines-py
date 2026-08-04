# Migrate from Fabric UI / Git

Move existing Fabric pipelines from the portal or Git-synced item folders into typed Python as the authoring source of truth. Deploy stays the same: export `*.DataPipeline/` folders and sync with Git (or promote with fabric-cicd).

## 1. Get the artifacts

You need either:

- a Fabric Git item folder (`Something.DataPipeline/` with `pipeline-content.json`, `.platform`, and optional `.schedules`), or
- raw pipeline JSON / `pipeline-content.json` exported from Fabric.

If the workspace is already Git-connected, pull or clone the connected repo and locate the `*.DataPipeline/` folders you want to migrate.

## 2. Generate Python with the CLI

```bash
fabric-data-pipelines codegen path/to/Item.DataPipeline -o pipeline.py
fabric-data-pipelines codegen path/to/pipeline-content.json --name MyPipeline -o pipeline.py
```

Item folders (or a `pipeline-content.json` inside one) restore the display name, `logicalId`, and schedules when present. Standalone JSON requires `--name` because Fabric content files do not store the pipeline name.

## 3. Review the generated source

Modeled activities become constructors (`Notebook`, `Copy`, `IfCondition`, …). Anything the library does not model yet is emitted as `RawActivity(...)` with the original `type` and `typeProperties`. Unrecognized Copy connectors or datasets use generic escape hatches (`CopySource`, `Dataset`).

Keep `RawActivity` where it is fine, or replace pieces gradually with typed classes as you adopt them. See [Activities](../concepts/activities.md) and [Raw](../reference/activities/raw.md).

## 4. Edit in Python

Treat the generated file as a starting point:

- tighten dependencies with `.then()`, `.after()`, or `>>`
- replace string expressions with `expr.*` helpers where useful
- add parameters, library variables, or schedules in code
- pin `Pipeline(logical_id=...)` from `.platform` when renames must keep the same Fabric identity

## 5. Re-export and sync

```python
pipeline.save_item("workspace")  # -> workspace/<Name>.DataPipeline/
```

Commit the folders into the Git-connected repo and sync into Fabric. See [Deploy to Fabric](deploy.md).

## Load without codegen

When you only need to inspect, validate, or round-trip in memory (no Python source yet):

```python
from fabric_data_pipelines import Pipeline, load_workspace

pipeline = Pipeline.load_item("out/Daily_Silver_Sales.DataPipeline")
pipeline = Pipeline.from_json(json_text, name="Daily_Silver_Sales")
pipelines = load_workspace("out")  # all *.DataPipeline/ folders
```

API details: [Importing](../concepts/importing.md).

## Fidelity and caveats

- Round-trip is **semantic**, not byte-identical. Typed models may inject policy defaults that sparse UI exports omit.
- Schedules live in `.schedules` on item folders; `load_item` / codegen restore them when present. They are not part of the Items API `to_definition()` payload.
- Unknown activity types stay as `RawActivity` until the library models them; unknown connectors use generic types.

## Bulk workspaces

`load_workspace("out")` discovers every `*.DataPipeline/` folder (recursively by default). The `codegen` CLI takes a single path per invocation — run it once per item you want as Python source.

## Next steps

- [Importing](../concepts/importing.md) — `from_json`, `load_item`, `load_workspace`
- [Exporting](../concepts/exporting.md) — JSON vs item-folder output
- [Deploy to Fabric](deploy.md) — Git sync, fabric-cicd, Terraform
- [Import reference](../reference/import.md) — public import API
