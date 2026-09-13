"""Choose which matches a card keeps, without letting the choice bias usage.

The harvest used to rank every match by easiness and keep the head. Measured on
Spanish that did two things, both bad:

* It biased the pool toward one kind of usage. `vez` kept four copies of
  `de vez en cuando`, because a short idiom built from common words is exactly
  what a frequency-burden score rewards. A sense distribution estimated from
  that pool would call `vez` monosemous. The same mechanism explains Tatoeba's
  `Tom`/`Mary` sentences arriving over-represented, and `nada` keeping
  "Yo no tengo nada que ver con esto/eso/en eso" in three separate slots.
* It computed the ranking for every match in order to throw almost all of it
  away. `que` scored 209,468 sentences to keep 80, and the top 100 cards alone
  accounted for 55% of all scoring work in a 9,999-card run.

Both fall to the same change. A card keeps a uniform sample of what matched it
rather than the head of a ranking, and the sample is chosen by a hash so the
decision costs one comparison for a match that will not be kept.

## Why a hash and not a random number

Bottom-k by hash is a uniform sample without replacement, like reservoir
sampling, but it does not depend on the order records arrive in and it carries
no RNG state. The same corpus yields the same pool whether it is read forwards,
backwards, or split across sources -- so a harvest stays reproducible without
storing a seed, and two runs that read their sources in different orders still
agree.

## Quality is still allowed to be brutal

Sampling neutrally is not the same as accepting anything. A card with 209,468
matches can afford to be extremely fussy; what it must not do is be fussy about
*usage*. So the pool is sampled wider than the budget and then cut down on form
alone -- rare vocabulary, corpus placeholder names, redundancy against the rest
of the pool. Those are judgements about whether a sentence is well made, and
they do not favour one sense of a word over another.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import heapq
import re
import unicodedata
from typing import Any, Callable, Iterable

POOLING_POLICY_VERSION = "harvest-neutral-pool/v1"

# How much wider than the budget a card samples before quality cuts it down.
# Wider means quality has more to choose from and the residual correlation
# between "well made" and "typical usage" has less room to reinstate the bias
# sampling just removed; it also costs memory linearly. Three is a starting
# value, not a measured one -- comparing sense distributions at 2x, 3x and 5x
# after a WSD run is what would settle it.
DEFAULT_POOL_MULTIPLIER = 3

_WORDS = re.compile(r"[^\W\d_]+", re.UNICODE)


def pool_key(card_id: str, identity: str) -> float:
    """A stable uniform [0,1) coordinate for one example on one card.

    Keyed by card as well as example so the same sentence is not kept or
    dropped in lockstep across every card it matches, which would correlate the
    pools of unrelated words.
    """

    digest = hashlib.blake2b(
        f"{card_id}\x00{identity}".encode("utf-8"), digest_size=8
    ).digest()
    return int.from_bytes(digest, "big") / float(1 << 64)


@dataclass
class SourcePool:
    """A uniform sample of one source's matches for one card."""

    capacity: int
    _heap: list[tuple[float, str]] = field(default_factory=list)
    held: dict[str, dict[str, Any]] = field(default_factory=dict)
    seen: int = 0

    def offer(self, key: float, identity: str, build: Callable[[], dict[str, Any]]) -> bool:
        """Admit this example if it belongs in the sample.

        ``build`` is called only when the example is admitted, which is the
        whole point: for a common word almost every match is rejected on one
        float comparison, and the expensive per-match work never happens.
        """

        if identity in self.held:
            return False
        self.seen += 1
        if len(self._heap) < self.capacity:
            heapq.heappush(self._heap, (-key, identity))
            self.held[identity] = build()
            return True
        worst_key, worst_identity = self._heap[0]
        if key >= -worst_key:
            return False
        heapq.heapreplace(self._heap, (-key, identity))
        self.held.pop(worst_identity, None)
        self.held[identity] = build()
        return True


def rare_word_count(tokens: Iterable[str], frequency_ranks: dict[str, int], *, deck_size: int) -> int:
    """Distinct words in the sentence that the deck will never teach.

    Absolute, unlike ``harder_tokens``, which is relative to the card's own
    rank. A word past the end of the inventory is one the learner does not meet
    in this deck at all, and a sentence full of them is usually full of proper
    nouns or specialist vocabulary -- which is a statement about how well made
    the sentence is, not about which sense it carries.
    """

    return sum(
        1
        for token in dict.fromkeys(tokens)
        if frequency_ranks.get(token, deck_size + 1) > deck_size
    )


_PLACEHOLDER_NAMES = re.compile(
    r"\b(?:Tom|Mary|M[áa]ria|Marie|Maria|John|Ken|Bob|Alice|Jim)\b", re.UNICODE
)


def strip_accents(text: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFD", text)
        if not unicodedata.combining(char)
    )


def deaccented_index(frequency_ranks: dict[str, int]) -> frozenset[str]:
    """Accent-stripped spellings of ranked words that are normally accented.

    A subtitle rip that has lost its accents writes `radiacion` for
    `radiación`. Those are the sloppiest rows in the corpus and they tend to
    have lost more than the one accent you can see.

    This is a preference and NOT a gate, because the evidence is not clean
    enough to delete a sentence on. A frequency list is not a dictionary:
    `importara`, `estudie` and `exploto` are all correct Spanish that simply
    does not appear in the top 9,999 surfaces, and a rule strict enough to
    reject `radiacion` rejects those too. Measured on 60,000 Spanish sentences,
    0.31% match and roughly a third of those are correct.
    """

    return frozenset(
        stripped
        for word in frequency_ranks
        if (stripped := strip_accents(word)) != word
    )


def quality_penalty(
    text: str,
    *,
    frequency_ranks: dict[str, int],
    deck_size: int,
    weights: dict[str, float],
    deaccented: frozenset[str] = frozenset(),
) -> float:
    """How badly made this sentence is, ignoring which sense it shows.

    Every term here is a property of the sentence's form. None of them can
    prefer one usage of the target word over another, which is the property
    that lets this be applied as hard as the supply allows.
    """

    tokens = _WORDS.findall(text.casefold())
    rare = rare_word_count(tokens, frequency_ranks, deck_size=deck_size)
    penalty = weights.get("rare_word", 1.0) * rare
    if _PLACEHOLDER_NAMES.search(text):
        penalty += weights.get("placeholder_name", 1.5)
    if deaccented:
        lost = sum(
            1
            for token in dict.fromkeys(tokens)
            if token not in frequency_ranks and token in deaccented
        )
        penalty += weights.get("lost_accent", 2.0) * lost
    return penalty


def token_set(text: str) -> frozenset[str]:
    return frozenset(_WORDS.findall(text.casefold()))


# How long a word-for-word run has to be before two sentences are the same
# example. Five is where an agreement family shows itself: "No tengo nada que
# ver" is shared by every member of one, while an idiom alone is shorter -- two
# sentences both using `de vez en cuando` share only four and stay distinct,
# which is what lets a card keep several genuine uses of one expression.
SHARED_PHRASE_TOKENS = 5


def phrase_set(text: str, size: int = SHARED_PHRASE_TOKENS) -> frozenset[tuple[str, ...]]:
    words = _WORDS.findall(text.casefold())
    if len(words) < size:
        return frozenset({tuple(words)}) if words else frozenset()
    return frozenset(
        tuple(words[index : index + size]) for index in range(len(words) - size + 1)
    )


def redundancy_penalty(
    subject: frozenset[str],
    others: list[frozenset[str]],
    *,
    threshold: float = 0.8,
    subject_phrases: frozenset[tuple[str, ...]] | None = None,
    other_phrases: list[frozenset[tuple[str, ...]]] | None = None,
) -> int:
    """How many kept examples this one nearly repeats.

    Tatoeba contributors write agreement families on purpose, so a card can
    receive one sentence several times over. Three of `nada`'s five best
    examples were the same sentence.

    Vocabulary overlap alone is not enough to see it. "No tengo nada que ver
    con este asunto" and "No tengo nada que ver con él" are plainly the same
    example, but on sentences this short the two or three words that differ are
    a large share of the vocabulary, so set overlap falls under any threshold
    that does not also collapse unrelated sentences. Filtering to content words
    inverts the problem rather than solving it: here the shared half is entirely
    function words and the differing half carries all the content.

    What actually identifies the family is the word-for-word run they have in
    common, so a shared phrase counts as a repeat regardless of overlap.
    Counting redundancy rather than rejecting it lets scarcity outvote it on a
    card that has nothing else.
    """

    count = 0
    for index, other in enumerate(others):
        if other and subject and len(subject & other) / max(len(subject), len(other)) >= threshold:
            count += 1
            continue
        if subject_phrases and other_phrases and subject_phrases & other_phrases[index]:
            count += 1
    return count


def systematic_sample(ordered: list[Any], keep: int) -> list[Any]:
    """Take ``keep`` items spread evenly across ``ordered``.

    Used to cut a quality-ranked shortlist down to budget. Taking the head
    instead would hand back to the quality score exactly the concentrating
    power that sampling was introduced to remove: whatever residual correlation
    quality has with usage would apply at full strength to the head and not at
    all to the rest.
    """

    total = len(ordered)
    if keep >= total:
        return list(ordered)
    if keep <= 0:
        return []
    step = total / keep
    return [ordered[min(total - 1, int(index * step))] for index in range(keep)]
