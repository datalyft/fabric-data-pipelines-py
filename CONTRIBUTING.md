# Contributing to fabric-data-pipelines

Thanks for your interest in improving this project. These guidelines explain how to help while the library is in Alpha.

## How to contribute right now

**Outside pull requests are closed for now.** Maintainers triage and land work in-tree.

Please contribute by opening a [GitHub Issue](https://github.com/datalyft/fabric-data-pipelines/issues):

1. Search existing issues first (including closed ones) to avoid duplicates.
2. Prefer reacting with 👍 or commenting on an existing issue when it already covers your request.
3. Open a new issue only when nothing fits.

## Opening useful issues

### Bugs

Include:

- Library version (`pip show fabric-data-pipelines` or the PyPI version you installed)
- Python version
- What you expected vs what happened
- A **minimal** Python snippet that reproduces the problem
- Relevant stack traces or validation error messages

### Features and activity models

Include:

- The Fabric activity `type` string (from exported JSON), when applicable
- A redacted `typeProperties` snippet from a UI-exported pipeline
- Why a typed model (or other change) would help

Use `RawActivity` as a workaround for unmodeled activity types today. Docs: [Raw Activity](https://fabric-data-pipelines.datalyft.io/latest/reference/activities/raw/).

### Questions

Open an issue with a clear title and enough context that maintainers can answer without a follow-up round trip. Link to the docs page you already checked when possible: [fabric-data-pipelines.datalyft.io](https://fabric-data-pipelines.datalyft.io/latest/).

## Pull requests

External PRs are not accepted at this time. If you open one, it may be closed with a pointer back to issues.

Maintainers may still use PRs internally for review.

## License

By contributing ideas or (when PRs reopen) code, you agree that your contribution is licensed under the same [MIT License](LICENSE) as the project.