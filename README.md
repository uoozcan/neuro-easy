# Neuro Easy

One Ubuntu menu for independent **MELD Graph** and **SWANe** workflows.

Development checkout: `~/projects/neuro-easy` in Ubuntu WSL2. Read [CODEX_HANDOFF.md](CODEX_HANDOFF.md) to continue development and [TEST_REPORT.md](TEST_REPORT.md) for observed evidence and [VERSIONS.md](VERSIONS.md) for exact versions. This is a development launcher; complete MRI-to-report validation and native-laptop acceptance remain pending.

## What has been exercised

- Ubuntu 20.04 WSL2: isolated SWANe 0.2.1.1 installation, package checks and a visually inspected WSLg GUI.
- The installed application's own checks detect dcm2niix, partial FSL 6.0.7.8 and Graphviz.
- Real Docker hello-world and CPU Compose configuration checks pass.
- The real public T1 DICOM reference subworkflow completed and its outputs were inspected; see TEST_REPORT.md.
- Offline CI tests launcher behavior only. It does not validate either scientific application.

Ubuntu 22.04/24.04 are candidate native targets. Current Docker apt documentation supports them; it no longer lists Ubuntu 20.04. Do not upgrade/reset an existing WSL distribution as part of this setup. The local Ubuntu 20.04 development session uses isolated official Docker static binaries; that test setup needs manual updates and is not the recommended laptop installation route.

## Start on Ubuntu

Use a Linux filesystem directory, separate from your MRI data:

```bash
git clone https://github.com/uoozcan/neuro-easy
cd neuro-easy
sudo apt update
sudo apt install python3 python3-venv git graphviz xclip tcsh bc dc \
  libegl1 libxcb-cursor0 libxkbcommon-x11-0 libxcb-icccm4 \
  libxcb-image0 libxcb-keysyms1 libxcb-render-util0
bash start.sh
```

The menu finds an existing Python >=3.10, including a supported interpreter in ~/miniconda3 or ~/miniforge3. It creates its own venv and never installs packages into conda base or system Python. If no supported Python exists, install one separately or use official Miniforge and set `NEURO_PYTHON=/path/to/python`. Existing environments are preserved.

The same entry point accepts commands:

```bash
bash start.sh doctor --for computer
bash start.sh install-swane
bash start.sh swane-smoke
bash start.sh open-swane
```

SWANe does not require any MELD configuration. Package installation includes dcm2niix. `requirements-swane-py311.lock` records the actual Python 3.11 environment; use `bash start.sh install-swane --locked` with Python 3.11 for pinned transitive versions. Other supported Python versions resolve dependencies separately and are not covered by that lock.

Logs, pip reports, installed versions, action status and all local configuration are under ignored `local/`. Rerunning installation resumes using the same project environment. A failure preserves the subprocess exit code; Ctrl+C records INTERRUPTED. Repeated scientific runs can reuse Nipype's completed-node cache only when the input checksums match. Changed inputs require a fresh output directory.

## SWANe T1 reference dependencies

The published 0.2.1.1 release requires FSL for the selected T1 workflow. Its newer development branch and installer have different requirements; this launcher does not install unreleased SWANe code.

Read the [FSL licence](https://fsl.fmrib.ox.ac.uk/fsl/docs/license.html) yourself. FSL installation requires your explicit acceptance. With an existing conda installation:

```bash
bash start.sh install-fsl --conda "$HOME/miniconda3/bin/conda" --accept-fsl-license --locked
bash start.sh swane-dependencies
bash start.sh doctor --for swane-analysis
bash start.sh open-swane
```

The tested linux-64 package set is recorded in requirements-fsl-linux-64.lock; --locked reuses those exact public package URLs. The FSL installer uses official FSL/conda-forge channels in a separate local/fsl-env. It pins the requested components to the official 6.0.7.8 release manifest and installs FSL's wrapper generator. This is a **partial FSL installation for T1 reference preprocessing**, not every SWANe module. The launcher exposes FSL's command wrappers without putting FSL's Python ahead of SWANe.

For an existing compatible FSL installation, use `bash start.sh configure --fsl-dir /path/to/fsl`. FSL also needs en_US.utf8 available in `locale -a`; if absent, generate it using Ubuntu's locale tools. FreeSurfer >=7.3.2, its personal licence, MATLAB Runtime and 3D Slicer >=5.2.1 are additional dependencies for applicable SWANe analyses/export; they have not been installed or validated here. MELD's bundled FreeSurfer is separate and is not reused.

### Reproduce the public T1 reference test

The candidate is a real 1 mm Siemens Prisma 3T MPRAGE series from [neurolabusc/dcm_qa_mprage](https://github.com/neurolabusc/dcm_qa_mprage), pinned to commit ffc4fd6edc37cac769d69740185bdb1306b5a3fb. Its repository has a BSD-2-Clause licence. The fetcher checks the archive's SHA-256 and retains the source licence locally.

```bash
local/swane-env/bin/python tools/fetch_public_t1.py
bash start.sh validate-swane-t1 \
  --dicom "$PWD/local/public-t1/dicom/6_T1_mprage_ns_sag_p2" \
  --output "$PWD/local/swane-t1-validation"
```

This calls the installed release's actual ref_workflow: DICOM conversion, radiological reorientation, neck/FOV cropping, robust BET, N4 correction and masked reference export. It uses CPU, two ITK threads and the release's BET threshold 0.3. It does not run registration, cortical reconstruction, other modalities or Slicer export.

Inspect `local/swane-t1-validation/outputs/`, `validation.json` and `mask-qc.png`. Automated checks require nonempty finite images, matching output geometry, a nonempty binary mask and consistency of the masked reference. A human must inspect the mask and image orientation. A passing subworkflow does not establish scientific accuracy or complete-study acceptance. Never commit these images or logs.

## MELD and FreeSurfer continuation

Follow [INSTALLATION_PLAN.md](INSTALLATION_PLAN.md) for personal registration, private licence import, activation of the already installed MELD image and the separately prepared standalone FreeSurfer 7.4.1 profile. The standalone installer is prepared and guarded; it has not been executed yet.

```bash
bash start.sh license-status
bash start.sh import-licenses --freesurfer /path/license.txt --meld /path/meld_license.txt
bash start.sh install-freesurfer --plan --host-storage /mnt/c
```

## MELD Graph CPU

Install Docker Engine/Compose using the [official Ubuntu guide](https://docs.docker.com/engine/install/ubuntu/) or enable Docker Desktop's WSL integration. Verify `docker info`, `docker compose version` and `docker run --rm hello-world` as your Ubuntu user.

Download/extract the [official v2.2.7 CPU release](https://github.com/MELDProject/meld_graph/releases/tag/v2.2.7) outside tracked source, then configure it:

```bash
bash start.sh configure --meld-release "$HOME/apps/meld_graph_2.2.7" \
  --data "$HOME/neuro-data/meld"
bash start.sh meld-config
bash start.sh doctor --for meld-install
bash start.sh install-meld
```

Compose normalizes the original release configuration, resolves its relative secrets paths, removes GPU reservations and replaces /data in a single generated CPU configuration. The upstream file is not edited. Installation checks >=30 GiB free at the actual Docker storage location and >=10 GiB at the data location, then records the immutable registry digest.

The image can be pulled before licences are available. Running it requires your own nonempty `license.txt` and `meld_license.txt` in the release directory. [Register through MELD's official instructions](https://meld-graph.readthedocs.io/en/latest/install_docker.html); never invent, share or commit licences.

```bash
bash start.sh prepare-meld
bash start.sh doctor --for meld-run
bash start.sh test-meld
bash start.sh run-meld --subject sub-001
```

MELD recommends at least 24 GB RAM for CPU prediction. This development host now exposes 24.46 GiB to Ubuntu and the actual container after a user-approved WSL limit increase. The RAM readiness check passes; personal licences are still required. The launcher refuses prediction/pytest below 24 GiB. Close memory-heavy Windows applications before eventual prediction on this 32 GB host. Preparation also requires the personal licences. Inspect pytest collection, skips and output logs; upstream verification may use preprocessed inputs and does not establish a raw-MRI pass.

Do not feed SWANe reconstructions to MELD without independent version/format validation. No interoperability is implemented.

## Readiness and troubleshooting

`doctor --for` accepts computer, swane-install, swane-gui, swane-analysis, meld-install, meld-run and all. It returns nonzero for missing prerequisites in that scope. The SWANe analysis scope checks the selected T1 components; it does not certify other modules. Default `doctor` checks all.

- GUI: use Ubuntu desktop/WSLg. The launcher uses XCB; offscreen rendering is not a GUI acceptance test.
- FSL BET fails with "dc: command not found": `sudo apt install bc dc`. Readiness now checks these commands separately from the upstream version check.
- Locale error: ensure en_US.utf8 exists.
- Slicer discovery can take a long time because this SWANe release searches the whole filesystem, including Windows mounts. Once Slicer is installed, set its exact path in Application Settings.
- Missing Slicer/FreeSurfer: install/configure the specific external dependency before requesting the corresponding analysis/export.
- Docker unavailable: check daemon/service, current-user socket access and Compose. The isolated WSL development daemon is session-managed; see TEST_REPORT.md for its restart command.
- Space: Linux and Docker/data filesystems are checked separately. WSL's virtual free space can exceed physical host capacity; also check the Windows drive containing ext4.vhdx.
- Interrupted steps: inspect local/last-action.json and local/logs. MELD pytest clears any prior pass before prerequisites or tests are attempted.

## Developer checks

```bash
bash start.sh swane-smoke
local/swane-env/bin/python -m unittest discover -s tests -v
local/swane-env/bin/python -m py_compile neuro_easy.py tools/*.py
bash -n start.sh
printf '12\n' | bash start.sh
```

No MRI, licence, model, environment, downloaded upstream tree or log belongs in Git. Source changes, version records and sanitized test summaries are the publication artifacts.
