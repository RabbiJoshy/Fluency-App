# Come-back items

## Restore More sentences / Set phrases (or stop advertising them)

Both settings still default **on**, so they look live. They only fire if a
deck actually carries backup-example shards (`vocabulary.backup_examples.index.json`)
or MWE/clitic memberships.

Live speech v12 indexes (es/pt 6000, cs 4000) have `mwe_memberships=0` and
`clitic_memberships=0`. Backup-example manifests 404. Decide whether to
rebuild those fields into releases, or hide/disable the toggles until the
data exists.
