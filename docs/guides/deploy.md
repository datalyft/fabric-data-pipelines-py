# Deploy to Fabric

This library stops at Fabric-compatible artifacts: raw pipeline JSON or `*.DataPipeline/` item folders. Getting those into a workspace is a separate step. The usual path is **Git sync**; teams with promotion pipelines often pair the export with **fabric-cicd**, **Terraform**, or the **Items REST API**.

## Primary path: Git sync

1. Author pipelines in Python and export item folders:
  ```python
   from fabric_data_pipelines import Pipeline, Wait

   pipeline = Pipeline(
       name="Daily_Silver_Sales_Transform",
       activities=[Wait(name="pause", wait_time_in_seconds=30)],
   )
   pipeline.save_item("workspace")  # -> workspace/Daily_Silver_Sales_Transform.DataPipeline/
  ```
   Or export several at once with `save_workspace([...], "workspace")`.
2. Commit the generated folders into the repository that is connected to your Fabric workspace (GitHub or Azure DevOps). A typical layout:
3. In Fabric, connect the workspace to that repo/branch (Workspace settings → Git integration) if it is not already connected.
4. Sync from Git into the workspace. Fabric creates or updates the pipeline items from the committed `*.DataPipeline/` folders.

Pin `Pipeline(logical_id=...)` when renames must keep the same Fabric identity.

See [Exporting](../concepts/exporting.md) for `logicalId` and `.schedules` behavior.

## Pair with fabric-cicd

[fabric-cicd](https://github.com/microsoft/fabric-cicd) deploys and promotes Fabric items across workspaces. A common split:

- **This library** authors validated `*.DataPipeline/` folders (and related content) in Git.
- **fabric-cicd** publishes those items into target workspaces as part of a release or environment promotion.

Export on merge (or in a release job), then point fabric-cicd at the folder that contains your item definitions. See also [CI with GitHub Actions](ci.md).

## Pair with Terraform

The [Fabric Terraform provider](https://registry.terraform.io/providers/microsoft/fabric/latest) manages workspace resources and item lifecycle. Use this library when you want typed Python to own the **pipeline definition content**, then:

- commit `*.DataPipeline/` folders and let Git sync apply them, or
- feed `Pipeline.to_definition()` / exported JSON into whatever workflow you use alongside Terraform-managed capacity, workspaces, and connections.

Treat Terraform as infra and promotion; treat `fabric-data-pipelines` as the authoring layer for pipeline JSON.

## REST Items API

For scripts or custom deployers that call the Fabric Items API directly:

```python
definition = pipeline.to_definition()
# definition["parts"] holds base64 InlineBase64 payloads for
# pipeline-content.json and .platform
```

Note: `.schedules` is written by `save_item()` for Git item folders; it is not included in the Items API `definition` payload returned by `to_definition()`.

## Next steps

- [Migrate from Fabric](migrate.md) — UI/Git item folders → typed Python source
- [Exporting](../concepts/exporting.md) — JSON vs item-folder details
- [CI with GitHub Actions](ci.md) — validate on PR, export on merge
- [How this compares](positioning.md) — UI, fabricflow, fabric-cicd, Terraform
