"""All dialogue forms must remain studyable independently of dictionary coverage."""
import json
from pathlib import Path
import unittest
import re

ROOT = Path(__file__).resolve().parents[2]


class CompleteSeriesTests(unittest.TestCase):
    def test_available_english_passages_are_not_lost_during_selection(self):
        token = re.compile(r"[^\W_]+(?:['’\-][^\W_]+)*", re.UNICODE)
        for slug in ['casa-de-papel', 'elite']:
            dialogue = json.loads((ROOT / f'app/data/series/{slug}.json').read_text())
            deck = json.loads((ROOT / f'app/data/series/{slug}-deck.json').read_text())
            available = {word for episode in dialogue['episodes'] for cue in episode['lines']
                         if cue.get('translation', {}).get('english')
                         for word in token.findall(cue['spanish'].lower().replace('’', "'"))}
            selected = {word for word, row in deck['surfaces'].items()
                        if any(example.get('english') for example in row['lines'])}
            self.assertEqual(available, selected, slug)

    def test_every_observed_form_has_one_frequency_ranked_card(self):
        for slug, count, tokens, episodes in [('casa-de-papel', 12706, 136924, 30),
                                              ('elite', 4482, 35791, 8)]:
            with self.subTest(series=slug):
                deck = json.loads((ROOT / f'app/data/series/{slug}-deck.json').read_text())
                observed = deck['intake']['surfaces']
                self.assertEqual(set(deck['surfaces']), set(observed))
                self.assertEqual(deck['matchedCount'], count)
                self.assertEqual(deck['trackCount'], episodes)
                self.assertEqual(deck['tokenCount'], tokens)
                self.assertEqual(sum(row['count'] for row in deck['surfaces'].values()), tokens)
                self.assertEqual(deck['admissionPolicy'], 'all-forms-v1')
                self.assertEqual(deck['intake']['mode'], 'no-wsd')
                self.assertGreater(deck['vocabularySummary']['cardsWithTranslatedExamples'], count * .6)
                self.assertLess((ROOT / f'app/data/series/{slug}-deck.json').stat().st_size, 25 * 1024 * 1024)
                for word, row in deck['surfaces'].items():
                    self.assertEqual(row['count'], observed[word]['count'])
                    self.assertEqual(row['card']['word'], word)
                    self.assertTrue(row['lines'])
                    card = row['card']
                    if card['definitionSource'] == 'inline':
                        self.assertEqual(card['sourceRank'], -1)
                        menu = deck['dictionaryMenus'][card['meaningMenu']]
                        self.assertTrue(menu)
                        if card['definitionStatus'] == 'available':
                            self.assertTrue(any(m['translation'] for m in menu))
                    else:
                        self.assertTrue(observed[word]['inStudyInventory'])
                        self.assertGreater(card['sourceRank'], 0)
                    for example in observed[word]['examples']:
                        source = deck['intake']['exampleLines'][example['line']]
                        self.assertEqual(source['text'][example['start']:example['end']], example['surface'])

    def test_elite_preserves_the_reviewed_quality_exclusion(self):
        dialogue = json.loads((ROOT / 'app/data/series/elite.json').read_text())
        episode = next(ep for ep in dialogue['episodes'] if ep['episode'] == 'S01E08')
        for cue in episode['lines'][638:641]:
            self.assertNotIn('translation', cue)
        self.assertEqual(dialogue['coverage']['translatedEpisodes'], 8)
        self.assertFalse(dialogue['coverage']['complete'])
