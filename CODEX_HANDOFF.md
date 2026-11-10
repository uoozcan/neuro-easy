# Codex continuation brief

## Start here

Read this file, IMPLEMENTATION_PROMPT.md, README.md, TEST_REPORT.md and the source before editing. Continue implementation; do not restart. The user has authorized installation, troubleshooting, testing and GitHub publication for MELD Graph and SWANe. Routine reversible work needs no repeated permission. Obtain required licence acceptance/registration from the actual user; do not invent or redistribute licences.

Repository: https://github.com/uoozcan/neuro-easy
Target: friend's Ubuntu laptop. Development: user's Ubuntu WSL2.

## Current state

This is a source-only development starter. Eight offline launcher regression tests passed on Windows Python 3.13. No MELD or SWANe installation, GUI check or scientific analysis has run. WSL access from the original ChatGPT Work session failed with Wsl/E_ACCESSDENIED; direct terminal HTTPS was also blocked. These are restrictions of that session, not proof of a broken Ubuntu installation. Do not reset/reinstall WSL.

The connected GitHub account worked, but the original host's gh CLI credentials were invalid. Recheck credentials in the new session; never print tokens. The project is now being published using the connected account. No external data, secrets, licence files or local runtime state should enter Git.

## Immediate work in an accessible Ubuntu session

1. Confirm Linux access and read applicable AGENTS.md. Inventory /etc/os-release, uname, CPU architecture, RAM, swap, free disk for project/data/Docker, Python, conda/venv, Docker daemon/Compose, GPU and GUI display. If launched from Windows, confirm the chosen WSL distribution/version first.
2. Recheck official releases and dependency documentation. Candidate versions reviewed on 2026-11-10: MELD v2.2.7 CPU and SWANe PyPI 0.2.1.1. The SWANe repository documents newer development features and an installer requiring >=0.2.5; do not assume the published candidate supports those features. Review the actual selected release, packaging and Ubuntu compatibility.
3. Inspect the official MELD release compose.yml and license lookup code. They were not available for source inspection in the original session. Confirm service name, working directory, mounts, GPU reservations and both licence locations before relying on the wrapper. Make CPU setup automatic using a verified supported Compose mechanism where practical.
4. Improve usability: allow SWANe setup without requiring a MELD release/configuration; provide independent readiness checks for each app; ensure doctor returns nonzero for missing prerequisites for the requested action. Add resource checks for actual Docker/data locations before large downloads and make setup resumable. Check interrupted-run reporting and collect reproducible logs locally.
5. Install isolated environments and the external dependencies required by the selected SWANe module, using official sources and release-specific instructions. Avoid changing system Python or installing into conda base. Avoid unreviewed curl-to-shell execution. Record package versions, upstream commit/release and container digests.
6. Test the actual SWANe GUI on WSLg and its module-specific dependency checks; an import test is insufficient. Select a minimal T1w structural/reference workflow as the candidate smoke analysis, but confirm required inputs and an appropriately licensed public dataset from official sources before downloading. Document the choice. Ask only if a missing scientific goal changes the required workflow.
7. Obtain user-provided MELD and FreeSurfer licences if not already present in a user-approved location. Do not search unrelated private folders for them. Run official MELD prepare_classifier and pytest. Inspect collected/skipped test cases and distinguish preprocessed-data checks from raw MRI processing.
8. Execute an actual public/deidentified MRI-to-output workflow separately for each application. Verify expected nonempty outputs, image geometry, report generation, and visual registration/segmentation quality where applicable. Do not infer interoperability or reuse a SWANe reconstruction as MELD input without validating exact versions and format requirements.
9. Run regression tests plus Bash syntax checks, fix failures, update test report with exact observed evidence and resource usage, and reproduce on native Ubuntu when available. Clean-clone Ubuntu reproduction is required before describing the distribution as validated.
10. Commit/push source-only changes and review GitHub Actions. Keep application tests distinct from offline CI. Document any remaining blockers precisely. No full scientific end-to-end pass may be claimed until actually observed.

## Run the current starter tests

```bash
python3 -m unittest discover -s tests -v
bash -n start.sh
python3 neuro_easy.py doctor
```

The current install commands are in README.md. Read and improve them before execution; this starter has not yet been proven in Linux. The full user-request prompt is IMPLEMENTATION_PROMPT.md.

## Completion criteria

A novice can clone/download the repository on the supported Ubuntu target, run one clear setup/menu entry point, see actionable prerequisites, launch SWANe, prepare/run MELD, and locate results. Each installation and analysis claim has actual evidence. Licences and data remain local. README states supported versions and the limits of testing. The final report includes exact GitHub commit and any remaining native-laptop acceptance work.
