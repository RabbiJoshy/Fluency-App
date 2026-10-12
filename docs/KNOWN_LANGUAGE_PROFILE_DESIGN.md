# Known languages, onboarding, and Smart Skip

Design recorded 2026-10-12. Josh subsequently requested BRIDGE implementation
in this chat. The shared profile and opt-in BRIDGE control are now implemented;
see `BRIDGE_IMPLEMENTATION.md` for verified behaviour, data limits and rollout.
The text below preserves the design rationale. Latest picker refinement: the
profile uses fixed listed choices, with no free-text addition. Languages without
a study deck carry a Coming soon reminder but can still be declared known.

## The product model

A learner's language background belongs to their profile. Smart Skip decides
how to use that background for a particular learning language. Recorded knowledge
of individual words remains a third, separate source of evidence.

| Information | Where the learner changes it | Scope |
| --- | --- | --- |
| Languages they can comfortably read | Settings → App → Languages you know | Account-wide |
| Whether to skip obvious look-alikes using those languages | Smart Skip → Look-alikes | Per learning language |
| Which known languages to use for that filter, if they want to narrow it | Smart Skip → Look-alikes | Per learning language |
| Specific words/meanings learned in another language | Existing study progress; a future BRIDGE control chooses whether to use it | Progress per source language; filtering preference per target language |

Turning Smart Skip off never removes languages from the profile. Disabling
Spanish as a source while studying Portuguese never removes Spanish from the
profile or changes filtering preferences for another learning language. Studying
French does not declare the learner a comfortable reader of French.

## When to ask

Ask once, after login or guest entry and the first learning-language choice,
before preparing the first study set. Keep this out of account creation itself.
The question is **Which languages can you comfortably read?** with the note:
**Choose languages where most everyday words are already familiar. You can
change this in Settings.**

Offer the whole supported profile-language catalogue, not just languages with
look-alike data for the currently selected deck. A profile cannot be tied to
the first deck's available filters. English may be preselected, but it must be
removable. Include **I'm still learning another language** as explanatory copy,
not another declaration of complete vocabulary knowledge: **You don't need to
add a language just because you're studying it here.**

Continue saves the selection and records completion even if nothing is selected.
Do not ask again when the learner switches languages, switches between Speech
and Lyrics, returns later, or signs in on a second device after profile sync.
Existing saved answers should migrate without requiring another onboarding
dialog. A newly supported language becomes available in Settings without
reopening onboarding.

Guest choices persist on the device. On moving from guest use to a new account,
carry the completed profile over if the account has no profile; an existing
account's saved profile takes precedence over another browser's guest choices.

## General Settings

Add **Languages you know** to the App tab, alongside other persistent personal
preferences, with a row showing the selected languages (or **None selected**).
Opening it shows a checklist with the same wording and catalogue as onboarding.
Save updates the single profile. Cancel preserves the existing answer.

Use a short explanation: **Saved for every language you study. Smart Skip
controls whether these languages are used to skip look-alikes.** Provide a
link to Smart Skip for the active learning language. The profile editor should
remain accessible regardless of whether Smart Skip is on or whether that deck
has any supported look-alike pairs.

## Smart Skip

Keep the Look-alikes shortcut's on/off control here. Show **Using English and
Spanish**, for example, using only selected profile languages supported by the
current deck. Provide **Edit languages you know** linking to the same Settings
editor rather than maintaining a second copy of the profile picker.

If per-deck source selection is retained, label it **Use for this language**.
It can restrict the profile's candidate sources; it must not rewrite the
account-wide list. By default, use all applicable profile languages. Explicit
source exclusions remain exclusions when profile languages are added later.
Unsupported source/target pairs should never be presented as active filtering.

Basic Smart Skip on by default is a recommendation, not a change made by this
design. Its initial source selection must follow a confirmed profile. Advanced
grammar/slang/name exclusions stay separate from the profile and off by default.

## BRIDGE compatibility

BRIDGE's roadmap calls for skipping a matching target word/meaning only when
the learner actually knows its source counterpart. It must retain the existing
matching and false-friend safeguards, without fabricating target study progress.

When BRIDGE is built, add a separate Look-alikes option:
**Use words I've learned in other languages**. Its list can be derived from
account progress, showing sources such as **Spanish · learned words only**.
Whole-language sources should be distinguished as **English · language I know**.
Do not add a currently studied language to the whole-language profile
automatically, infer full fluency from a completed level, or ask users to
declare whole-language knowledge to activate BRIDGE.

Profile familiarity and recorded learning progress may both be relevant to one
source language. Keep their evidence separate, and show a single clear reason
for each skipped target word. A language removed from the profile may still be
a valid progress-based BRIDGE source if the learner enables that separate option.
The qualifying progress states, sense matching and rollout defaults belong to
BRIDGE's later data audit and implementation, not this settings work.

## Storage and migration contract

Store one account-scoped profile with known language codes, onboarding completion,
schema version and update timestamp. Sync it through the account metadata path;
keep a local copy for offline use. An explicitly confirmed empty list differs
from an unconfigured profile. Cache reads must respect the current account.

Store Smart Skip enabled state and any per-target source exclusions with the
existing per-language Fast Track preferences. Never infer profile completion
from Smart Skip enabled state.

The existing `fluency_known_languages_v1` browser list is a migration source.
Use it as the initial confirmed profile when attaching existing preferences to
the appropriate account. Do not repeatedly seed unrelated accounts with another
account's browser preferences. Migrate an existing per-language intro completion
to the global completion marker, retaining explicitly selected empty lists.

Profile edits invalidate prepared decks and refresh supported exclusion counts,
level counts, explanatory copy and skipped-word lists. They do not manufacture
correct answers, mark target words learned, erase study history or silently
replace the order/content of an active study session. Apply deck-composition
changes when preparing the next set.

## Pre-implementation behaviour verified in the code

- `main.js` tracks intro completion separately for each target language in
  `fluencySeenKnownLanguagesIntroV1`. The prompt is considered on setup startup,
  language/source changes and entry to Artist mode.
- `auth.js` also considers it after account or guest entry. This is not a
  signup-only question.
- `cognates.js` saves one browser-wide language list in
  `fluency_known_languages_v1`, without account sync.
- The current intro offers only the current deck's applicable languages and
  saves that subset. The Smart Skip picker likewise writes only the current
  deck's selected sources, which can discard declarations relevant to other
  learning languages. The shared-profile design must fix both paths.

## Implementation acceptance checks

1. A new learner confirms the profile once; choosing a second learning language
   never prompts again, including after reload and sync on another device.
2. Empty selections remain empty, complete onboarding, and survive reload/sync.
3. Settings is editable with Smart Skip off and on decks without cognate data.
4. Smart Skip source changes for one target preserve the profile and other
   targets' source preferences.
5. Profile changes preserve source-language declarations not supported by the
   current target. Old saved lists migrate without repeated onboarding.
6. Switching accounts cannot reuse another account's cached profile. Offline
   edits sync without a stale remote copy overwriting a newer local edit.
7. Studying a language never declares whole-language knowledge. The saved
   profile and per-target policy do not require BRIDGE to be implemented.
8. Counts and future prepared sets update while recorded learning progress and
   the active set remain intact.

Related: `CHAT_ROADMAP.md` → BRIDGE; decision 0028 (words that must not be skipped).
