# How this compares

Short answer: this library **authors** typed, validated pipeline definitions (JSON and Git item folders). It does not replace the UI for exploration, and it does not replace deploy/promotion tools.

## Fabric UI + Git integration

The Fabric portal is the right place to explore activities, debug a single run, and learn the product. Git integration already lets you version `*.DataPipeline/` folders. What the UI does not give you is a typed, reviewable authoring experience in Python: dependency helpers, expression builders, and graph validation before anything hits the workspace. Use the UI to discover; use this library when pipelines are product code. Coming from the UI or an existing Git item folder? See [Migrate from Fabric](migrate.md).

## fabricflow

[fabricflow](https://github.com/ladparth/fabricflow) is a code-first SDK aimed at building and **operating** Fabric pipelines and related items through the REST API (workspaces, templates, execute/monitor). Overlap exists on activity modeling, but the centers of gravity differ: fabricflow leans toward live API workflows and templates in a workspace; `fabric-data-pipelines` leans toward **offline definition authoring**, Git item folders, and CI validation without calling Fabric. Teams can use both — author definitions here, operate or template-deploy via fabricflow — but you do not need both for a Git-sync workflow.

## fabric-cicd

[fabric-cicd](https://github.com/microsoft/fabric-cicd) is about **deploying and promoting** Fabric items across environments. It consumes item definitions; it does not replace authoring them. Generate `*.DataPipeline/` folders with this library, then let fabric-cicd publish them. See [Deploy to Fabric](deploy.md).

## Terraform Fabric provider

The [Fabric Terraform provider](https://registry.terraform.io/providers/microsoft/fabric/latest) manages capacity, workspaces, and resource lifecycle as infrastructure as code. Pipeline **content** is still a nested JSON/item definition problem. Use Terraform for the platform envelope; use `fabric-data-pipelines` to produce the pipeline definitions that Git sync, fabric-cicd, or custom automation applies.
