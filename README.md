# fabric-data-pipelines

[![PyPI](https://img.shields.io/pypi/v/fabric-data-pipelines)](https://pypi.org/project/fabric-data-pipelines/)
[![CI](https://github.com/datalyft/fabric-data-pipelines-py/actions/workflows/ci.yml/badge.svg)](https://github.com/datalyft/fabric-data-pipelines-py/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/fabric-data-pipelines)](https://pypi.org/project/fabric-data-pipelines/)
[![Downloads](https://img.shields.io/pypi/dm/fabric-data-pipelines)](https://pypi.org/project/fabric-data-pipelines/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Docs](https://img.shields.io/badge/docs-fabric--data--pipelines.datalyft.io-blue)](https://fabric-data-pipelines.datalyft.io/latest/)

**Docs:** [fabric-data-pipelines.datalyft.io](https://fabric-data-pipelines.datalyft.io/latest)

`fabric-data-pipelines` is a Python library for authoring [Microsoft Fabric](https://learn.microsoft.com/fabric) data pipelines as code.

Microsoft Fabric pipelines are JSON definitions under the hood. Editing that JSON by hand is slow and brittle: activity payloads are deeply nested, dependency wiring is verbose, and expression strings are easy to break. This library lets you describe pipelines with typed Python objects and then generate the exact Fabric-compatible JSON or Git item folders that Fabric expects.

Full guides, API reference, and real-world examples live on the [documentation site](https://fabric-data-pipelines.datalyft.io/latest/).

## Who this is for

This package is designed for teams that want Microsoft Fabric pipelines to be:

- declared in Python instead of assembled in the UI or hand-written JSON
- reviewed and versioned in Git
- exported into Fabric's `*.DataPipeline` folder format
- validated before deployment or commit

Typical users are data engineers, analytics engineers, and platform teams building repeatable ETL or orchestration flows in Fabric.

## Why use it

- Typed activities instead of manually building nested Fabric payloads
- Readable dependency helpers like `.then()`, `.after()`, and `>>`
- Expression helpers for parameters, activity outputs, run metadata, and interpolation
- First-class support for Fabric Git item folders, including `.platform` and `.schedules`
- Validation of dependency graphs before serialization
- An escape hatch via `RawActivity` when Fabric supports something not modeled yet

## What it helps you build

You can use `fabric-data-pipelines` to build:

- small pipelines such as `Wait -> Notebook`
- ETL orchestration with `Script`, `Copy`, `Lookup`, and `ExecutePipeline`
- control-flow pipelines with `IfCondition`, `ForEach`, `Switch`, and `Until`
- scheduled Fabric items ready for Git integration

## Installation

```bash
pip install fabric-data-pipelines
# or
uv add fabric-data-pipelines
```

Requires Python 3.10+.

```python
from fabric_data_pipelines import Pipeline, Wait, Notebook
```

## Quickstart

Create a tiny pipeline in Python and export the JSON definition:

```python
from fabric_data_pipelines import Notebook, Pipeline, Wait

wait = Wait(name="Wait_For_Upstream", wait_time_in_seconds=30)
transform = Notebook(
    name="Transform_Silver_Sales",
    notebook_id="00000000-0000-0000-0000-000000000002",
    workspace_id="00000000-0000-0000-0000-000000000001",
)

wait.then(transform)

pipeline = Pipeline(
    name="Daily_Silver_Sales_Transform",
    activities=[wait, transform],
)
pipeline.save("daily_silver_sales_transform.json")
```

That produces a Fabric-compatible pipeline definition without manually assembling the underlying JSON.

## Before / after

Hand-writing Fabric JSON means nested policies, dataset settings, and column mappings. The same landing truncate-and-copy in Python is compact; the generated definition is ~200 lines.

**Python** (see [`examples/landing_truncate_copy.py`](examples/landing_truncate_copy.py)):

```python
from fabric_data_pipelines import (
    AzureSqlMITable,
    ColumnMapping,
    ColumnRef,
    Copy,
    ExternalReferences,
    Pipeline,
    Script,
    ScriptBlock,
    SqlMISink,
    SqlMISource,
    TabularTranslator,
    TypeConversionSettings,
    expr,
)

LANDING = expr.library_variable("Demo_ETL_Library_Landing")
SOURCE = expr.library_variable("Demo_ETL_Library_SourceDb")
COLUMNS = ["customer_id", "region", "segment", "updated_at"]

truncate = Script(
    name="Truncate_Landing_customers",
    database="Landing",
    scripts=[
        ScriptBlock(
            text={"value": "TRUNCATE TABLE sales.customers", "type": "Expression"},
            type="Query",
        )
    ],
    external_references=ExternalReferences(connection=LANDING),
)
copy = Copy(
    name="Copy_customers_to_Landing",
    source=SqlMISource(
        sql_reader_query=SELECT_SQL,
        dataset_settings=AzureSqlMITable(database="SourceDb", connection=SOURCE),
    ),
    sink=SqlMISink(
        write_behavior="insert",
        dataset_settings=AzureSqlMITable(
            database="Landing",
            schema_name="sales",
            table="customers",
            connection=LANDING,
        ),
    ),
    translator=TabularTranslator(
        mappings=[
            ColumnMapping(
                source=ColumnRef(name=col, type="String", physical_type="nvarchar"),
                sink=ColumnRef(name=col, type="String", physical_type="nvarchar"),
            )
            for col in COLUMNS
        ],
        type_conversion=True,
        type_conversion_settings=TypeConversionSettings(allow_data_truncation=True),
    ),
)
truncate.then(copy)
```

**Generated Fabric JSON** (excerpt of ~200 lines):

```json
{
  "properties": {
    "activities": [
      {
        "name": "Truncate_Landing_customers",
        "type": "Script",
        "typeProperties": {
          "database": "Landing",
          "scripts": [
            {
              "text": { "value": "TRUNCATE TABLE sales.customers", "type": "Expression" },
              "type": "Query"
            }
          ]
        },
        "externalReferences": {
          "connection": "@pipeline().libraryVariables.Demo_ETL_Library_Landing"
        }
      },
      {
        "name": "Copy_customers_to_Landing",
        "type": "Copy",
        "dependsOn": [
          { "activity": "Truncate_Landing_customers", "dependencyConditions": ["Succeeded"] }
        ],
        "typeProperties": {
          "source": { "type": "SqlMISource", "datasetSettings": { "...": "..." }, "sqlReaderQuery": "..." },
          "sink": { "type": "SqlMISink", "datasetSettings": { "typeProperties": { "table": "customers", "schema": "sales" } } },
          "translator": { "type": "TabularTranslator", "mappings": ["... 4 column mappings ..."] }
        }
      }
    ],
    "libraryVariables": { "...": "..." }
  }
}
```

Full generated payload: [`docs/snippets/before_after_pipeline.json`](docs/snippets/before_after_pipeline.json).

## Real-world examples

The `examples/` folder contains pipelines that mirror common Fabric workloads:

| Example | Pattern |
| --- | --- |
| `daily_notebook_transform.py` | `Wait` → `Notebook` |
| `landing_truncate_copy.py` | Truncate + Sql MI `Copy` with column mappings |
| `scheduled_gold_refresh.py` | Weekly schedule + `save_item()` Git folder |
| `lakehouse_lookup_to_warehouse.py` | `Lookup` → `SetVariable` → Warehouse `Copy` |
| `parameterized_elt_controller.py` | `ForEach` + `Switch` + Dataflow / stored procedure |
| `etl_with_lock_pattern.py` | Lock acquire / retry / invoke child / release |

```bash
uv run python examples/landing_truncate_copy.py
uv run python examples/scheduled_gold_refresh.py
```

See the [ETL Patterns](https://fabric-data-pipelines.datalyft.io/latest/guides/etl-patterns/) guide for walkthroughs of each pattern.

## How it fits into Fabric

This library supports two main output shapes:

### 1. Raw pipeline JSON

Use `Pipeline.to_json()` or `Pipeline.save()` when you want the pipeline definition itself.

```python
json_text = pipeline.to_json()
pipeline.save("daily_load.json")
```

### 2. Fabric Git item folders

Use `Pipeline.save_item()` or `save_workspace()` when your repository is the source of truth and Fabric should consume item folders.

Fabric expects each pipeline item to live in a directory such as:

```text
Gold_Finance_Metrics_Refresh.DataPipeline/
  pipeline-content.json
  .platform
  .schedules
```

This package generates those files for you, including schedule configuration when present.

Commit the folders into a Git-connected Fabric workspace and sync — see [Deploy to Fabric](https://fabric-data-pipelines.datalyft.io/latest/guides/deploy/). For validate-on-PR / export-on-merge, see [CI with GitHub Actions](https://fabric-data-pipelines.datalyft.io/latest/guides/ci/).

## How this compares

| Tool | Role vs this library |
| --- | --- |
| Fabric UI + Git | Explore and debug in the portal; author typed, validated definitions here |
| [fabricflow](https://github.com/ladparth/fabricflow) | Live REST API / templates / execute-monitor; this library is offline Git-first authoring |
| [fabric-cicd](https://github.com/microsoft/fabric-cicd) | Deploy/promote items; this library authors the item folders it ships |
| Terraform Fabric provider | Infra and resource lifecycle; this library owns pipeline JSON/item content |

Longer write-up: [How this compares](https://fabric-data-pipelines.datalyft.io/latest/guides/positioning/).

## Core concepts

### Activities

Supported activity models include:

| Class | Fabric `type` | Notes |
| --- | --- | --- |
| `Copy` | `Copy` | Typed SQL MI / Lakehouse / Warehouse sources and sinks |
| `Lookup` | `Lookup` | |
| `Notebook` | `TridentNotebook` | |
| `Dataflow` | `RefreshDataFlow` | Dataflow Gen2 |
| `StoredProcedure` | `SqlServerStoredProcedure` | |
| `Script` | `Script` | Query / NonQuery blocks |
| `ExecutePipeline` | `ExecutePipeline` | |
| `SetVariable` / `AppendVariable` | `SetVariable` / `AppendVariable` | |
| `IfCondition` | `IfCondition` | Nested activities |
| `ForEach` | `ForEach` | Nested activities |
| `Switch` | `Switch` | Cases + default |
| `Until` | `Until` | Nested activities |
| `Wait` | `Wait` | |
| `Fail` | `Fail` | |
| `Web` | `WebActivity` | HTTP via Fabric connection |
| `RawActivity` | *(any)* | Escape hatch for unmodeled types |

**Not modeled yet** (use `RawActivity`): GetMetadata, Azure Function, Teams/Outlook, and others. See the [roadmap](ROADMAP.md).

### Dependency chaining

```python
lookup.then(copy).then(notebook)  # Succeeded (default)
copy.then(notify, on="Failed")  # Failed / Completed / Skipped
join.after(copy_a, copy_b)  # fan-in
lookup >> copy  # same as .then()
```

### Expressions

```python
from fabric_data_pipelines import expr

expr.parameter("run_date")
# '@pipeline().parameters.run_date'

expr.activity_output("get_tables", "value")
# "@activity('get_tables').output.value"

expr.library_variable("MyConnection")
expr.interp(expr.run_id())  # '@{pipeline().RunId}' for SQL interpolation
```

### Schedules

Fabric stores schedules in a separate `.schedules` file alongside `pipeline-content.json` and `.platform`. Schedules must be attached on the pipeline via `Pipeline(schedules=[...])` (multiple allowed, max 20) and are written by `Pipeline.save_item()`.

```python
from fabric_data_pipelines import Pipeline, Schedule, Wait, Weekly

schedule = Schedule(
    enabled=True,
    job_type="Execute",
    configuration=Weekly(
        start_date_time="2026-07-10T00:00:00",
        end_date_time="2027-07-10T00:00:00",
        local_time_zone_id="Romance Standard Time",
        times=["21:30"],
        weekdays=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    ),
)

pipeline = Pipeline(
    name="daily_load",
    activities=[Wait(name="pause", wait_time_in_seconds=5)],
    schedules=[schedule],
)
pipeline.save_item("out")
```

### Validation

`Pipeline.to_json()` and `Pipeline.save()` call `validate_graph()` before serializing. That catches:

- duplicate activity names, including nested scopes
- unknown `dependsOn` targets
- cross-scope dependencies
- cycles in the dependency graph

Attaching more than 20 schedules on `Pipeline(schedules=[...])` is rejected at construction time (Fabric limit).

## Stable Fabric identity

When exporting Fabric item folders, `logicalId` handling matters:

- If you set `Pipeline(logical_id=...)`, that `logicalId` stays stable across renames.
- If you omit `logical_id`, the library derives it deterministically from `Pipeline.name`.
- If a `.platform` file already exists on disk, rewrites preserve its existing `logicalId`.

If you rely on the derived value and later rename the pipeline, Fabric will treat it as a new item. Pin `logical_id` if identity continuity matters.

## Documentation

**[fabric-data-pipelines.datalyft.io](https://fabric-data-pipelines.datalyft.io/latest/)** — guides, API reference, and pattern walkthroughs.

## Roadmap

Additional activity types and stronger offline validation are planned — see [ROADMAP.md](ROADMAP.md). Outside PRs are closed for now; open a [GitHub Issue](https://github.com/datalyft/fabric-data-pipelines/issues) instead (bugs, features, roadmap votes).

Import existing Fabric JSON or `*.DataPipeline/` folders with `Pipeline.from_json` / `Pipeline.load_item`, or generate Python via `fabric-data-pipelines codegen`.

## Development

```bash
uv sync
uv run ruff check
uv run ruff format --check
uv run mypy src tests
uv run pytest
```

Maintainer notes (releases, Amplify docs hosting): [`maintainers/`](maintainers/).

## License

MIT
