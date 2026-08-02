# Roadmap

`fabric-data-pipelines` is Alpha. Open items below; vote or request work via [GitHub Issues](https://github.com/datalyft/fabric-data-pipelines/issues).

## Feedback and contributions

Outside pull requests are closed for now. Please open an issue instead — maintainers triage and land the work in-tree.

| Kind | What to include |
| --- | --- |
| Bug | Expected vs actual behavior, library version, and a minimal Python snippet that reproduces it |
| Feature / activity | The Fabric activity or behavior you need; link a roadmap item if it already exists |
| Roadmap vote | 👍 or comment on an existing issue, or open one for a gap not listed below |

## Import (priority)

Round-trip from existing Fabric items — the adoption unlock for editing UI-built pipelines in Python.

- [x] Load from Git item folders (`*.DataPipeline/`) — [#3](https://github.com/datalyft/fabric-data-pipelines/issues/3)
- [x] `from_json` / parse into typed models (where modeled; else `RawActivity`) — [#4](https://github.com/datalyft/fabric-data-pipelines/issues/4)
- [x] Codegen CLI: JSON → `.py` (follow-on once load works) — [#5](https://github.com/datalyft/fabric-data-pipelines/issues/5)

## Validation and errors

Stronger offline checks and clearer failures, treated as one workstream. Not a full Fabric runtime simulation.

- [ ] Deeper offline validation beyond graph checks (`validate_graph`) and Pydantic field types — [#6](https://github.com/datalyft/fabric-data-pipelines/issues/6)
- [ ] Errors that enumerate the valid set when a choice is rejected (e.g. unknown sink for a source type) — [#7](https://github.com/datalyft/fabric-data-pipelines/issues/7)

## Activities

- [x] Web
- [ ] GetMetadata — [#8](https://github.com/datalyft/fabric-data-pipelines/issues/8)
- [ ] Azure Function — [#9](https://github.com/datalyft/fabric-data-pipelines/issues/9)
- [ ] Teams / Outlook — [#10](https://github.com/datalyft/fabric-data-pipelines/issues/10)
- [ ] Filter — [#11](https://github.com/datalyft/fabric-data-pipelines/issues/11)
- [ ] Power BI semantic model refresh — [#12](https://github.com/datalyft/fabric-data-pipelines/issues/12)
- [ ] Other Fabric activity types still only named in the `RawActivity` docs — [#13](https://github.com/datalyft/fabric-data-pipelines/issues/13)

## Nice to have

- [ ] Diff-stable / deterministic JSON emission — [#14](https://github.com/datalyft/fabric-data-pipelines/issues/14)
