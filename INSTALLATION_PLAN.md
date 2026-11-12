# MELD and FreeSurfer installation/activation plan

Updated 2026-11-12. Continue the existing Ubuntu WSL installation; do not reinstall MELD.

## Versions and separation

| Use | Version | Current state |
| --- | --- | --- |
| MELD Graph | v2.2.7 CPU, pinned digest in VERSIONS.md | Prepared; all 17 upstream tests passed; raw-MRI attempt stopped, exit 137; leave stopped at user request |
| FreeSurfer used by MELD | 7.2.0 inside the MELD image | Licensed conversion and public-T1 autorecon1 passed |
| Standalone FreeSurfer for SWANe | 8.1.0 official Ubuntu20 DEB | Installed via explicit apt upgrade; configured complete classic T1 reconstruction and CPU SynthStrip output/QC checks pass; 7.4.1 retained as unmanaged fallback |
| SWANe | 0.2.1.1 | Installed; T1 reference test and GUI evidence in TEST_REPORT.md |

MELD's selected source rejects FreeSurfer 7.3/7.4. It retains its bundled 7.2.0 regardless of the host SWANe setup. No SWANe-to-MELD handoff is implemented.

## 1. Personal registration

The user completed [FreeSurfer registration](https://surfer.nmr.mgh.harvard.edu/registration.html). The genuine emailed licence was imported privately with mode 600. Its contents and the user's contact details are excluded from Git.

The user also completed [MELD registration](https://docs.google.com/forms/d/e/1FAIpQLSdocMWtxbmh9T7Sv8NT4f0Kpev-tmRI-kngDhUeBF9VcZXcfg/viewform). The genuine emailed meld_license.txt was imported with mode 600. Both syntax checks pass. The official data archive was SHA-256 verified and extracted; upstream setup with --skip-download-data succeeded. All 17 upstream pytest cases passed; separate PDF generation passed with header-clipping limitations. Fresh raw-MRI acceptance remains pending; see TEST_REPORT.md. Never invent registrations or substitute licences.

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

The fresh original public-T1 attempt in local/meld-raw-validation received SIGTERM then SIGKILL 30 seconds later and ended with exit 137. The user explicitly requested on 2026-11-12 that MELD remain stopped. Preserve its partial outputs; do not resume without new instruction. For another subject, run an independently licensed/public/deidentified raw subject using MELD's documented input layout. Inspect predictions, geometry, reports and reconstruction/registration quality before claiming raw-MRI-to-report acceptance. The public scanner-QA T1 used for installation checks has no supplied lesion ground truth and is not an FCD detection accuracy benchmark.

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

Review the installed official setup script, then configure the launcher. The examples below use this host's upgraded 8.1.0; for a new baseline 7.4.1 installation, substitute 7.4.1 until the explicit upgrade in section 7 has completed:

```bash
bash start.sh configure --freesurfer-dir /usr/local/freesurfer/8.1.0
bash start.sh swane-dependencies
```

The launcher skips MATLAB startup-file creation for this structural profile and sources the official setup in a child shell, points FS_LICENSE to the imported personal licence unless already supplied, uses ignored local/swane-freesurfer-subjects by default, and reapplies the SWANe/FSL executable paths. It does not modify .bashrc or the MELD image.

For a dedicated manual terminal:

```bash
export FREESURFER_HOME=/usr/local/freesurfer/8.1.0
export NO_FSFAST=1  # structural setup; skip MATLAB startup-file creation
export FS_LICENSE="$PWD/local/meld-release/license.txt"
mkdir -p "$PWD/local/swane-freesurfer-subjects"
export SUBJECTS_DIR="$PWD/local/swane-freesurfer-subjects"
source "$FREESURFER_HOME/SetUpFreeSurfer.sh"
recon-all -version
```

Check shared libraries, real licence-requiring MRI commands and SWANe detection. A version or format conversion test is not cortical reconstruction. Run actual MRI reconstruction and inspect its outputs/QC before claiming that scope.

The baseline 7.4.1 profile does not enable SWANe's >=8.1 Synth options; this host completed the explicit 8.1.0 upgrade in section 7. MATLAB Runtime R2019b Update 9 and Slicer 5.12.4 are now installed and detected on this host; other machines still require their own installation.

## 6. MATLAB Runtime and Slicer follow-up

Completed on 2026-11-11 after the user's separate MATLAB Runtime licence acceptance. MATLAB Runtime R2019b Update 9 is installed at /usr/local/freesurfer/7.4.1/MCRv97. checkMCR.sh succeeds and a compiled executable reaches its own MATLAB argument validation. No subfield segmentation is implied.

For another machine, inspect the installed fs_install_mcr script and the exact MathWorks Runtime licence before its silent agreement step. The vendor-supported command is fs_install_mcr R2019b with FREESURFER_HOME set to the intended installation; system-directory installation requires sudo. This session used the same official package via a verified staged download and new target, then placed v97 as MCRv97. Do not globally append its old library paths to the shell profile; FreeSurfer wrappers supply them per process.

Slicer 5.12.4 revision 34645 is under local/apps/Slicer-5.12.4-linux-amd64. Official archive size/SHA-512 are in VERSIONS.md. Ubuntu host libraries added: libpcre2-16-0, libpulse-mainloop-glib0 and libopengl0. The required SlicerFreeSurfer and SurfaceWrapSolidify extensions are installed; their actual module names differ from extension names.

For another machine, download the official Linux archive, compare its publisher checksum before extracting, and install the two extensions through Slicer's Extension Manager. Set the exact Slicer executable in SWANe Application Settings. This host's existing SWANe settings were backed up and updated through ConfigManager; the fresh GUI confirms detection. Keep Slicer's Python/Qt libraries separate from SWANe and MATLAB Runtime.

The unmodified SWANe minimal public-T1 exporter saved a valid scene, which reloaded with exact voxel preservation after accounting for Slicer's signed K-axis reindexing. The real GUI displayed the scene. Complete multimodal export, subfields and full raw-MELD scientific acceptance remain separate tests.

## Evidence and resume

TEST_REPORT.md distinguishes offline mocks, installed applications, GUI checks, MRI preprocessing and complete scientific workflows. Keep MRI data, licences, models, logs, environments and private registration screenshots out of Git.

Official sources: [MELD Docker installation](https://meld-graph.readthedocs.io/en/latest/install_docker.html), [FreeSurfer Linux setup](https://surfer.nmr.mgh.harvard.edu/fswiki/LinuxInstall), [official release packages/checksums and package-install guidance](https://surfer.nmr.mgh.harvard.edu/fswiki/rel7downloads).

## 7. Explicit upgrade from 7.4.1 to 8.1.0

The user authorized this host upgrade; the package installation and subsequent configured T1/classic reconstruction plus CPU SynthStrip checks completed. Check TEST_REPORT.md for actual runtime results. SWANe 0.2.1.1 requires >=8.1 for its Synth options. This does not change MELD's bundled 7.2.0.

For an existing, registered 7.4.1 installation on Ubuntu 20.04/22.04, inspect the plan:

```bash
local/swane-env/bin/python tools/upgrade_freesurfer_810.py --plan --host-storage /mnt/c
```

Download the matching official 8.1.0 Ubuntu DEB from [FreeSurfer downloads](https://surfer.nmr.mgh.harvard.edu/fswiki/rel7downloads) into ignored local/downloads. The Ubuntu20 package is 9,454,809,452 bytes. Check physical free space before downloading; the upgrade additionally requires 30 GiB free after that package is present. On WSL, --host-storage must identify the actual Windows drive containing ext4.vhdx, which can differ from the Windows project drive.

After personally accepting the FreeSurfer licence, run this explicit command for the Ubuntu20 package:

```bash
sudo local/swane-env/bin/python tools/upgrade_freesurfer_810.py \
  --package "$PWD/local/downloads/freesurfer_ubuntu20-8.1.0_amd64.deb" \
  --host-storage /mnt/c --accept-freesurfer-license
```

Use the Ubuntu22 package name on Ubuntu 22.04. This utility verifies the publisher MD5 and package identity, simulates apt with no removals, then preserves the complete old tree with same-filesystem hard links before the official apt upgrade. It never repackages the DEB. Missing 7.4.1 paths are restored in a finally block; conflicting paths are refused. The registered package becomes 8.1.0; retained 7.4.1 files are an unmanaged fallback. The installed MCRv97 is shared by a directory symlink, without changing global library paths or downloading another Runtime.

Do not rerun after an interruption while a target or preservation tree exists. Inspect local/freesurfer-810-upgrade.json and the actual apt/dpkg process first. PACKAGE_INSTALLED means package installation only. Verify version, licensed MRI conversion, selected libraries, MCR startup and the intended Synth workflow before selecting the new directory:

```bash
bash start.sh configure --freesurfer-dir /usr/local/freesurfer/8.1.0
bash start.sh swane-dependencies
```

The launcher defaults host FS_V8_XOPTS=0, retaining classic reconstruction. Official [v8 release notes](https://surfer.nmr.mgh.harvard.edu/fswiki/rel7downloads/rel8notes) describe fast recon-all peaks around 80 GiB; this 25 GiB VM is not a suitable acceptance environment for that mode. An explicit caller value is preserved. Individual Synth tools have different memory requirements and need separate tests; version detection does not validate them. Leave SWANe Synth preferences off until the chosen workflow has been tested. A failed new-version runtime check can be followed by selecting the retained /usr/local/freesurfer/7.4.1 directory; this is configuration fallback, not a dpkg package downgrade.
