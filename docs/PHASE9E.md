# Phase 9E development checkpoint and live validation — 2026-11-05

Owner authorized testing/installing against the actual Calibre installation,
with verified original-plugin and ISFDB4 preference backups. No sandbox,
firewall, ACL, VM or Windows security changes are part of this phase.

## Pre-install checkpoint

Repository main, starting HEAD 759c404b7ac93b499ff0c1b2ecc4ab657c6b6b20.
Complete offline suite: 145 executed; 144 passed, 0 failures/errors/skips,
one existing advanced-search expected failure. Camoufox fixtures: 24 passed,
0 failures/errors/skips. Runtime confirmed live: Calibre 9.17.0 / embedded
Python 3.14.8. No actual Calibre application/library worker was running.

Original installed ZIP:
C:\Users\apt\AppData\Roaming\calibre\plugins\ISFDB4.zip
Static identity ISFDB4, version 1.4.14, correct import marker.
Original SHA-256:
9be3ce2cce7d3cd666b040757883e1791b55cb78e64ed9fda2836cceab38a760

Verified byte-for-byte backup directory:
C:\Users\apt\Documents\ISFDB4-Phase9E-Backup-20261105-084400
Original ZIP stored as ISFDB4-original.zip. ISFDB4-specific preferences copied
as metadata_sources/ISFDB4.json, SHA-256
aab259b846970f31b620a4126935c2bdcbe46e45ea8b7cb0fdc13052050e758c.
plugins/ISFDB4.json was not present. Backup preceded all live Calibre startup.
Calibre subsequently confirmed the expected active configuration path.

Only intended source, test, fixture and documentation changes are staged for
the checkpoint. No generated ZIP, backup, configuration, .codex artifact,
credential file, library or temporary runtime log is included. Existing tracked
IDE files are unchanged. No version, transport or security policy is changed.

Checkpoint SHA, candidate hash, installation/live outcomes and rollback status
will be appended after those operations; this pre-install record does not claim
they have already succeeded. No push or tag is authorized or performed.
