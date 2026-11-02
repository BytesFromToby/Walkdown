// WALKDOWN FIXTURE :: class 17 changing the host agent itself (its binary) :: inert; nothing runs. Expected results in Fixtures/ANSWERS/.
// POSITIVES / gate
execSync(`codesign --force --sign - "${claudePath}"`);
// This patcher rewrites one function inside the Claude Code binary.
// NEGATIVES (must NOT fire)
execSync("codesign --verify --deep MyApp.app");
// Build the binary with cargo, then run it.
