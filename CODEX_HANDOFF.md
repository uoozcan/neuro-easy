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
Ubuntu 20.04.6, x86_64, i7-10750H (12 logical CPUs), about 15.5 GiB RAM and 4 GiB swap.
System Python is 3.8.10. Existing /home/umut/miniconda3/bin/python is 3.11.14 and was used only to create an isolated project venv. Existing conda environments were preserved.
SWANe 0.2.1.1, dcm2niix and partial FSL 6.0.7.8 are installed in local/. Real WSLg GUI inspection shows dcm2niix/FSL/Graphviz detected.
Graphviz, xclip, tcsh, Qt/XCB libraries, bc and dc were installed using apt.
FreeSurfer, MATLAB Runtime and 3D Slicer have not been installed.

The selected scientific test is SWANe's real T1 reference subworkflow on one licensed public MPRAGE DICOM series. Check TEST_REPORT.md and local/swane-t1-validation/validation.json for its final status. The first actual run failed because FSL BET needed dc; that was installed and an actionable readiness check added. The retry reuses completed Nipype nodes.

Docker static 29.9.3 and Compose 5.7.0 are local development tools because Ubuntu 20.04 is no longer listed in Docker's current apt support matrix. Real hello-world passed. A dedicated project daemon uses local/docker.sock and local/docker-data; it is session-managed. README/TEST_REPORT describe the restart command. Do not treat this as a native-laptop Docker deployment.

Official MELD v2.2.7 archive and source are under ignored local/. The generated CPU Compose configuration was checked with real Compose. Both licence locations were confirmed as /run/secrets/license.txt and /run/secrets/meld_license.txt. The original release Compose is unchanged.

## Acceptance boundaries

- Offline tests, package checks, visible GUI, T1 reference preprocessing, MELD pytest and complete raw-MRI pipelines are separate acceptance levels.
- Missing personal MELD/FreeSurfer licences block MELD preparation and scientific execution.
- WSL currently has less RAM than MELD's 24 GB recommendation. The launcher refuses pytest/prediction under 24 GiB.
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
