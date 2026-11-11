# Versions and provenance — 2026-11-11

These are observed WSL development versions, not a native Ubuntu compatibility certification.

| Component | Observed version / immutable source | Validation |
| --- | --- | --- |
| Ubuntu | 20.04.6 LTS, WSL2, x86_64 | Actual development host |
| WSL RAM after follow-up | 24.4558 GiB visible inside Ubuntu and the MELD container; 25 GiB configured ceiling | Actual container capacity and full upstream prediction suite; true peak unmeasured |
| Main SWANe Python | 3.11.14 (isolated venv) | Package, GUI and real T1 reference test |
| Clean-clone Python | 3.11.18 (new isolated venv) | Exact lock match and package checks |
| SWANe | 0.2.1.1, PyPI | Published release; newer development features excluded |
| pip bootstrap | 26.3 | Pinned by launcher |
| Qt | PySide6 6.9.3 | Real WSLg/XCB window inspected |
| Nipype / NumPy | 1.10.0 / 2.2.4 | Actual reference workflow |
| dcm2niix package | 1.0.20250506; binary reports v1.0.20250505 | Actual 192-slice conversion |
| FSL | Partial 6.0.7.8 manifest components | Actual T1 reference workflow; not all modules |
| Docker | 29.9.3 static, official stable binary | Actual hello-world and MELD container smoke |
| Compose | 5.7.0 | Official release checksum verified; actual CPU config |
| MELD Graph | v2.2.7, source e523c9de4677cfc46efe97069fe59442be160788 | Full upstream pytest: 17 passed; separate report generated; fresh raw-MRI run pending |
| MELD image | meldproject/meld_graph@sha256:c02adca0cf8e647762f7d09705bc1718079b190794a926b38d1521a6bb72c0ef | amd64 Linux, image size 18,243,989,272 bytes |
| Container runtime | Python 3.9.25, torch 1.10.0+cu102, working directory /app | Actual import smoke, no GPU used |
| MELD bundled FreeSurfer | /opt/freesurfer-7.2.0 in image | Licensed format roundtrip and public-T1 autorecon1 passed; fresh full reconstruction running |
| SWANe standalone FreeSurfer | Official Ubuntu 20.04 DEB 7.4.1 | Official DEB installed via apt; ELF/version/licensed format checks and SWANe GUI detection passed |
| SWANe MATLAB Runtime / Slicer | Not installed | Applicable modules/export remain pending |
| Native Ubuntu 22.04/24.04 | Candidate laptop targets | No native-laptop acceptance run |

SWANe wheel SHA-256:
f69072597fd8b073525aaecbff77fd20d1b8d8bd6de37fb1f509e19a8a8f4ae1.

Official MELD release archive SHA-256:
e7db6152de57eb1a51e25042f7d2a3e2cff76cc8c6db727669da6bb52d5b46e2.

Official Docker archive SHA-256 recorded after download:
3fb5d1f13014c18cc54945bc177c58a9056a482dada031e17d12cf2e6922c973.

Compose binary SHA-256, matched against upstream checksums.txt:
7758048ad38e580f22559603312874fec8bb638d021a9e64182385fc17cc12a2.

Partial FSL requested pins: fsl-bet2=2111.7, fsl-flirt=2111.2,
fsl-avwutils=2209.2, fsl-data_standard=2208.0, Python 3.11 from the official
6.0.7.8 manifest, and fsl-installer=3.21.0 for wrappers.
The actual 87 transitive FSL package URLs are source-controlled in requirements-fsl-linux-64.lock. Only public FSL/conda-forge HTTPS URLs without credentials or query parameters are included. Some supporting packages are newer than the 6.0.7.8 component manifest; the explicit lock records the exact tested partial environment. The Python package lock is requirements-swane-py311.lock.

Public real T1 dataset source: neurolabusc/dcm_qa_mprage at
ffc4fd6edc37cac769d69740185bdb1306b5a3fb, BSD-2-Clause.
Selected archive SHA-256:
558335329ca94dd5d2e85d1c3d4c9ef2682f2acf8a92bba81a60e50999f7402e.
The supplied reference NIfTI SHA-256 is
c18ad5698aba7dad90a50f26840cabb880a05b8eedfeae6fb6319ef9f0450262.
No images, DICOM headers or licences are included in this repository.

Official sources: [MELD release](https://github.com/MELDProject/meld_graph/releases/tag/v2.2.7),
[MELD installation](https://meld-graph.readthedocs.io/en/latest/install_docker.html),
[SWANe PyPI metadata](https://pypi.org/pypi/swane/0.2.1.1/json),
[FSL conda installation](https://fsl.fmrib.ox.ac.uk/fsl/docs/install/conda.html),
[FSL manifest](https://fsl.fmrib.ox.ac.uk/fsldownloads/fslconda/releases/manifest.json),
[Docker static binary installation](https://docs.docker.com/engine/install/binaries/),
[Compose releases](https://github.com/docker/compose/releases/tag/v5.7.0),
[public T1 dataset](https://github.com/neurolabusc/dcm_qa_mprage).

Official FreeSurfer Ubuntu 20.04 7.4.1 DEB: 6,687,701,644 bytes; MD5 3f488ddc5c1a19fe23bb9cbe2c9f457f; observed SHA-256 2046cdafb6939ac076e0443794d793d4ffbacf83b01e3398ce9046ffa5f4e4f7.

Official MELD data asset SHA-256: f739a9c9b9efbda22dec150a9099929bebb6975177d5dc1771cdb620eb3af466 (701,224,128 bytes); matched GitHub asset metadata before extraction.
