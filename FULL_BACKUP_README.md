# Full project backup

Branch: full-backup-2026-11-01. This snapshot includes the current source and
Git history, private strategy notes, market CSVs, all locally saved chart files,
audits, original uploaded files, generated explanatory images and previous exports.
Private material previously ignored by Git is deliberately included at the
user's explicit request. The old handoff notes remain useful history; read the
latest USER_CLARIFICATIONS.md and CURRENT_SPEC.md for current decisions.

The current full Python suite passed 148 tests. No full automated USDJPY strategy
backtest has been completed. Latest source work is included in this snapshot.

Installed dependencies and reproducible build/runtime caches are excluded:
node_modules, Python virtual environments/bytecode, Gradle caches, frontend/dist,
backend/app/build and backend/build. Third-party files already tracked in the original repository are preserved.
Lockfiles, requirements and Gradle wrapper
are included so dependencies can be installed and builds regenerated. Machine
credentials and the execution environment itself are not project backup files.
Chat transcript and inline-only image binaries are not available for export;
the saved handoff and clarification notes describe the confirmed strategy rules.

## Restore from the bundle

git clone -b full-backup-2026-11-01 trading-software-everything.bundle Trading-Software
cd Trading-Software

All included private data is tracked on this backup branch and restores during
clone. No separate ZIP extraction is required. SHA256SUMS.json inventories the
snapshot file bytes; Git additionally verifies object integrity.

## Push from a computer with working GitHub access

git remote set-url origin https://github.com/Rahul-PuriG/Trading-Software.git
git push -u origin full-backup-2026-11-01

The earlier cloud push failed due to VPN enrollment/proxy HTTP 503. The export
is a local bundle until a successful remote push is confirmed.
