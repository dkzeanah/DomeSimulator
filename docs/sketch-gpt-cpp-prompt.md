# Standalone C++ build prompt

Build **sketch-gpt-cpp**, a production desktop dome design and documentation
studio. Follow the entire accompanying `sketch-gpt-standalone-spec.md` as the
acceptance contract. Implement the software and generate a sample release.

Use C++20 or newer with CMake presets and pinned, documented dependencies.
Separate libraries for geometry, document/commands, rendering, technical
drawings and export from the desktop executable. Geometry and document code
must be testable without a display or GUI event loop. Use double precision in
the model and explicit float conversion at the GPU boundary.

Choose a maintained desktop stack, such as Qt 6 with a native GPU viewport, or
an equally justified alternative. Qt's drawing/PDF facilities may serve the
vector sheet pipeline. Use established math and JSON libraries where useful.
Verify current APIs, licensing and redistribution requirements from official
documentation before choosing versions. Implement the final geometry/command
core in C++; a Python golden-reference tool is acceptable during the port.

Use RAII, value semantics where appropriate, stable typed IDs and explicit
ownership. Avoid raw owning pointers. Commands support transactional edits,
undo/redo, deterministic replay and serialized persistence. Separate UI view
models from authoritative geometry. Use a coherent error/result convention,
validate schema and all numeric inputs, and avoid exceptions escaping event
handlers or worker thread boundaries. Background exports support progress and
cancellation without touching UI objects from a worker thread.

Provide debug/release CMake presets, unit/integration tests, original-solver
golden comparisons, replay tests, offscreen render tests and rendered PDF QA.
Run address/undefined behavior sanitizers on a supported toolchain and explain
any platform-specific exclusions. Produce a Windows executable with required
runtime deployment, build/install documentation, dependency licenses, example
project and append-only sample release. Document tolerances, units, transforms,
remaining limitations and the engineering decisions still required.

Start by inspecting available repository code and reference PDFs. If none are
available, say so and proceed with explicit assumptions. Work until the app runs
and all core acceptance tests pass; report measured results and artifact paths.
