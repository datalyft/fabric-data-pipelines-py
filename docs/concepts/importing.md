# Importing

Load existing Fabric pipelines into typed Python objects, then re-export or generate source.

## Parse pipeline JSON

Fabric `pipeline-content.json` does not store the pipeline name (that lives on the item folder / `.platform`). Pass `name=` explicitly:

```python
from fabric_data_pipelines import Pipeline

pipeline = Pipeline.from_json(json_text, name="Daily_Silver_Sales")
# or
pipeline = Pipeline.from_dict(data, name="Daily_Silver_Sales")
```

Modeled activity types become concrete classes (`Notebook`, `Copy`, `IfCondition`, …). Anything unmodeled becomes `RawActivity` with the original `type` and `typeProperties` preserved.

## Load a Fabric Git item folder

```python
from fabric_data_pipelines import Pipeline, load_workspace

pipeline = Pipeline.load_item("out/Daily_Silver_Sales.DataPipeline")
# logicalId from .platform and schedules from .schedules are restored when present

pipelines = load_workspace("out")  # all *.DataPipeline/ folders, including nested
pipelines_top = load_workspace("out", recursive=False)  # immediate children only
```

`load_item` also accepts a workspace directory that contains exactly one `*.DataPipeline` folder.
`load_workspace` discovers item folders recursively by default; pass `recursive=False` for a shallow scan.

## Round-trip

```python
loaded = Pipeline.load_item(item_dir)
loaded.save_item("out_roundtrip")
```

Fidelity is **semantic**: the typed graph and re-exported Fabric JSON match for library-emitted content. Policy defaults the models inject may differ from sparse UI exports; unknown connectors/datasets use generic escape hatches (`CopySource`, `Dataset`, `RawActivity`).

## Generate Python with the CLI

```bash
fabric-data-pipelines codegen path/to/Item.DataPipeline -o pipeline.py
fabric-data-pipelines codegen path/to/pipeline-content.json --name MyPipeline -o pipeline.py
```

The CLI emits reviewable constructors for modeled types and `RawActivity(...)` for the rest. See [Exporting](exporting.md) for the write path.

For the end-to-end UI/Git → Python → re-export workflow, see [Migrate from Fabric](../guides/migrate.md).
