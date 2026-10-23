# Standalone Rust build prompt

Build **sketch-gpt-rust**, a production desktop dome design and documentation
studio. Follow the entire accompanying `sketch-gpt-standalone-spec.md` as the
acceptance contract. Implement the software and generate a sample release.

Use stable Rust with a Cargo workspace. A suggested decomposition is
`geometry`, `document`, `render`, `drawings`, `export`, and `desktop`; improve
boundaries where necessary. Keep geometry/document crates independent of UI and
GPU state so deterministic tests and batch exports run headlessly. Use f64 for
geometry and a documented f32 conversion at the rendering boundary.

Choose a maintained native UI/GPU stack (for example egui with wgpu, or an
equally justified alternative), serde project serialization, and a suitable
math library. Verify actual current APIs and compatibility before locking
versions. Do not wrap a Python app and call that a Rust implementation. A
temporary import/golden-reference bridge to DomeSim's Python solver is acceptable
while porting, but ship the final core solver and command model in Rust.

Design commands as an explicit enum with typed validated IDs, transactional
apply/revert, deterministic replay and error values. Distinguish lengths,
angles and coordinate spaces in types where practical. Validate all serialized
input, bound expensive allocations, and report unsupported schema versions.
Keep unsafe code out of the geometry and document core; explain any unavoidable
unsafe boundary. Export work runs off the UI thread with progress and cancellation.

Provide `cargo fmt --check`, clippy with warnings addressed, unit/integration
tests, numeric golden tests against the original solver, command replay tests,
offscreen render tests and PDF page render checks. Include an installable Windows
build, reproducible build commands, example project and an append-only sample
release. Document architecture, coordinate conventions, tolerance choices and
known limitations. Do not claim engineer-approved construction documents.

Start by inspecting available repository code and reference PDFs. If none are
available, say so and proceed with explicit assumptions. Work until the app runs
and all core acceptance tests pass; report measured results and artifact paths.
