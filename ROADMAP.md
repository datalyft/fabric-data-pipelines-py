# Roadmap

`fabric-data-pipelines` is Alpha. Open items below, vote or request work via [GitHub Issues](https://github.com/datalyft/fabric-data-pipelines/issues).

## Import (priority)

Round-trip from existing Fabric items — the adoption unlock for editing UI-built pipelines in Python.

- [ ] Load from Git item folders (`*.DataPipeline/`)
- [ ] `from_json` / parse into typed models (where modeled; else `RawActivity`)
- [ ] Codegen CLI: JSON → `.py` (follow-on once load works)

## Validation and errors

Stronger offline checks and clearer failures, treated as one workstream. Not a full Fabric runtime simulation.

- [ ] Deeper offline validation beyond graph checks (`validate_graph`) and Pydantic field types
- [ ] Errors that enumerate the valid set when a choice is rejected (e.g. unknown sink for a source type)

## Activities

- [x] Web
- [ ] GetMetadata
- [ ] Azure Function
- [ ] Teams / Outlook
- [ ] Filter
- [ ] Power BI semantic model refresh
- [ ] Other Fabric activity types still only named in the `RawActivity` docs

## Nice to have

- [ ] Diff-stable / deterministic JSON emission.
