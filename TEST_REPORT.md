# Verification report — 2026-11-11

## Current verification — 2026-11-11

This section supersedes earlier licence blockers and in-progress installation statements below. Complete raw-MRI-to-report acceptance is still pending.

| Scope | Observed result |
| --- | --- |
| Personal licences | Both genuine emailed files imported privately, mode 600; syntax checks and actual licensed commands pass |
| MELD preparation | Official data SHA-256 matched; upstream preparation exited 0 |
| Full upstream MELD pytest | 17 collected, 17 passed, no skips, exit 0 |
| Separate report generation | Four-page PDF generated, exit 0; all pages inspected, with header clipping on pages 2/3 |
| Bundled FreeSurfer 7.2 autorecon1 | Public original T1 completed, exit 0; limited visual/numeric QC |
| Standalone FreeSurfer 7.4.1 | Official DEB installed through apt, exit 0; version, selected ELF libraries and licensed MRI conversion pass |
| Fresh SWANe WSLg GUI | Detects FreeSurfer 7.4.1, FSL, dcm2niix and Graphviz; optional dependency warnings remain |
| Offline launcher tests | 37 passed; external application/network calls mocked |
| Fresh raw T1 through MELD | RUNNING; launched 2026-11-11 12:31 UTC, reconstruction started; no final pass |

### MELD preparation and full upstream tests

Official data asset: 701,224,128 bytes, SHA-256 f739a9c9b9efbda22dec150a9099929bebb6975177d5dc1771cdb620eb3af466, matched GitHub metadata. A slow initial container download was deliberately stopped, its bytes preserved, and WSL curl resumed the same URL. The verified archive contained 112 entries / 1,567,506,466 uncompressed bytes; extraction did not overwrite prior data. prepare_classifier.py --skip-download-data exited 0.

Command: /usr/bin/time -v bash start.sh test-meld, in Ubuntu-20.04 using the pinned CPU image in VERSIONS.md. Full upstream pytest collected and passed all 17 tests, including slow tests, with no skips. Pytest reported 6296.74 seconds; outer elapsed was 1:53:00. Actual final exit was 0 at 2026-11-10 20:59:27 UTC. Private log: local/logs/meld-upstream-pytest-full.log; durable status: local/meld-test.json.

This suite uses preprocessed surfaces/features. Its FreeSurfer test uses -dontrun, and prediction passes --no_report. New predictions were generated; the archive only contained expected predictions. Clustered HDF5 differences were zero in both hemispheres, and generated native NIfTI data/affine exactly match the expected result. The suite is not a raw-MRI reconstruction or report-generation pass.

The archive README explicitly states its input NIfTIs are empty placeholders. Inspection confirmed the example T1 has only zeros. An initial QA helper incorrectly compared the prediction grid to that placeholder and failed before starting the planned report. The failure is preserved privately. The corrected comparison uses FreeSurfer mri/orig/001.mgz: matching (256,256,240) grid and affine, finite prediction, 13,047 nonzero voxels. This corrects reference selection; it is not a lesion-accuracy result.

### Separate actual PDF report test

Ran unmodified upstream generate_prediction_report in the pinned container against the newly generated predictions and the real MRI supplied as FreeSurfer orig/001.mgz. A separate /data root held a converted copy of that matching anatomy; original empty input fixtures were unchanged. Models, parameters, preprocessed features and FreeSurfer outputs were mounted read-only. No new inference or raw reconstruction was performed.

Actual exit 0. Output: local/meld-report-validation/output/predictions_reports/sub-test001/reports/MELD_report_sub-test001.pdf, 2,587,769 bytes, four A4 pages. All four pages were rendered with Poppler and visually inspected. Anatomy, cluster overlays, surface views, saliency plots and version page are present. Headers on pages 2 and 3 are clipped in the unmodified upstream output; this is a report-layout limitation, not a polished-report acceptance pass. The original PDF and result.json are retained privately. No clinical interpretation or prediction-accuracy claim is made.

### FreeSurfer operational and MRI checks

Bundled 7.2.0 licensed MRI conversion roundtrip passed: (192,256,170), finite, identical voxel values, affine rounding at most 7.62939453125e-06. A first diagnostic failed because bash -lc reset PATH; the corrected official setup passed.

Separate recon-all -autorecon1 -openmp 4 on the original public T1 completed with exit 0 in 5401.18 seconds, ending 2026-11-10 20:20:39 UTC. orig, nu, T1 and brainmask are finite (256,256,256), 1 mm, matching geometry. Retained mask volume: 1758.635 mL; masked brain intensities equal T1 inside the mask. Fifteen sampled orthogonal slices showed no gross brain truncation and some extracerebral/dural remnants. No ground-truth segmentation accuracy was measured. This is not complete cortical reconstruction. Evidence: local/freesurfer-validation/bundled-autorecon1-result.json and local/logs/freesurfer-bundled-autorecon1.log.

Official standalone Ubuntu 20.04 FreeSurfer 7.4.1 DEB was checksum-verified and installed through apt with 104 dependencies, exit 0. No tar installation was executed and no existing FreeSurfer was replaced. Package size/MD5/SHA-256 are in VERSIONS.md. Installed path: /usr/local/freesurfer/7.4.1; version freesurfer-linux-ubuntu20_x86_64-7.4.1-20230614-7eb8460. Selected ELF dependency checks for mri_convert, mri_watershed, mri_em_register and freeview found no missing libraries. Actual native original-T1 NIfTI -> MGZ -> NIfTI conversion passed: (192,256,256), finite, identical voxel values, maximum affine rounding 4.410743713378906e-06. Evidence: local/freesurfer-validation/native-741/result.json and local/logs/freesurfer-official-apt-install.log. This is not a full native 7.4 reconstruction.

Official FreeSurfer setup was inspected before sourcing. The launcher uses NO_FSFAST=1 to avoid MATLAB startup-file creation, sets FSLDIR consistently, sources setup in a child shell and retains isolated SWANe/FSL paths. It does not edit .bashrc or source host FreeSurfer for MELD.

### GUI, resources and temporary settings

After capture/focus failures, the user brought SWANe forward. The earlier public-T1 workflow graph was visually confirmed. Following the later WSL restart, a fresh FreeSurfer-aware SWANe window was inspected on 2026-11-11. It detects dcm2niix, FSL, Graphviz and FreeSurfer 7.4.1. It correctly warns that >=8.1 is recommended for Synth and optional MATLAB Runtime R2019b is absent. Slicer discovery remains unbounded; Slicer is not installed. Freeview 7.4.1 was then opened on the public T1 from bundled autorecon1. After an initial capture timeout, fresh selection/activation showed all orthogonal MRI planes and 3D slice planes. A coronal click changed the linked cursor from voxel [127,127,128] to [153,133,128] and updated the sagittal/axial views. This establishes actual viewer display/navigation, not native 7.4 reconstruction. A nonfatal WSLg runtime-dir permission warning was retained without broad permission changes. Private evidence: local/freesurfer-validation/native-741/freeview-gui.json. No GUI-driven analysis or Slicer export is claimed.

MELD pytest initially used all CPUs, then an eight-CPU quota. Observed memory reached at least 13.53 GiB in sampled statistics, with gaps; the true peak is unmeasured. The GNU time wrapper RSS is Docker-client memory, not application peak. Concurrent installation, cache reclamation and temporary installer suspension make runtimes observational rather than controlled benchmarks. A diagnostic profiler was canceled and removed; no conclusion was drawn from a native backtrace.

Temporary Windows Balanced selection was reverted to the original Power saver scheme at 2026-11-10 21:17 UTC; both the actual scheme and restore_required=false were subsequently verified. The paused installer was resumed and finished; no paused installer/profiler remains. WSL restarted before the next day's continuation; the existing project daemon was restarted without reinstalling or resetting WSL.

### Fresh raw-MRI validation in progress

Command:

```bash
bash start.sh run-meld --subject sub-publicqa --threads 4 \
  --data "$PWD/local/meld-raw-validation"
```

This uses the original public scanner-QA T1 (source/commit/checksum below), a fresh subject and isolated data root, bundled FreeSurfer 7.2.0, default noHarmo and no FLAIR. No earlier autorecon1, host 7.4 surfaces or SWANe outputs were reused. Input provenance passed; actual recon-all has started. Log: local/logs/meld-public-raw-pipeline.log; status: local/meld-run-sub-publicqa.json. Full reconstruction, feature extraction, inference, report, structural checks and visual QC must finish before acceptance. There is no supplied lesion ground truth.

The launcher now checks actual finite, varying 3D MRI input in the pinned container, rejects the empty example, records hashes/image provenance, refuses untracked/changed reconstruction reuse, and checks fresh prediction/report files after upstream returns. This prevents upstream's zero-exit error paths from becoming false passes. Successful structural checks still require visual reconstruction/registration/report review. Actual negative test with the empty official T1 returned 2 and did not launch analysis. Thirty-seven offline tests pass, including preflight/postcheck failure propagation and per-run data isolation; Bash syntax, Python compilation and git diff checks pass. A real pinned-container postcheck rejected missing artifacts with exit 2; freshly copied actual reference prediction/MRI/PDF passed structural checks (not a fresh inference run). Each Compose invocation now retains a unique private configuration snapshot so another command cannot replace a long-running case's data mount.

Publication: commit 5bb246a9ba8c98148c2e0d705bc27d2d80993538 passed GitHub Actions Launcher tests only run 43022131830. Its 37 offline cases do not validate scientific execution. Draft PR remains https://github.com/uoozcan/neuro-easy/pull/1.

Remaining separate scopes: raw-MRI run completion/QC, SWANe full study/reconstruction/export, optional MATLAB Runtime/Slicer/Synth dependencies, native Ubuntu laptop reproduction and SWANe-to-MELD interoperability. The historical sections below retain prior attempts and blockers; their older licence/installation statements are superseded here.

## Follow-up: RAM allocation and extended GUI inspection

The user authorized increasing WSL RAM if the physical host could support it and requested further GUI inspection.

Windows reports 31.82 GiB physical RAM. The existing .wslconfig was backed up outside Git, its existing settings were preserved, and memory=25GB was added under [wsl2]. Active Ubuntu processes were inspected: they belonged to this setup session, with no running scientific analysis. The project Docker daemon was stopped cleanly. Terminating the distribution alone retained the old VM limit, so WSL was fully stopped and restarted.

Observed after restart: /proc/meminfo reports 26,259,234,816 bytes, or 24.4558 GiB; swap is 7 GiB. The restored Docker daemon reports the same memory, and an actual MELD container Python check reports 24.4558 GiB. doctor --for meld-run now reports meld_recommended_ram=true and only meld_licenses missing (exit 2). The prior 15.5 GiB RAM blocker is resolved. This verifies capacity visibility, not a 24 GiB stress test or MELD prediction. Windows had 4.83 GiB available before the restart; close memory-heavy Windows apps before eventual prediction.

The desktop was unlocked and the real WSLg GUI was reopened. Inspected Application Settings: correct local working directory, structural workflow, CPU/resource controls and CUDA unchecked. FreeSurfer Synth options were disabled as expected. No settings changes were saved during this inspection.

Created local public-t1-qa, scanned the same licensed public DICOM directory, confirmed its automatic 3D T1w association and imported all 192 images as one volume. The GUI showed a green valid-input check and enabled Workflow execution. All 192 imported file content hashes match the source series exactly.

Generated the workflow without executing it. The GUI's expanded step tree showed NIfTI conversion, standard orientation, neck removal, large-FOV cropping, scalp removal, bias correction, masking and saving. The generated SVG is valid XML (9,433 bytes), although Qt logged a transient "Start tag expected" read warning during generation. Execute SWANe Workflow became enabled. No GUI-driven scientific execution or Slicer export is claimed.

GUI limitations: the release's Slicer discovery runs an unbounded find / search; it remained searching and had scanned Windows-mounted filesystems for many minutes in the earlier session. Slicer is still not installed. The subject workflow-preferences popup could not be visually verified reliably through the Windows automation capture (blank capture/invalid transient-window coordinates); it was dismissed with Escape. Main-window import and workflow generation were verified directly.

Only sanitized text evidence is committed. The WSL configuration/backup, imported DICOM data, GUI subject, generated SVG and logs remain local.

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

A clean local Git clone created a fresh isolated SWANe environment under its own ignored local/. Python 3.11.18 installed the full recorded lock; pip freeze exactly matched requirements-swane-py311.lock. pip check and SWANe import passed, exit 0. The latest cloned source regression suite passed all 21 tests, and Python compilation, Bash syntax and menu quit checks passed. The clean clone also installed a separate FSL environment using requirements-fsl-linux-64.lock. All 87 explicit public package URLs matched the original tested environment exactly, FSL wrappers were generated, and its actual SWANe dependency check returned 0 with dcm2niix/FSL/Graphviz/t1_runtime detected. This was a new source checkout and new environments on the same existing WSL distribution, not a clean OS or native-laptop scientific reproduction. The real MRI subworkflow was not rerun uncached in the clean clone.

## MELD and remaining blockers

Image installation completed, exit 0. Immutable image:
meldproject/meld_graph@sha256:c02adca0cf8e647762f7d09705bc1718079b190794a926b38d1521a6bb72c0ef.
The observed Linux amd64 image size is 18,243,989,272 bytes. A real licence-independent container smoke check ran in /app with Python 3.9.25, imported numpy/torch/meld_graph, and reported torch 1.10.0+cu102. No GPU device was requested; this is the upstream CPU release.

After image installation, actual prepare-meld and test-meld attempts returned 1 with "Obtain your own license.txt and place it in the MELD release folder." doctor --for meld-run returned 2 with missing meld_licenses and meld_recommended_ram. Upstream prepare_classifier and pytest were not executed past that prerequisite guard, and pytest collection/skips remain unobserved.

The user stated they have neither personal MELD nor FreeSurfer licence files. No unrelated private folders were searched. No substitute licence was used. MELD preparation, upstream pytest and raw-MRI-to-report execution cannot proceed without them.

The initial 15.5 GiB WSL allocation was below the configured 24 GiB MELD prediction guard. The follow-up above resolves that capacity blocker: Ubuntu and the actual container now see 24.4558 GiB. Missing personal licences still block scientific MELD verification. Image installation and capacity/configuration inspection do not establish a scientific pass.

SWANe FreeSurfer/MATLAB/Slicer modules and complete study/report export remain unexecuted. Native Ubuntu 22.04/24.04 laptop reproduction also remains unexecuted.

## Dedicated WSL Docker test daemon

The test daemon has project-local binaries, socket and storage. It is not a system service. To restart from Windows PowerShell after it has stopped, run the following in a separate terminal and keep it running:

```powershell
wsl -d Ubuntu-20.04 -u root -- bash -lc 'export PATH=/home/umut/projects/neuro-easy/local/tools/docker:$PATH; exec dockerd --host unix:///home/umut/projects/neuro-easy/local/docker.sock --group umut --data-root /home/umut/projects/neuro-easy/local/docker-data --exec-root /run/neuro-easy-docker --pidfile /run/neuro-easy-docker.pid --bip 192.168.231.1/24 --default-address-pool base=192.168.232.0/21,size=24'
```

The custom subnet avoids WSL's startup warning about 172.17.176.0/20 overlapping Docker's default bridge. This does not change WSL's networking configuration.

## Publication

Draft PR: https://github.com/uoozcan/neuro-easy/pull/1. GitHub Actions run 42842223591 passed the existing Ubuntu 22.04/Python 3.10 launcher tests and Bash syntax check for commit 3d4ad589466791007cf834fb53158c9c8b515f66. The proposed workflow expansion could not be pushed because the CLI OAuth credential lacks workflow scope, so the original workflow is preserved. Implementation commit b5e17af801c0ca959c2b75eaf4a28963508315f4 passed GitHub Actions run 42844193187, including the 21-test suite and Bash syntax check. The completed real-MRI and container evidence is recorded above. Subsequent publication changes update documentation only; the current PR head and its checks are visible on GitHub. No full scientific end-to-end pass is claimed.

## MELD/FreeSurfer activation preparation — observed checks

The user requested planning/execution of MELD and FreeSurfer installation. The existing MELD image already bundles FreeSurfer 7.2.0. Rechecked official release/licence documentation and prepared INSTALLATION_PLAN.md. A separate FreeSurfer 7.4.1 profile is for SWANe, not a replacement for the bundled MELD tool.

Actual standalone installer --plan succeeded for Ubuntu 20.04 and showed 844.2 GiB virtual Linux free space / 85.8 GiB backing-drive free space. Running the standalone installer without explicit personal FreeSurfer acceptance returned 2 before downloading. No FreeSurfer archive has been downloaded or unpacked in this phase. Actual licence status reports both configured files MISSING. Personal registration/acceptance and the exact saved file paths are pending from the user.

Thirty offline tests passed on the installed Ubuntu Python 3.11 environment, including new tests for private licence import/backups, all-files-before-write validation, malformed MELD licence rejection, explicit acceptance, corrupted download rejection, preserving existing installation files and archive traversal rejection. Bash syntax, menu quit, Python compilation and git diff checks passed. All application/network calls are mocked in the installer regression tests. No additional MELD or FreeSurfer scientific pass is claimed.
