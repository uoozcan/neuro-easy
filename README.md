# Neuro Easy â€” development starter

One terminal menu for **MELD Graph** and **SWANe**. This is an initial launcher, not a validated neuroimaging distribution. The applications have NOT been installed or tested in Ubuntu in the authoring session. No SWANe-to-MELD data handoff is implemented.

## Plan and acceptance

| Stage | Deliverable | Current state |
| --- | --- | --- |
| Research | Official installation routes and version candidates | Reviewed; links below |
| Launcher | Configuration, menu, isolated SWANe install, MELD Compose wrapper | Implemented; offline checks only |
| WSL inventory | Ubuntu, RAM, disk, display, Docker | Blocked: Wsl/E_ACCESSDENIED |
| Actual installation | SWANe and imaging dependencies; MELD image/model | Not run |
| Application checks | SWANe import, GUI and dependency checks | Not run |
| MELD verification | Official prepare_classifier and pytest | Not run |
| Scientific end-to-end | Raw public MRI to inspected outputs for each application | Not run; SWANe module/dataset selection needed |
| Distribution | GitHub source published; clean Ubuntu reproduction pending |

## Ubuntu / WSL setup

Use Ubuntu with Python >=3.10 (Ubuntu 22.04/24.04 are candidate targets, not yet validated here). WSL is for development; repeat acceptance tests on the friend's native Ubuntu laptop. MELD documents Windows WSL2 but also cautions against general virtual-machine use. Its documentation recommends at least 24 GB RAM for CPU prediction and estimates a ~13 GB image. Allow additional space for software, models, data and outputs; check actual Docker and data disks. SWANe needs a working desktop display; test WSLg separately.

In a normal Windows PowerShell terminal, run `wsl --list --verbose`. Then open your Ubuntu distribution and work in `~/projects/neuro-easy` (copy this folder there). Do not reinstall/reset WSL to work around this session's access restriction.

Install Ubuntu prerequisites after reviewing the package list:

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip git dcm2niix graphviz
```

Install Docker Engine and the Compose plugin using Docker's official Ubuntu guide, or enable Docker Desktop's integration for your WSL2 distribution. Docker must be usable by the current Ubuntu user. This starter does not change Docker group membership. It does not install FSL, FreeSurfer, Slicer or their GUI/system dependencies: follow the selected SWANe release's dependency guide before claiming a complete installation.

Download the official **MELD Graph v2.2.7** release archive from its release page and extract it outside this repository. Review its compose.yml. For CPU mode remove the GPU reservation section as the MELD documentation describes. Obtain your own FreeSurfer `license.txt` and MELD `meld_license.txt` and put them in that extracted release directory. They must never be committed.

```bash
python3 neuro_easy.py configure --meld-release "$HOME/apps/meld_graph_2.2.7" --data "$HOME/neuro-data/meld" --swane-version 0.2.1.1
python3 neuro_easy.py doctor
bash start.sh
```

Replace the MELD directory with the actual folder containing compose.yml. Configuration creates the data directory and stores settings under ignored `local/`. The original release compose file remains the base configuration; the launcher overrides its /data mount. After pulling its image, the launcher records the registry digest and uses it for subsequent runs. The initial upstream image reference may be mutable: confirm its correspondence to the selected release before installation. Fully locked transitive Python dependencies remain future work; pip freeze records what was installed.

## Command sequence and verification

```bash
python3 neuro_easy.py install-swane
python3 neuro_easy.py swane-smoke
python3 neuro_easy.py open-swane
python3 neuro_easy.py install-meld
python3 neuro_easy.py prepare-meld
python3 neuro_easy.py test-meld
```

The SWANe package goes into `local/swane-env`; no system Python packages are changed. An import pass is not a GUI or imaging-workflow pass. Opening SWANe requires interactive inspection and configuration of external tools. The older PyPI release may not match features documented on the current development branch.

MELD preparation downloads models and official test data. `test-meld` executes upstream pytest and writes its status to `local/meld-test.json`. A prior pass is cleared before a new attempt. It does not test SWANe, validate clinical use, or necessarily exercise reconstruction from raw MRI. Inspect which upstream tests actually ran and ensure none required for acceptance were skipped.

For your own deidentified data, organize the data directory using MELD's documented MELD/BIDS structure, then run:

```bash
python3 neuro_easy.py run-meld --subject sub-001
```

This invokes the official pipeline. This starter does not yet validate NIfTI headers/BIDS structure, collect a full provenance report, or check scientific output quality. First establish the official test-data pass. Select and validate a SWANe module separately before adding any integrated workflow.

## Troubleshooting

* Wsl/E_ACCESSDENIED in this chat: run the inventory in your normal terminal and continue in a session with access to Ubuntu. No application was installed by that failed check.
* Docker absent/unreachable: confirm `docker info` and `docker compose version` work in Ubuntu; check Desktop integration or Engine service.
* venv creation fails: install the Ubuntu python3-venv package matching your interpreter.
* SWANe Qt/display or missing imaging-tool errors: follow its release-specific dependency guide and verify the display. Do not set offscreen mode and call that a GUI test.
* MELD licence error: verify your own nonempty files are in the extracted release folder and inspect the upstream release's mount configuration.
* Out of memory/disk: inspect both WSL limits and Docker's resource limits; data and Docker may be on different filesystems. The doctor reports only the filesystem containing this starter.

## Developer tests and GitHub

```bash
python3 -m unittest discover -s tests -v
```

These tests use fake subprocesses where needed. They test launcher behavior, not installed applications. The CI repeats these checks on Ubuntu only; it does not download MRI models or claim analysis validation.

Before publishing, inspect `git status` and staged files. Publish source and docs only. Do not upload local/, data, licences, images or logs. The source repository is published at https://github.com/uoozcan/neuro-easy; application validation remains pending. See IMPLEMENTATION_PROMPT.md for the complete continuation brief.

## Official references

* MELD installation/licences/verification: https://meld-graph.readthedocs.io/en/latest/install_docker.html
* MELD inputs/prediction: https://meld-graph.readthedocs.io/en/latest/run_prediction_pipeline.html
* MELD releases: https://github.com/MELDProject/meld_graph/releases
* SWANe repository and dependency links: https://github.com/LICE-dev/swane
* SWANe published package: https://pypi.org/project/swane/
* Docker Ubuntu installation: https://docs.docker.com/engine/install/ubuntu/

Official pages were reviewed on 2026-11-10. Version candidates are not a tested compatibility matrix. Third-party software retains its own licensing requirements.
