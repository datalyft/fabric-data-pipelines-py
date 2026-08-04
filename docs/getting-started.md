# Getting Started

## Install

```bash
pip install fabric-data-pipelines
# or
uv add fabric-data-pipelines
```

Requires Python 3.10+.

## Build your first pipeline

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

This creates a Fabric-compatible pipeline definition without hand-writing the nested JSON payload.

## Understand the building blocks

Most pipelines follow the same pattern:

1. Create activities such as `Wait`, `Notebook`, `Copy`, or `Script`.
2. Declare the execution order with `.then()`, `.after()`, or `>>`.
3. Build a `Pipeline`.
4. Export either a JSON definition or a Fabric item folder.

## Choose your export shape

### Save a pipeline definition

```python
json_text = pipeline.to_json()
pipeline.save("daily_silver_sales_transform.json")
```

### Save a Fabric item folder

```python
pipeline.save_item("out")
```

That writes a `Daily_Silver_Sales_Transform.DataPipeline/` folder containing `pipeline-content.json`, `.platform`, and `.schedules` when schedules are configured.

## Run the examples

```bash
uv run python examples/daily_notebook_transform.py
uv run python examples/landing_truncate_copy.py
uv run python examples/scheduled_gold_refresh.py
```

## Next steps

- Read [Deploy to Fabric](guides/deploy.md) to close the loop with Git sync (and fabric-cicd / Terraform).
- Read [Migrate from Fabric](guides/migrate.md) if you already have UI or Git-synced pipelines.
- Read [Dependencies](concepts/dependencies.md) to model orchestration flows.
- Read [Expressions](concepts/expressions.md) to build dynamic Fabric expressions.
- Read [Scheduling](guides/scheduling.md) to generate `.schedules`.
- Read [ETL Patterns](guides/etl-patterns.md) for real-world pipelines across landing, ELT, and locks.
- Read [How this compares](guides/positioning.md) if you are evaluating against the UI, fabricflow, or fabric-cicd.
