# Local records, backups, and recovery

Records stay in the selected data directory until you remove that directory.
There is no automatic evidence deletion, per-run purge interface, or remote sync.
Shared JSON artifacts can be referenced by several runs, so do not delete
individual artifact files to clear one result.

## Limits

The app refuses new runs at 500 runs or 64 MiB of local stored files. Artifact
writes also check the storage limit. A run is limited to 1,500 events and each
artifact to 128 KiB. Evidence is retained when a limit interrupts a run; a lack
of finalization is reported as incomplete rather than repaired into a pass.

One job runs at a time. The server keeps at most 64 job results in memory and
persists the latest job status for browser recovery. At most 16 HTTP connections
are handled concurrently, with a 25-second connection timeout. Attack, comparison,
and validation have a 120-second job deadline checked at operation boundaries.
An in-flight provider request can delay cancellation/deadline handling until it
returns or times out; this is not immediate process termination.

## Make a backup

1. Stop the application with Ctrl+C. Do not run another process against the same
   data directory while making or restoring a backup.
2. From the project folder, use a new destination outside the source data directory:

```powershell
python -m omnichain --data-dir ./runtime --backup-to ./backup-01
```

The command uses SQLite's backup API, copies the JSON artifacts, and reports
verification results for the copied runs. Check the output: incomplete source
runs remain incomplete in the backup. The command does not certify that every
run passed security checks. A failed copy can leave an incomplete destination;
use a new destination after resolving the cause.

To inspect the backup without changing the original records:

```powershell
python -m omnichain --data-dir ./backup-01 --port 8766
```

This opens a writable copy. Keep an additional untouched backup if needed.

## Interrupted work and changed versions

A browser reload reconnects to a running job. A server restart changes its
persisted RUNNING status to INTERRUPTED. Start a new run to retry; partial records
remain available. A failed retry must not reuse an earlier passing validation.

The database schema is versioned. Existing version-zero databases using the
original tables are recognized as version one; unsupported newer versions are
rejected. There is no general-purpose migration tool.

The strengthened evaluator uses scenario version two. Existing version-one
records are preserved, but they cannot be treated as current passing assessments.
Code, policy, fixtures, model settings, or runtime changes also require a new
assessment. Export older records for historical inspection; a changed context
does not silently alter their recorded verdict.

## Start a clean set of records

Use `--data-dir ./runtime-new` for a new directory. This preserves the old history.
If you want to remove local records, stop every app instance, verify the exact
chosen directory, save any wanted export/backup, then remove that **whole data
directory** using your file manager. Backups and exported JSON files remain until
you remove them separately. This is not a secure-erasure guarantee.

## Trust boundary

The application detects many changes and missing records. It does not prevent
someone with full control of the computer from rewriting the database, artifacts,
and anchors together. Backups and copied evidence are not independently signed.
