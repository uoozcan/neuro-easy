# MELD and FreeSurfer installation/activation plan

Updated 2026-11-10. Continue the existing Ubuntu WSL installation; do not reinstall MELD.

## Versions and separation

| Use | Version | Current state |
| --- | --- | --- |
| MELD Graph | v2.2.7 CPU, pinned digest in VERSIONS.md | Image installed; imports/Compose/RAM checked |
| FreeSurfer used by MELD | 7.2.0 inside the MELD image | Personal licence imported; actual MRI format roundtrip passed |
| Standalone FreeSurfer for SWANe | 7.4.1 official Ubuntu 20.04 DEB | Package download/installation in progress; see TEST_REPORT.md for final observed state |
| SWANe | 0.2.1.1 | Installed; T1 reference test and GUI evidence in TEST_REPORT.md |

MELD's selected source rejects FreeSurfer 7.3/7.4. It retains its bundled 7.2.0 regardless of the host SWANe setup. No SWANe-to-MELD handoff is implemented.

## 1. Personal registration

The user completed [FreeSurfer registration](https://surfer.nmr.mgh.harvard.edu/registration.html). The genuine emailed licence was imported privately with mode 600. Its contents and the user's contact details are excluded from Git.

The user also completed [MELD registration](https://docs.google.com/forms/d/e/1FAIpQLSdocMWtxbmh9T7Sv8NT4f0Kpev-tmRI-kngDhUeBF9VcZXcfg/viewform). The genuine emailed meld_license.txt was imported with mode 600. Both syntax checks pass. The official data archive was SHA-256 verified and extracted; upstream setup with --skip-download-data succeeded. Upstream pytest is running; see TEST_REPORT.md for its final observed result. Never invent registrations or substitute licences.

Configured licence directory:
`/home/umut/projects/neuro-easy/local/meld-release/`.

From Windows Explorer:
`\\wsl.localhost\Ubuntu-20.04\home\umut\projects\neuro-easy\local\meld-release`.

## 2. Licence import for another machine

```bash
cd /home/umut/projects/neuro-easy
bash start.sh license-status
bash start.sh import-licenses --meld /path/to/your/meld_license.txt
```

FreeSurfer can also be imported separately with --freesurfer /path/license.txt. The importer checks all supplied files before writing, normalizes an optional BOM, uses mode 600 and privately backs up replaced files. Syntax checks do not prove operational validity. Never paste licence contents into chat or GitHub.

Upstream MELD can exit 0 on malformed licence input; the launcher rejects malformed/missing six-digit MELD License IDs before executing upstream.

## 3. Activate and validate MELD

For a new machine, once both personal licences are present, run sequentially:

```bash
bash start.sh doctor --for meld-run
bash start.sh prepare-meld
bash start.sh test-meld
```

The observed official data archive is 701,224,128 bytes with SHA-256 f739a9c9b9efbda22dec150a9099929bebb6975177d5dc1771cdb620eb3af466. The first slow container download was deliberately stopped after preserving partial bytes; WSL curl resumed the same official URL, and the digest matched GitHub before extraction. Upstream setup was then run with --skip-download-data.

Capture actual exit codes, model/test-data paths, runtime/resource observations, and pytest collection/failures/skips. Upstream verification may use preprocessed inputs and does not prove a raw-MRI reconstruction pass.

Then run an independently licensed/public/deidentified raw subject using MELD's documented input layout. Inspect predictions, geometry, reports and reconstruction/registration quality before claiming raw-MRI-to-report acceptance. The healthy public T1 used for installation checks is not an FCD detection accuracy benchmark.

Ubuntu and the actual container expose 24.4558 GiB RAM under the 25 GiB WSL ceiling. Avoid simultaneous memory-heavy imaging jobs. Native Ubuntu reproduction remains separate.

## 4. Standalone FreeSurfer for SWANe

Use the vendor-supported Ubuntu DEB installer, rather than unpacking a tar archive or unpacking the DEB manually. The prior archive installer was prepared but never executed.

The pinned 7.4.1 Ubuntu 20 package is 6,687,701,644 bytes, approximately 6.23 GiB. Its official MD5 is 3f488ddc5c1a19fe23bb9cbe2c9f457f. The Ubuntu 22 profile uses MD5 bfe85dd76677cfb7ca2b247b9ac6148e. SHA-256 is also recorded after downloading.

```bash
bash start.sh install-freesurfer --plan --host-storage /mnt/c
# Only after personally accepting the FreeSurfer licence:
bash start.sh install-freesurfer --accept-freesurfer-license --host-storage /mnt/c
```

The installer checks 40 GiB free in the download/system filesystems and WSL's actual backing drive. It verifies checksum and package name/version/architecture before invoking apt. Ubuntu resolves dependencies through apt-get with --no-remove and --no-install-recommends; installation requires sudo. Existing FreeSurfer software is never silently replaced. Downloads remain under ignored local/downloads; the official package installs under /usr/local/freesurfer/7.4.1. System package installation is distinct from the isolated SWANe Python environment.

For download/verification only, add --download-only. A package-verified status is not an installation or runtime pass.

## 5. Configure and check standalone tools

Review the installed official setup script, then configure the launcher:

```bash
bash start.sh configure --freesurfer-dir /usr/local/freesurfer/7.4.1
bash start.sh swane-dependencies
```

The launcher sources the official setup in a child shell, points FS_LICENSE to the imported personal licence unless already supplied, uses ignored local/swane-freesurfer-subjects by default, and reapplies the SWANe/FSL executable paths. It does not modify .bashrc or the MELD image.

For a dedicated manual terminal:

```bash
export FREESURFER_HOME=/usr/local/freesurfer/7.4.1
export FS_LICENSE="$PWD/local/meld-release/license.txt"
mkdir -p "$PWD/local/swane-freesurfer-subjects"
export SUBJECTS_DIR="$PWD/local/swane-freesurfer-subjects"
source "$FREESURFER_HOME/SetUpFreeSurfer.sh"
recon-all -version
```

Check shared libraries, real licence-requiring MRI commands and SWANe detection. A version or format conversion test is not cortical reconstruction. Run actual MRI reconstruction and inspect its outputs/QC before claiming that scope.

FreeSurfer 7.4.1 does not enable SWANe's >=8.1 Synth options. MATLAB Runtime and Slicer remain separate dependencies for applicable modules/export.

## Evidence and resume

TEST_REPORT.md distinguishes offline mocks, installed applications, GUI checks, MRI preprocessing and complete scientific workflows. Keep MRI data, licences, models, logs, environments and private registration screenshots out of Git.

Official sources: [MELD Docker installation](https://meld-graph.readthedocs.io/en/latest/install_docker.html), [FreeSurfer Linux setup](https://surfer.nmr.mgh.harvard.edu/fswiki/LinuxInstall), [official release packages/checksums and package-install guidance](https://surfer.nmr.mgh.harvard.edu/fswiki/rel7downloads).
