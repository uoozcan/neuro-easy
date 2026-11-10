# Verification report — 2026-11-10

This report supersedes the original restricted Windows-session inventory. Installation, mocked launcher regression, GUI, reference preprocessing and full MRI-to-report acceptance are separate scopes.

## Environment actually inspected

- Distribution: Ubuntu-20.04, WSL2; Ubuntu 20.04.6 LTS, x86_64; kernel 6.18.58.1-microsoft-standard-WSL2.
- CPU: Intel i7-10750H, 12 logical CPUs.
- WSL memory: 15.5 GiB RAM, 4 GiB swap. MELD recommends at least 24 GB RAM for CPU prediction.
- Initial Linux free space: 867 GiB on the WSL virtual filesystem; Windows D: 172 GiB free. The WSL virtual disk is on Windows C:, which had 90.9 GiB physically free during installation. These are separate capacities.
- System Python: 3.8.10. Existing Miniconda Python 3.11.14 was used to create local/swane-env; conda base and pre-existing environments were not modified.
- WSLg: DISPLAY=:0, WAYLAND_DISPLAY=wayland-0. Real windows were inspected using the Windows computer-use API.
- Original sandbox Wsl/E_ACCESSDENIED was resolved by using authorized elevated terminal access; WSL itself was not reset.

## Observed passes

1. Clone and official source/release inspection: repository cloned to /home/umut/projects/neuro-easy. MELD v2.2.7 commit e523c9de4677cfc46efe97069fe59442be160788; release archive SHA-256 e7db6152de57eb1a51e25042f7d2a3e2cff76cc8c6db727669da6bb52d5b46e2. Service meld_graph, image meldproject/meld_graph:v2.2.7, /data mount and both Docker secret licence paths verified in the actual release. Source test_freesurfer invokes recon-all -dontrun and rejects 7.3/7.4; it does not reconstruct a raw MRI.
2. SWANe installation: isolated Python 3.11 venv; swane==0.2.1.1 from PyPI. Selected wheel SHA-256 f69072597fd8b073525aaecbff77fd20d1b8d8bd6de37fb1f509e19a8a8f4ae1. Actual package versions are recorded in requirements-swane-py311.lock and local install reports.
3. bash start.sh swane-smoke: pip check and import succeeded, exit 0. This is package evidence only.
4. Real SWANe GUI: launched through bash start.sh open-swane using WSLg/XCB. Visually inspected the working-directory prompt, configuration wizard and main Home window. After dependency installation the visible Home window showed green checks for dcm2niix v1.0.20250505, FSL 6.0.7.8 and Graphviz. FreeSurfer was missing; Slicer discovery had not established an installation. No offscreen mode was used.
5. Actual release dependency checks: bash start.sh swane-dependencies, exit 0 after setup. dcm2niix/FSL/Graphviz detected; FreeSurfer missing. The new t1_runtime check covers bc, dc and the FSL commands the reference subworkflow invokes.
6. Partial FSL installation: user explicitly accepted the FSL licence. A separate conda environment contains components pinned from the official 6.0.7.8 Linux manifest, plus fsl-installer 3.21.0 for command wrappers. local/fsl-explicit.txt records all packages. This is not a full FSL/module installation. The classic conda solver was interrupted after a slow solve; the installed libmamba solver completed the isolated transaction.
7. Docker: official local static 29.9.3 and checksum-verified Compose 5.7.0. docker run --rm hello-world ran successfully, exit 0; digest sha256:c567b231f65614688711a75f31518a064258a51d442117a3e771a3a8fdba78ef.
8. CPU Compose: bash start.sh meld-config passed with actual Compose. The generated single normalized configuration preserves resolved secrets, overrides /data and removes GPU reservations; the original upstream file was not edited.
9. Offline source checks: 21 unittest cases passed on Ubuntu Python 3.11.14, exit 0. Cases include independent SWANe setup, CPU model generation, digest retention/invalidation, licence guard, resource guard, subject argument safety, preserved subprocess exit code and interrupted/failed status replacement. External application calls are mocked in these tests.
10. Bash syntax, Python compilation and menu quit smoke checks passed. FSL setup without explicit licence acceptance returned 2 without starting installation. Action-specific SWANe T1 readiness returned 0 after dependencies were installed.

## Real public-MRI test

Candidate: SWANe 0.2.1.1 ref_workflow, conventional 1 mm T1w MPRAGE on a Siemens Prisma 3T VE11.
Dataset: https://github.com/neurolabusc/dcm_qa_mprage, commit ffc4fd6edc37cac769d69740185bdb1306b5a3fb, In/6_T1_mprage_ns_sag_p2.zip.
Licence: repository BSD-2-Clause; retained locally alongside provenance.
Archive SHA-256: 558335329ca94dd5d2e85d1c3d4c9ef2682f2acf8a92bba81a60e50999f7402e.

Command:

```bash
bash start.sh validate-swane-t1 \
  --dicom "$PWD/local/public-t1/dicom/6_T1_mprage_ns_sag_p2" \
  --output "$PWD/local/swane-t1-validation"
```

First actual attempt: converted 192 real DICOM slices, reoriented and cropped the volume, then failed in BET because dc was missing. Exit nonzero; validation.json recorded FAILED with the actual traceback. Original result and log were preserved locally. After apt installed dc, the retry reused completed nodes, finished robust BET and reached N4 bias correction.

Conversion-reference check: converted NIfTI shape (192, 256, 256), affine and voxel values exactly match the upstream reference; maximum affine difference 0.0. Canonical comparison after SWANe reorientation also preserves geometry and all voxel values. A 15-slice BET overlay was visually inspected: no gross brain truncation was apparent in the sampled views; small anterior extracerebral remnants remain. This is limited QC without a ground-truth segmentation.

Final result: PASSED for the T1 reference subworkflow, exit 0. Five nonempty outputs were produced: reference, brain reference, binary brain mask, uncorrected reference and uncorrected brain reference. All image data are finite; all five share shape (192, 256, 170), 1 mm voxel spacing and matching geometry. The brain image equals the corrected reference multiplied by the mask. Mask volume is 1577.925 mL. Orientation is LAS.

The successful retry took 1447.89 seconds (24.1 minutes), with 738.8 MiB peak self RSS and 611.5 MiB peak child RSS reported separately. This includes cached conversion/cropping from the first failed attempt; it is not a fresh uncached runtime for the entire pipeline. The first attempt took 231.56 seconds. The final checksum-aware harness was then executed against the completed same-input cache, passed again in 14.55 seconds, recorded hashes for 192 input files and all five outputs, and verified output geometry/masking again.

The final N4-corrected mask overlay was also visually inspected. No gross truncation was apparent in the 15 sampled orthogonal slices; small anterior extracerebral remnants remain. No ground-truth segmentation accuracy was measured. Local validation-full-run.json preserves the full retry's metrics; validation.json and visual-qc.json record the final checks and limited visual assessment.

This subworkflow has no inter-modal/atlas registration, cortical reconstruction or Slicer export. It cannot establish complete SWANe study acceptance or clinical accuracy.

## Clean-source reproduction

A clean local Git clone created a fresh isolated SWANe environment under its own ignored local/. Python 3.11.18 installed the full recorded lock; pip freeze exactly matched requirements-swane-py311.lock. pip check and SWANe import passed, exit 0. The cloned source regression suite also passed. This was a new source checkout and venv on the same existing WSL distribution, not a clean OS or native-laptop scientific reproduction.

## MELD and remaining blockers

Image installation completed, exit 0. Immutable image:
meldproject/meld_graph@sha256:c02adca0cf8e647762f7d09705bc1718079b190794a926b38d1521a6bb72c0ef.
The observed Linux amd64 image size is 18,243,989,272 bytes. A real licence-independent container smoke check ran in /app with Python 3.9.25, imported numpy/torch/meld_graph, and reported torch 1.10.0+cu102. No GPU device was requested; this is the upstream CPU release.

After image installation, actual prepare-meld and test-meld attempts returned 1 with "Obtain your own license.txt and place it in the MELD release folder." doctor --for meld-run returned 2 with missing meld_licenses and meld_recommended_ram. Upstream prepare_classifier and pytest were not executed past that prerequisite guard, and pytest collection/skips remain unobserved.

The user stated they have neither personal MELD nor FreeSurfer licence files. No unrelated private folders were searched. No substitute licence was used. MELD preparation, upstream pytest and raw-MRI-to-report execution cannot proceed without them.

WSL has 15.5 GiB RAM, below the configured 24 GiB MELD prediction guard. The current machine allocation has not been changed. Image installation and source/configuration inspection do not establish a scientific MELD pass.

SWANe FreeSurfer/MATLAB/Slicer modules and complete study/report export remain unexecuted. Native Ubuntu 22.04/24.04 laptop reproduction also remains unexecuted.

## Dedicated WSL Docker test daemon

The test daemon has project-local binaries, socket and storage. It is not a system service. To restart from Windows PowerShell after it has stopped, run the following in a separate terminal and keep it running:

```powershell
wsl -d Ubuntu-20.04 -u root -- bash -lc 'export PATH=/home/umut/projects/neuro-easy/local/tools/docker:$PATH; exec dockerd --host unix:///home/umut/projects/neuro-easy/local/docker.sock --group umut --data-root /home/umut/projects/neuro-easy/local/docker-data --exec-root /run/neuro-easy-docker --pidfile /run/neuro-easy-docker.pid --bip 192.168.231.1/24 --default-address-pool base=192.168.232.0/21,size=24'
```

The custom subnet avoids WSL's startup warning about 172.17.176.0/20 overlapping Docker's default bridge. This does not change WSL's networking configuration.

## Publication

Draft PR: https://github.com/uoozcan/neuro-easy/pull/1. GitHub Actions run 42842223591 passed the existing Ubuntu 22.04/Python 3.10 launcher tests and Bash syntax check for commit 3d4ad589466791007cf834fb53158c9c8b515f66. The proposed workflow expansion could not be pushed because the CLI OAuth credential lacks workflow scope, so the original workflow is preserved. Latest commit/CI and completed live-test evidence will be added after the remaining runs finish. No full scientific end-to-end pass is claimed.
