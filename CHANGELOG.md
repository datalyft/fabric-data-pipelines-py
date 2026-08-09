# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0](https://github.com/datalyft/fabric-data-pipelines/releases/tag/v0.3.0) - 2026-08-09

### Added

- Validation: `InvalidChoiceError` for finite choice rejections that list the allowed values ([#7](https://github.com/datalyft/fabric-data-pipelines/issues/7)).
- Validation: Construction-time activity validation on `Activity` and every activity subclass (required fields, control-flow bodies, Copy sink/staging, connector↔dataset pairing for known types, and related invariants) ([#6](https://github.com/datalyft/fabric-data-pipelines/issues/6)).

### Changed

- **Breaking:** previously accepted invalid activity shapes now fail at construction and on import (for example Copy without sink, mismatched known connector/dataset pairs, empty `ForEach`/`Until` bodies, `Script` without a connection). Unknown connector/dataset types and `RawActivity` remain escape hatches. Graph checks via `validate_graph()` are unchanged.

## [0.2.2](https://github.com/datalyft/fabric-data-pipelines/releases/tag/v0.2.2) - 2026-08-03

### Added

- Import: load pipelines from Fabric Git item folders via `Pipeline.load_item` and `load_workspace` ([#3](https://github.com/datalyft/fabric-data-pipelines/issues/3)).
- Import: `Pipeline.from_dict` / `from_json` and `parse_activity` parse Fabric JSON into typed models (unknown activities → `RawActivity`) ([#4](https://github.com/datalyft/fabric-data-pipelines/issues/4)).
- Import: CLI `fabric-data-pipelines codegen` emits Python source from an item folder or pipeline JSON ([#5](https://github.com/datalyft/fabric-data-pipelines/issues/5)).
- Import: `load_workspace` discovers nested `*.DataPipeline` folders by default (`recursive=False` for top-level only) ([#17](https://github.com/datalyft/fabric-data-pipelines/issues/17)).

### Fixed

- Import: `SqlMISource` / `DataWarehouseSource` accept Expression or string `sqlReaderQuery` ([#16](https://github.com/datalyft/fabric-data-pipelines/issues/16)).

## [0.2.1](https://github.com/datalyft/fabric-data-pipelines/releases/tag/v0.2.1) - 2026-07-29

### Added

- `Web` activity (`WebActivity`) for HTTP calls via a Fabric connection (`relative_url`, `method`, headers/body, timeouts).

## [0.2.0](https://github.com/datalyft/fabric-data-pipelines/releases/tag/v0.2.0) - 2026-07-29

### Changed

- **Breaking:** rename the import package from `fabric_pipelines` to `fabric_data_pipelines` so it matches the PyPI distribution name `fabric-data-pipelines`. Update imports: `from fabric_data_pipelines import Pipeline, …`.

## [0.1.0](https://github.com/datalyft/fabric-data-pipelines/releases/tag/v0.1.0) - 2026-07-29

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
