# Private review mapping permissions — 2026-10-08

The adjudication CLI previously wrote its arm-mapping key using default filesystem
permissions and only then applied mode 0600. With a permissive umask, another
local account could potentially read the mapping during that interval.

The exporter now creates the file exclusively with mode 0600 before writing any
content. Existing paths, including symlinks, are rejected; serialization failures
create no file. The mapping remains sensitive and must be kept separate from
reviewers. POSIX permissions do not protect against the file owner or root and
are not a replacement for Windows ACLs or secure host administration.

Verification: all 159 Python tests passed locally, including three new regression
tests observing permissions before the first write, refusing existing files and
symlinks, and rejecting non-finite JSON before creating output.

This is AI-assisted engineering hardening, not an independent security review.
Accepted progress remains 81/100 (+0); external acceptance gates remain open.
