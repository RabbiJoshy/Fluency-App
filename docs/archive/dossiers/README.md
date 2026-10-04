# Dossiers

A dossier is the shared working authority for one named job: the facts that job may treat as gathered. Several chats may contribute before the job starts or while it is in session. `CHAT_ROADMAP.md` points to the dossier. A dossier is not a decision, a runbook, or an output snapshot.

## Lifecycle

1. **Collecting:** The dossier may be assembled ahead of its roadmap job. Record its status at the top. Contributing chats append under their own headings and preserve earlier contributions rather than rewriting the whole file. Unverified leads stay labelled as such.
2. **Signed off:** Record sign-off and freeze the dossier. The named job can use its accepted facts to produce a new, versioned snapshot in the appropriate workspace location. Do not overwrite an earlier snapshot.
3. **After a ship:** Keep the signed-off dossier frozen. If the shipped result needs improvement, add an `OPEN.md` row pointing to the dossier or a `docs/open/` writeup. Leave the chat column as `none` until Joshua reopens the work. A reopened job gets a new codename and output version; the old dossier stays put.

`docs/research/` is optional scratch space for exploratory work, including work done before or after a ship for a future version. It is not a required stop for a dossier. `LATER.md` holds eventual directions that are neither shipped nor under active research.
