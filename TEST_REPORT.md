# Verification report — 2026-11-10

## Observed passes

Command: python -m unittest discover -s tests -v
Environment: Windows host, Python 3.13, this restricted authoring session.
Result: 8 tests passed, process exit 0. Tests exercise configuration paths, invalid release folder, missing/empty licence, immutable image override, Windows installation rejection, unpinned execution rejection, failed-analysis status replacement and subject argument handling. External commands are mocked. No application or scientific validation is implied.

## Observed blockers

wsl --list --verbose: Wsl/E_ACCESSDENIED. No Ubuntu distribution could be inspected.
Direct Python HTTPS request: WinError 10013 socket access forbidden.
Host doctor: Linux=false, Docker command/daemon/Compose=false, display=false, dcm2niix=false, Python >=3.10=true, filesystem free space=106.3 GiB (Windows project disk only). Doctor returned nonzero as expected. This is not the Ubuntu laptop inventory.

## Not executed

Ubuntu installation, Bash menu syntax/runtime checks, dependency resolution for the chosen SWANe version, SWANe GUI launch, module-level SWANe processing, MELD image pull/configuration/preparation, upstream MELD pytest, raw MRI-to-report checks, clean-laptop reproduction and GitHub CI/publication. The upstream release compose file could not be inspected from this session; actual compose merging/licence handling must be checked against the downloaded release before use.

## Next acceptance steps

1. Open an accessible Ubuntu terminal, inventory WSL version, Ubuntu version, architecture, RAM, display and disk locations.
2. Verify SWANe version/module compatibility and install external dependencies from that release's official documentation.
3. Obtain personal FreeSurfer and MELD licences, download/review the chosen official MELD release, configure local paths.
4. Run doctor, application installation and SWANe GUI smoke checks.
5. Run MELD preparation and upstream verification, inspect the collected test cases and any skipped tests.
6. Run selected public/deidentified MRI workflows independently in both applications and inspect expected image/report outputs and registration quality.
7. Repeat on the friend's native Ubuntu laptop, then publish source-only GitHub repository and record Ubuntu CI result.

No full end-to-end pipeline success is claimed.
