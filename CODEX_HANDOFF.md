# Codex continuation brief

Read AGENTS.md, README.md, IMPLEMENTATION_PROMPT.md, TEST_REPORT.md and source before continuing. TEST_REPORT.md's current section supersedes historical blockers.

## Checkout and authorization

Repository: https://github.com/uoozcan/neuro-easy
Active checkout: /home/umut/projects/neuro-easy, Ubuntu-20.04 WSL2, branch codex/wsl-install-validation.
The separate Windows workspace was an empty Git repository and remains separate.
The user authorizes installation, troubleshooting, testing and GitHub updates, including GUI inspection. Continue existing installations; do not reset WSL or replace unrelated environments.

The user explicitly accepted FSL and personally completed both FreeSurfer and MELD registration. Genuine emailed licences were imported into ignored local/meld-release with mode 600. Both syntax checks and actual licensed commands pass. Do not ask again or commit licences/contact details/private registration evidence.

## Installed and validated

- Ubuntu 20.04.6 x86_64, i7-10750H / 12 logical CPUs. Windows physical RAM 31.82 GiB; backed-up .wslconfig ceiling 25 GiB. Ubuntu/container see 24.4558 GiB plus 7 GiB swap. System Python 3.8 is unchanged.
- Isolated local/swane-env: Python 3.11.14, SWANe 0.2.1.1, dcm2niix, Qt. Partial FSL 6.0.7.8 is separate. Apt Graphviz, xclip, tcsh, bc/dc and Qt libraries installed.
- Real SWANe public-T1 reference subworkflow passed with five checked outputs and limited 15-slice QC. Retry reused completed nodes; 1447.89 seconds is not a fresh whole-pipeline benchmark. A separate clean source clone/env reproduced exact Python/FSL locks and package/dependency checks on this same WSL OS.
- Public DICOM GUI import: 192 files match hashes; workflow graph generated and inspected. No GUI-driven scientific execution or Slicer export.
- Official FreeSurfer 7.4.1 Ubuntu20 DEB installed through apt, exit 0, at /usr/local/freesurfer/7.4.1. Official MD5 and observed SHA-256 are in VERSIONS.md. Selected ELF libraries, version and real licensed MRI format roundtrip pass. Actual Freeview WSLg display and linked-plane navigation on the public test T1 also passed (local/freesurfer-validation/native-741/freeview-gui.json). No full native 7.4 reconstruction. Setup reviewed; NO_FSFAST=1 avoids modifying MATLAB startup, FSLDIR is seeded, no .bashrc edits.
- A fresh SWANe WSLg GUI was inspected on 2026-11-11 and detects FreeSurfer 7.4.1/FSL/dcm2niix/Graphviz. The later requested dependency installation completed: MATLAB Runtime R2019b Update 9 (9.7.0.1737446) at /usr/local/freesurfer/7.4.1/MCRv97, and Slicer 5.12.4 revision 34645 under local/apps/Slicer-5.12.4-linux-amd64. SlicerFreeSurfer/SurfaceWrapSolidify extensions are installed and their actual modules load. Fresh SWANe GUI detects both; only the >=8.1 Synth recommendation remains. The exact Slicer path is configured with prior settings backed up; the old GUI was closed and only its lingering read-only find process stopped.
- Local Docker static 29.9.3 / Compose 5.7.0, dedicated local/docker.sock and local/docker-data. Project daemon is session-managed; TEST_REPORT.md has its exact custom-subnet restart command. WSL restarted before the next-day continuation, and only this existing daemon was restarted.
- MELD v2.2.7 CPU pinned image: meldproject/meld_graph@sha256:c02adca0cf8e647762f7d09705bc1718079b190794a926b38d1521a6bb72c0ef. Bundles FreeSurfer 7.2.0; host 7.4 must never replace it.
- Official MELD data SHA-256 f739a9c9b9efbda22dec150a9099929bebb6975177d5dc1771cdb620eb3af466 verified; preparation exited 0. Data/models remain ignored.
- Full upstream pytest completed: 17 collected / 17 passed, no skips, exit 0, 6296.74 pytest seconds, outer 1:53:00. local/meld-test.json and local/logs/meld-upstream-pytest-full.log. Do not rerun it merely to rediscover results.
- Pytest predictions exactly match references, but use preprocessed surfaces/features, -dontrun and --no_report. The bundled input T1 is explicitly an empty placeholder. It is not a raw-MRI test.
- Initial private QA compared prediction grid to the empty placeholder and failed; corrected comparison to FS orig/001.mgz passed. Both records retained.
- Separate actual report-only test generated a four-page PDF from existing predictions and matching supplied MRI, exit 0. All pages rendered and inspected. Headers on pages 2/3 clip in unmodified upstream output; record this limitation. local/meld-report-validation/result.json, no new inference/reconstruction.
- Separate bundled FS7.2 autorecon1 passed on original public T1, exit 0 in 5401.18 seconds. Finite/matching images; limited QC showed no gross sampled truncation and some extracerebral remnants. Not full cortical reconstruction.
- The user personally accepted the exact packaged MATLAB Runtime licence before its agreement step. Vendor installer exit 0, checkMCR exit 0. A deliberate no-argument compiled-runtime probe reaches MATLAB:minrhs and exits 1; this verifies initialization, not segmentation. No global LD_LIBRARY_PATH change.
- SWANe's unmodified T1 Slicer exporter created a 31,736,507-byte MRB. Reload CRC/MRML checks and exact voxel/world-geometry checks passed after explicitly accounting for K reversal +169 index shift. Initial exact-grid failure is retained. Actual Slicer WSLg scene display passed. Extension names are not module identifiers; actual freesurferimporter/segmenteditorwrapsolidify modules were verified. No third-party code patch was needed. See TEST_REPORT.md and local/optional-dependencies evidence.
- Thirty-seven offline regression tests pass, including fail-closed pre/post checks. Bash syntax, Python compilation, diff checks passed. CI remains separate from actual scientific acceptance.

## Active fresh raw-MRI run — inspect, do not duplicate

Launched 2026-11-11 12:31 UTC:

```bash
cd /home/umut/projects/neuro-easy
bash start.sh run-meld --subject sub-publicqa --threads 4 \
  --data "$PWD/local/meld-raw-validation"
```

Actual preflight passed and recon-all started. Fresh original public T1; no host 7.4 surfaces, earlier autorecon1 or SWANe outputs reused. Separate root includes copied official models/parameters. Default noHarmo, no FLAIR. Source: neurolabusc/dcm_qa_mprage commit ffc4fd6edc37cac769d69740185bdb1306b5a3fb, BSD-2-Clause; MRI SHA c18ad5698aba7dad90a50f26840cabb880a05b8eedfeae6fb6319ef9f0450262. No supplied lesion ground truth.

Observe these files:
- local/meld-run-sub-publicqa.json — launcher RUNNING/final exit
- local/logs/meld-public-raw-pipeline.log — outer output/time
- local/meld-raw-validation/output/fs_outputs/sub-publicqa/scripts/recon-all.log — live reconstruction progress
- local/meld-raw-validation/.neuro-easy/sub-publicqa.json — input hashes/image and structural output status
- local/meld-raw-validation/output/predictions_reports/sub-publicqa — eventual prediction/report

Tool session 98765 runs the pipeline; daemon session 27305 and Old GUI session 1969 is closed; new SWANe session 68024, Slicer GUI session 27218, Freeview session 84631. Runtime installer session 73006 finished 0. These are continuation hints, not current-state proof. Container name initially meld-release-meld_graph-run-fa2d0d41814d. Use actual ps/status/logs before acting.

Do not claim full raw-MRI pass until actual final exit, all stages, fresh outputs and visual reconstruction/registration/report QC complete. Structural checks are not clinical accuracy. If upstream exits 0 on a failure, postcheck must reject missing/stale outputs. A negative actual test rejected the empty official T1 with exit 2 and never started analysis.

The new --data option affects only that run and preserves saved configuration. Each Compose invocation now uses a unique ignored local/runs configuration snapshot, avoiding a shared-file race during concurrent commands. The already-active raw run retains its older shared snapshot; do not overwrite local/compose.cpu.json while it runs. tools/check_meld_case.py executes inside pinned MELD: varying finite 3D MRI, safe filenames, input hashes/image, no untracked/changed reconstruction reuse; postcheck requires fresh native-space predictions and PDF. All-zero lesion predictions are valid. Do not delete incomplete output to force a rerun; inspect upstream resume behavior (it refuses incomplete subjects) and preserve evidence first.

## Resources and cleanup

Observed pytest memory reached at least 13.53 GiB, with sampling gaps; true peak unmeasured. Wrapper RSS is Docker client, not application RSS. Timings include concurrent installations/cache troubleshooting and are observational.

Temporary Balanced power scheme was restored to original Power saver at 2026-11-10 21:17 UTC. Actual scheme and local/power-profile-backup.json restore_required=false verified. No paused installer or diagnostic profiler remains. New run preserves the original power scheme; AC/DC sleep timeout is 0 (never). Do not reset WSL while calculations run.

Keep images, models, licences, logs, downloaded sources, environments and local config out of Git. No patient data/contact information in publication.

## GitHub and remaining scopes

Draft PR: https://github.com/uoozcan/neuro-easy/pull/1. Keep draft while scientific/native-laptop acceptance is incomplete; do not merge without instruction. Source commit 5bb246a9ba8c98148c2e0d705bc27d2d80993538 passed GitHub Actions run 43022131830 (37 offline cases). Later documentation-only updates still need their actual head checks observed. The original GitHub Actions workflow remains because CLI OAuth lacks workflow scope; proposed expansion is only ignored local/launcher-expanded.yml.

For CLI push, the working authenticated helper is /home/umut/bin/gh auth git-credential (local gh at /home/umut/bin/gh). Do not print tokens.

Remaining: finish/QC active raw-MRI case; SWANe complete study/reconstruction/export; Synth version/features and complete subfield/multimodal validation; actual native Ubuntu laptop reproduction (requires access to that machine); independently verified interoperability. Do not treat any one completed scope as another.
