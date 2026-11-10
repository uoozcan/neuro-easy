# MELD and FreeSurfer installation/activation plan

Status checked 2026-11-10. This continues the existing Ubuntu WSL installation.

## Versions and separation

| Use | Version | Current state |
| --- | --- | --- |
| MELD Graph | v2.2.7 CPU, pinned registry digest in VERSIONS.md | Image installed; runtime imports/Compose/RAM checked |
| FreeSurfer used by MELD | 7.2.0 inside the existing MELD image | Files already bundled; personal licence and operational checks pending |
| Standalone FreeSurfer for SWANe | 7.4.1 official Ubuntu 20.04 archive | Installer prepared/dry-run only; not downloaded or installed |
| SWANe | 0.2.1.1 | Already installed and tested as described in TEST_REPORT.md |

Do not substitute standalone FreeSurfer 7.4.1 into MELD. The selected MELD source explicitly rejects 7.3/7.4; it uses the bundled 7.2.0. A separate native installation is not needed merely to run MELD's Docker workflow.

## 1. Complete personal registration

The actual user must read/accept the terms and register personally:

- [FreeSurfer registration and licence](https://surfer.nmr.mgh.harvard.edu/registration.html): receive your personal license.txt.
- [MELD Graph registration](https://docs.google.com/forms/d/e/1FAIpQLSdocMWtxbmh9T7Sv8NT4f0Kpev-tmRI-kngDhUeBF9VcZXcfg/viewform): receive meld_license.txt.

Do not paste licence contents into chat or GitHub. Save the two files locally and give the assistant their exact paths. No licence file or acceptance has been invented. FSL acceptance already provided earlier is separate from FreeSurfer acceptance.

The configured MELD licence destination in this WSL checkout is:
`/home/umut/projects/neuro-easy/local/meld-release/`.

For access from Windows Explorer:
`\\wsl.localhost\Ubuntu-20.04\home\umut\projects\neuro-easy\local\meld-release`.

## 2. Import licences privately

```bash
cd /home/umut/projects/neuro-easy
bash start.sh license-status
bash start.sh import-licenses \
  --freesurfer /path/to/your/license.txt \
  --meld /path/to/your/meld_license.txt
```

Each option may be supplied separately as its file becomes available. Windows paths must be expressed as WSL paths, such as /mnt/c/Users/.../Downloads/license.txt.

The importer checks all supplied files before changing either installed file, removes an optional UTF-8 BOM, installs with mode 600, and privately backs up any replaced file under ignored local/. Contents are never printed. File syntax checks do not establish registration validity or analysis success. An operational upstream check is still required.

MELD's upstream licence module can exit with code 0 on malformed input; the launcher therefore rejects a missing/non-six-digit MELD License ID before calling upstream. FreeSurfer licence structure is checked conservatively without printing the values.

## 3. Activate and validate the existing MELD installation

Once both genuine personal licence files are installed:

```bash
bash start.sh doctor --for meld-run
bash start.sh prepare-meld
bash start.sh test-meld
```

Execute these sequentially. Preparation downloads upstream models and official test data. Capture actual exit codes, model/test-data paths, runtime and resource use. Inspect pytest collection, failures and skips. Upstream verification may reuse preprocessed input; a pass does not establish raw-MRI reconstruction.

Then run one independently licensed/public/deidentified raw-MRI subject through MELD's documented input layout. Check nonempty prediction volumes, geometry, reports and visual reconstruction/registration quality before claiming the raw-MRI workflow passed. Do not reuse SWANe FreeSurfer surfaces without independent compatibility validation.

The current WSL ceiling is 25 GiB; Ubuntu and an actual container expose 24.4558 GiB. Close memory-heavy Windows applications before prediction on this 31.82 GiB physical host. Do not run memory-heavy SWANe/FreeSurfer and MELD jobs concurrently.

## 4. Install standalone FreeSurfer for SWANe

Prepared profile: official FreeSurfer 7.4.1 Ubuntu 20.04 archive, approximately 8.9 GB compressed, separate destination local/apps/freesurfer-7.4.1. The dry-run observed 844.2 GiB virtual Linux free space and 85.8 GiB on the actual Windows backing drive. Recheck immediately before downloading; the installer requires at least 40 GiB in both locations.

```bash
bash start.sh install-freesurfer --plan --host-storage /mnt/c
# Only after personally accepting the FreeSurfer licence:
bash start.sh install-freesurfer --accept-freesurfer-license --host-storage /mnt/c
```

The installer selects the official Ubuntu 20.04/22.04 x86_64 profile, resumes downloads, verifies the upstream published MD5 and records SHA-256. It safely extracts into project-local staging and refuses to replace an existing installation. It never changes system Python, conda base, .bashrc or the MELD container.

The published Ubuntu 20.04 archive MD5 is f735655a88b0a5e05bef4ab73d991e3d. MD5 here is an upstream download-integrity check; the observed SHA-256 is recorded separately. Full download/extraction remains unexecuted until actual licence acceptance is provided.

## 5. Configure/test standalone tools after unpacking

Review the installed SetUpFreeSurfer.sh, then use its official setup in a dedicated terminal with a separate SUBJECTS_DIR. Point FS_LICENSE to your own personal licence file. Keep this shell separate from MELD.

```bash
export FREESURFER_HOME="$PWD/local/apps/freesurfer-7.4.1"
export FS_LICENSE="$PWD/local/meld-release/license.txt"
mkdir -p "$PWD/local/swane-freesurfer-subjects"
export SUBJECTS_DIR="$PWD/local/swane-freesurfer-subjects"
source "$FREESURFER_HOME/SetUpFreeSurfer.sh"
recon-all -version
```

Check runtime shared libraries and an official licence-requiring MRI utility test before claiming operational readiness. Then run the installed SWANe release's dependency checks in that correctly configured environment. MATLAB Runtime and Slicer are separate module/export dependencies; install only from their official sources when the selected analysis needs them. FreeSurfer 7.4.1 does not enable SWANe's newer >=8.1 Synth options.

A version command, unpacked binaries, a package import or an offline test is not a reconstruction pass. Classical recon-all and any SWANe FreeSurfer module must receive actual MRI validation and visual QC.

## Evidence and next resume

The current software, RAM, GUI and T1-reference evidence is in TEST_REPORT.md.
The two personal licence files are still absent from the configured MELD destination.
Registration/acceptance questions are pending with the user.
No licence-requiring MELD/FreeSurfer scientific step has been claimed as passed.

Official sources: [MELD Docker installation](https://meld-graph.readthedocs.io/en/latest/install_docker.html),
[FreeSurfer download/install](https://surfer.nmr.mgh.harvard.edu/fswiki/DownloadAndInstall),
[FreeSurfer Linux setup](https://surfer.nmr.mgh.harvard.edu/fswiki/LinuxInstall),
[official release archives/checksums](https://surfer.nmr.mgh.harvard.edu/fswiki/rel7downloads).
