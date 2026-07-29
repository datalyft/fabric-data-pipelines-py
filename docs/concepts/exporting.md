# Exporting

This library supports two related export workflows depending on how you manage Fabric pipelines.

## Export a raw pipeline definition

Use `Pipeline.to_json()` or `Pipeline.save()` when you need the pipeline JSON itself.

```python
json_text = pipeline.to_json()
pipeline.save("daily_load.json")
```

This is useful for inspection, testing, or integrating with APIs that accept the pipeline definition directly.

## Export a Fabric Git item folder

Use `Pipeline.save_item()` when the output should match Fabric's Git-backed item format.

```python
pipeline.save_item("out")
```

That creates a folder named like:

```text
Gold_Finance_Metrics_Refresh.DataPipeline/
  pipeline-content.json
  .platform
  .schedules
```

`examples/scheduled_gold_refresh.py` writes this shape end-to-end, including a weekday schedule and a pinned `logical_id`.

## Export multiple pipelines at once

Use `save_workspace()` when you want to generate several Fabric pipeline folders inside the same workspace directory.

```python
from fabric_data_pipelines import save_workspace

save_workspace([pipeline_a, pipeline_b], "workspace")
```

## Logical IDs and rename safety

Fabric item identity is tracked through `logicalId` in `.platform`.

- If you set `Pipeline(logical_id=...)`, that identity stays stable across renames.
- If you omit `logical_id`, the library derives one from the pipeline name.
- If a `.platform` file already exists, rewrites preserve its existing `logicalId`.

If you plan to rename pipelines over time and keep the same Fabric item identity, set an explicit `logical_id`.

## Schedules live separately

Fabric stores schedule configuration in `.schedules`, separate from `pipeline-content.json`. If your pipeline has schedules configured, `save_item()` writes that file automatically.

Read [Scheduling](../guides/scheduling.md) for the full schedule model.

## Next: land it in Fabric

Exporting folders is only half the loop. See [Deploy to Fabric](../guides/deploy.md) for Git sync, fabric-cicd, Terraform, and the Items REST API.
