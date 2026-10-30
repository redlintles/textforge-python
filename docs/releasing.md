# Release procedure

Nothing in the implementation work publishes a package, pushes Git, or changes
existing versions. The distribution starts with the pre-existing binding crate
version 0.1.0. The core remains 0.1.9. A maintainer must approve future version
changes and actual publication according to the main project's AGENTS.md.

1. Verify availability/ownership of `textforge-python` on PyPI and TestPyPI.
   The package imports as `textforge`. Avoid installing another distribution that
   supplies that same import into the same environment.
2. Run the full quality script against an installed wheel. Build a release wheel
   and sdist with `maturin build --release --locked --sdist --out dist`.
   Run `python -m twine check dist/*`.
3. Unpack the sdist in a new directory outside both repositories. Run
   `maturin build --release --locked --out dist`, install the resulting wheel in a
   clean virtual environment, then run the included Python tests. Verify LICENSE,
   `_native.pyi`, and `py.typed` are present in the wheel. Cargo may need network
   access for third-party dependencies; the TextForge checkout is not needed.
4. Review the wheels built by GitHub Actions. CI covers Linux x86_64, Windows
   x86_64 and macOS arm64; it tests Python 3.10, 3.12, and 3.14 on Linux. Other
   platforms can build from source; do not claim them as tested wheel targets.
5. Configure GitHub environments named `testpypi` and `pypi`, with required
   maintainer reviewers. Create trusted publishers on each index for owner
   `redlintles`, repository `textforge-python`, workflow `ci.yml`, and the matching
   environment. This is an account setup step that cannot be done by a package.
6. After approval, push the reviewed commits yourself. Run the CI workflow manually
   with destination `testpypi` first. Install that exact release from TestPyPI into
   a clean environment and smoke-test it. Review all files before approval.
7. Manually run CI with destination `pypi` after release approval. The publishing
   job uses OIDC via the PyPA action; no long-lived PyPI token belongs in this repo.
   Normal pushes, pull requests, and the default manual destination `none` never
   publish. The PyPI and TestPyPI environments should both require review.

Release metadata is defined in Cargo.toml and pyproject.toml. There is no hard-coded
second Python version to update. Cargo publish is disabled: this repository's
release artifact is the Python distribution. The workflow builds abi3 wheels for
Python >=3.10; Rust is needed only for source installation. Linux wheel portability
in CI is controlled by maturin's manylinux build image, not the developer machine's
local glibc tag.

Sources consulted when preparing packaging:
- https://www.maturin.rs/distribution.html
- https://pyo3.rs/v0.30.1/
- https://docs.pypi.org/trusted-publishers/adding-a-publisher/
