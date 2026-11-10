# Project instructions

Read CODEX_HANDOFF.md before continuing work. Follow the user's authorized goal of a beginner-friendly Ubuntu setup for MELD Graph and SWANe. Do not confuse MELD Graph with the GNOME diff application.

Keep local configuration, licences, MRI/DICOM data, downloaded models, environments and logs out of Git. Do not reset WSL or replace existing environments. Use isolated environments and official sources. Keep MELD and SWANe workflows independent until interoperability is verified.

Record tests honestly: mocked launcher tests, imports, GUI checks, upstream verification and scientific MRI workflows are different acceptance levels. Do not claim one based on another. Run relevant tests after changes and preserve failure exit codes. Update TEST_REPORT.md with observed results and blockers.

Do not publish identifiable medical data, credentials or licence contents. Read release-specific dependency and licence requirements before installation. Never use --break-system-packages.
