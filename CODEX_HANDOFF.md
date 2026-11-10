# Codex continuation brief

Read AGENTS.md, README.md, IMPLEMENTATION_PROMPT.md, TEST_REPORT.md and the source before continuing.

## Working checkout and authorization

Repository: https://github.com/uoozcan/neuro-easy
Active development checkout: /home/umut/projects/neuro-easy in Ubuntu-20.04 WSL2.
The Windows workspace was an empty Git repository and was left separate.
The user authorizes installation, troubleshooting, testing and GitHub updates.
On 2026-11-10 the actual user explicitly accepted the FSL licence and stated they do not have MELD or FreeSurfer licences. Do not ask for FSL acceptance again for this authorized installation. Do not invent or obtain another person's personal licences.

## Observed state

WSL access and HTTPS work when the terminal command runs outside the restricted sandbox. Do not reset WSL.
Ubuntu 20.04.6, x86_64, i7-10750H (12 logical CPUs), initially about 15.5 GiB RAM and 4 GiB swap; after the user-approved memory follow-up, Ubuntu and the MELD container see 24.4558 GiB RAM and 7 GiB swap. The 31.82 GiB Windows host now has memory=25GB in its backed-up .wslconfig.
System Python is 3.8.10. Existing /home/umut/miniconda3/bin/python is 3.11.14 and was used only to create an isolated project venv. Existing conda environments were preserved.
SWANe 0.2.1.1, dcm2niix and partial FSL 6.0.7.8 are installed in local/. Real WSLg GUI inspection shows dcm2niix/FSL/Graphviz detected.
Graphviz, xclip, tcsh, Qt/XCB libraries, bc and dc were installed using apt.
Standalone FreeSurfer for SWANe, MATLAB Runtime and 3D Slicer have not been installed. MELD already bundles FreeSurfer 7.2.0 inside its installed image.

The selected scientific test is SWANe's real T1 reference subworkflow on one licensed public MPRAGE DICOM series. The real reference subworkflow completed with five checked outputs and limited visual QC; TEST_REPORT.md records its timing and acceptance scope. local/swane-t1-validation/validation-full-run.json preserves the full retry, and validation.json records the checksum-aware cached check. The first actual run failed because FSL BET needed dc; that was installed and an actionable readiness check added. The successful retry reused completed Nipype nodes; its observed 1447.89-second runtime is therefore not a fresh uncached whole-pipeline benchmark. A fresh source clone with new SWANe and partial FSL environments also passed dependency/package checks with exact Python/FSL lock matches and 21 launcher tests.

Docker static 29.9.3 and Compose 5.7.0 are local development tools because Ubuntu 20.04 is no longer listed in Docker's current apt support matrix. Real hello-world passed. A dedicated project daemon uses local/docker.sock and local/docker-data; it is session-managed. README/TEST_REPORT describe the restart command. Do not treat this as a native-laptop Docker deployment.

Official MELD v2.2.7 archive and source are under ignored local/. The generated CPU Compose configuration was checked with real Compose. Both licence locations were confirmed as /run/secrets/license.txt and /run/secrets/meld_license.txt. The original release Compose is unchanged. The image is installed at digest sha256:c02adca0cf8e647762f7d09705bc1718079b190794a926b38d1521a6bb72c0ef; a real container import smoke passed. Scientific preparation/pytest are blocked by the personal licence prerequisite.

## Acceptance boundaries

- Offline tests, package checks, visible GUI, T1 reference preprocessing, MELD pytest and complete raw-MRI pipelines are separate acceptance levels.
- Missing personal MELD/FreeSurfer licences block MELD preparation and scientific execution.
- The WSL RAM blocker is resolved: actual container-visible RAM is 24.4558 GiB and meld_recommended_ram=true. The launcher still correctly blocks execution until personal licences are provided. Capacity visibility has been checked; a full memory stress/prediction test has not run.
- SWANe's T1 reference test does not cover registration, cortical reconstruction, multi-modal studies or Slicer reports.
- No SWANe-to-MELD interoperability is implemented.
- Clean native Ubuntu laptop reproduction still requires access to that computer.
- Keep all images, models, licences, logs, downloaded sources and environments out of Git.

## Commands

```bash
cd /home/umut/projects/neuro-easy
bash start.sh doctor --for swane-analysis
bash start.sh swane-smoke
bash start.sh swane-dependencies
bash start.sh open-swane
local/swane-env/bin/python -m unittest discover -s tests -v
bash -n start.sh
```

See TEST_REPORT.md for exact observed results, final GitHub publication and remaining work. Continue from the existing installation; do not reinstall unrelated environments.

## Published continuation

Draft PR: https://github.com/uoozcan/neuro-easy/pull/1 on codex/wsl-install-validation. Source implementation b5e17af801c0ca959c2b75eaf4a28963508315f4 passed GitHub Actions run 42844193187. The draft status reflects incomplete full scientific/native-laptop acceptance. The original CI workflow is preserved because the CLI credential lacks workflow scope; the proposed expanded workflow is only in ignored local/launcher-expanded.yml.

Follow-up GUI inspection imported the 192-image public T1 series into local/swane-work/public-t1-qa and generated the real workflow graph. All imported content hashes match. No GUI analysis was executed. Application Settings were inspected; subject preferences had a capture limitation. Slicer discovery remains an unbounded filesystem search; see TEST_REPORT.md.

## MELD/FreeSurfer activation preparation

Read INSTALLATION_PLAN.md. Personal registration/FreeSurfer acceptance was requested asynchronously; no acceptance or licence paths have been supplied for this phase. The standalone FreeSurfer 7.4.1 installer is prepared and dry-run only, with no software downloaded. It requires explicit --accept-freesurfer-license, checks actual WSL backing-drive space, verifies the upstream archive checksum and stages extraction without replacing existing software. Private import-licenses and license-status commands are implemented; status currently reports both files MISSING. Only syntax is checked, never licence authenticity. Upstream MELD can exit 0 on malformed licence input, so preflight now rejects malformed licence structure before execution. Thirty offline regression cases passed; these are not software/analysis installation passes.
