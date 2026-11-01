# Router audit and firmware research

This archive consolidates the earlier `orbi-tools` and
`research/orbi-rbr850-7.2.8.8` directories into this repository. The source
directories were copied on **2026-11-01**, without deleting or changing them.
Installed dependencies and Python caches were omitted.

The investigations describe **RBR850 V7.2.8.8_5.1.24**, primarily observed on
**2026-10-27–29**. They are historical evidence, not a current router health
check or a claim of support for other builds. Statements that the MCP server
is still future work describe the original investigation. Use the
[current project guide](../../README.md) and [access guide](../access.md) for
the implemented CLI and its limits.

## Research notes

| Topic | Document |
| --- | --- |
| Original tools and audit entry point | [Router audit](router-audit/README.md) |
| Key enrollment and connection handoff | [Router access](router-audit/docs/router-access.md) |
| Validated reads, hardware findings and untested operations | [Capability report](router-audit/docs/router-capabilities.md) |
| Firmware acquisition, extraction and source findings | [Firmware investigation](firmware-rbr850-7.2.8.8/README.md) |
| UDP activation, vendor OpenSSH and authentication boundaries | [Shell analysis](firmware-rbr850-7.2.8.8/SHELL-ANALYSIS.md) |
| Owner-key enrollment through SeAL | [SeAL analysis](firmware-rbr850-7.2.8.8/SEAL-SSH-ENROLLMENT.md) |
| Persistent keys and the untested startup repair | [Dropbear persistence](firmware-rbr850-7.2.8.8/DROPBEAR-PERSISTENCE.md) |
| Work remaining in the MCP implementation | [Feature backlog](../feature-backlog.md), [delivery TODO](../../TODO.md) |

An observed read does not validate the corresponding setter. A hidden form
does not establish a working backend or model support. A failed SOAP call does
not rule out an SSH implementation. Keys on persistent storage do not prove
that an SSH service restarts after reboot. Preserve these distinctions when
using the historical reports to plan new tools.

## Layout and publication boundary

`router-audit/` contains the original SOAP tooling and its reports.
`firmware-rbr850-7.2.8.8/` contains the firmware notes, extraction/emulation
helpers and dependency lists. The research scripts are preserved unchanged;
they are archival tools, not the supported MCP implementation. In particular,
`disable-iot.py` changes router configuration, and activation/enrollment
helpers can contact or modify a router. Consolidation did not run them.

The notes and helper sources are eligible for Git. Personal home paths, device
MAC addresses, fingerprints and the enrolled authorization-file hash were
replaced with placeholders in the Markdown copies. Those placeholders cannot
be used to establish trust in a different device.

The complete local archive also includes the following **ignored files**:

- `router-audit/router-config-report.json`: private configuration observations.
- `firmware-rbr850-7.2.8.8/evidence/`: raw device observations, host identities
  and derived reports. Only its two inventory-building Python sources are
  eligible for Git.
- `firmware-rbr850-7.2.8.8/downloads/`, `firmware/`, `volumes/`, `rootfs/` and
  `reference/`: firmware images, extracted files, vendor documents and saved
  third-party references with their original provenance/license files.
- Generated filesystem/UBI inventories, the verification snapshot and the
  saved GPL index.
- `.local/`: original Markdown before adaptation, the source inventory and
  the complete import manifest with per-file hashes.

These files are present in the consolidated local working tree. They are not
available in a fresh Git clone. Historical evidence links resolve only when
that local archive is present. A Git clone therefore contains the reports and
reproduction sources, but does not independently reproduce every live finding.
Keep an independent backup of the ignored archive. The entire research tree
is excluded from the runtime npm package by its `.npmignore`.

## Provenance and offline checks

[provenance.json](provenance.json) records the import date, source locations,
source-tree digests and before/after hashes for the versioned imports. The
local `.local/source-inventory.json` was saved before copying or editing.
`.local/import-manifest.json` records every imported file, including ignored
artifacts. Raw files were copied byte for byte; only the seven Markdown notes
were adapted for links, historical context and privacy.

Source-tree digests are SHA-256 over UTF-8 records sorted by source-relative
path: `path`, NUL, the lowercase file SHA-256, then newline. Dependency/cache
directories listed in the provenance file are excluded. All hashes are
computed offline from saved files.

The firmware [download manifest](firmware-rbr850-7.2.8.8/download-manifest.json)
retains the original download URLs, sizes and checksums. Reproducing firmware
checks requires the local artifacts and the Python packages listed alongside
the helpers. Create a new virtual environment rather than copying the old
one. Do not confuse a successful offline simulation with a live router test.
