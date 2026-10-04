# Fluency Next

Fluency Next is the local-first successor to Fluency. French Speech is the first
implementation, while the core is designed to support additional languages and
modes without duplicating vocabulary identities or pipeline logic.

The code repository contains source code, configuration, tests, documentation,
and compact release metadata. Large corpora, model caches, intermediate runs,
registries, and generated releases belong in the separate `Fluency-Workspace`.

## Invariants

`docs/INVARIANTS.md` records the rules that constrain every decision here:
compatibility, declared absence, verified provenance, adapters at the edges, and
discovery over registration.

## Local bootstrap

Python 3.12 is the supported development runtime for the initial rebuild.

```bash
make bootstrap
make test
make pilot
make dev
```

The development server listens on <http://127.0.0.1:4173> by default. It uses
the local `app/` directory and mounts only compact releases from the separate
workspace. It has no production or GitHub dependency.

## Current scope

The app is live at <https://rabbijoshy.github.io/Fluency-App/> with Speech
decks for Spanish, Portuguese, Czech, Finnish and French, Lyrics decks for
Spanish artists, and Artist mode test releases in French and Portuguese.
Releases are published to one repository per language (decision 0026).

What is open, and which chat owns it, is `CHAT_ROADMAP.md`. Eventual direction
is `LATER.md`. Decisions and their reasons are in `docs/decisions/`; the
migration history that got here is in `docs/archive/`.
