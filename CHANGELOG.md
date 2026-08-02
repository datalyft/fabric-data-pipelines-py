# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Import: `Pipeline.from_dict` / `from_json`, `Pipeline.load_item`, `load_workspace`, and `parse_activity` for round-tripping Fabric JSON and `*.DataPipeline/` folders (unknown activities → `RawActivity`).
- CLI: `fabric-data-pipelines codegen` emits Python source from an item folder or pipeline JSON.

## [0.2.1] - 2026-07-29

### Added

- `Web` activity (`WebActivity`) for HTTP calls via a Fabric connection (`relative_url`, `method`, headers/body, timeouts).

## [0.2.0] - 2026-07-29

### Changed

- **Breaking:** rename the import package from `fabric_pipelines` to `fabric_data_pipelines` so it matches the PyPI distribution name `fabric-data-pipelines`. Update imports: `from fabric_data_pipelines import Pipeline, …`.

## [0.1.0] - 2026-07-29

### Added

- Initial release of `fabric-data-pipelines`.
- Define Microsoft Fabric data pipelines as code with Pydantic v2 validation.
- Activities: Copy, Lookup, Notebook, Dataflow, StoredProcedure, Script, ExecutePipeline, SetVariable, AppendVariable, IfCondition, ForEach, Switch, Until, Wait, Fail, and RawActivity.
- Dependency chaining via `.then()`, `.after()`, and `>>` with Succeeded/Failed/Completed/Skipped.
- Expression helpers (`expr.parameter`, `expr.activity_output`, …).
- Pipeline-level parameters, variables, library variables, and concurrency.
- `to_json()`, `save()`, `save_item()`, and `to_definition()` (REST API base64 parts).
- Build-time validation for duplicate names, cycles, and unknown/cross-scope dependencies.
- Snapshot tests against real Fabric pipeline JSON exports.

[0.2.1]: https://github.com/datalyft/fabric-data-pipelines/releases/tag/v0.2.1
[0.2.0]: https://github.com/datalyft/fabric-data-pipelines/releases/tag/v0.2.0
[0.1.0]: https://github.com/datalyft/fabric-data-pipelines/releases/tag/v0.1.0
