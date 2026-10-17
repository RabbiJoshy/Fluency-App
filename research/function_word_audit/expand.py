"""Explicit editorial slot types and simpler copy for the full preview, never live data.

Types describe the whole highlighted slot, not every token inside it. Allowed
lemmas constrain vocabulary; they are not authoritative POS annotations.
"""
from copy import deepcopy
from html import escape
import json
import re
from check import plain
from slot_review import apply as apply_slot_review

# Reviewed mappings from existing formula labels to display label and whole-slot type.
SLOTS = {}
def slots(labels, label, kind):
    for old in labels.split('|'): SLOTS[old] = (label, kind)
slots('Verb|Verb (1st Sing)|Verb (2nd Sing)|Verb (3rd Sing)|Verb (Passive/Impersonal)|Verb of self-action', 'verb', 'verb')
slots('Thought / Speech', 'think / say / know / hope', 'verb')
slots('Infinitive|Infinitive Goal|Infinitive Objective', 'infinitive (dictionary form)', 'verb')
slots('Noun', 'noun', 'noun')
for old in ['Feminine Noun','Feminine Singular Noun','Masculine Noun','Masculine Singular Noun','Feminine Plural Noun','Masculine Plural Noun','Plural Feminine Noun','Plural Masculine Noun','Plural Noun','Singular Noun']:
    SLOTS[old]=(old.lower(),'noun')
slots('Preposition','preposition','prep')
slots('Adjective / Abstract','adjective','adj')
slots('Clause|Main Clause|Main Action|Statement|Result','what happens','clause')
slots('Condition|Time Condition','a situation','clause')
slots('Description','description','clause')
slots('Contrast|Counterpoint','a contrasting idea','clause')
slots('Cause|Motive / Cause','a reason','phrase')
slots('Degree','more, less or better','phrase')
slots('Standard','what you compare with','phrase')
slots('Model / Standard','what you compare with','phrase')
slots('Destination|Masculine Destination|Place|Location|Transit Space|Surface','a place','phrase')
slots('Place / Time|Feminine Destination / Time|Masculine Destination / Time','a place / time','phrase')
slots('Time Period','a time / period','phrase')
slots('Limit / Endpoint','an endpoint','phrase')
slots('Recipient|Person|Companion','a person','phrase')
slots('Tool / Manner','a tool / way of doing it','phrase')
slots('Capacity / Profession|Role / Capacity','a role / job','phrase')
slots('Complement','noun / verb / pronoun','mixed')
slots('Noun / Origin','a noun / origin','mixed')
slots('Masculine Noun / Origin|Masculine Noun / Place','masculine noun','noun')
slots('Feminine Noun / Origin|Feminine Noun / Place','feminine noun','noun')
slots('Masculine Path / Reason|Feminine Path / Reason','a route / reason','phrase')
slots('Missing Element','what is missing','phrase')
slots('Topic','a topic','phrase')
slots('Surprising Subject','an unexpected example','phrase')
slots('Action|Movement|Position|Discussion / Thought','an action / situation','phrase')
slots('State / Verb|Verb / State|State / Gratitude|Movement / Time','an action / situation','mixed')
slots('Verb / Noun|Noun / Action','noun / verb','mixed')
slots('Object|Entity|Element|Item / Clause|Addition','an item / idea','mixed')

# Each family retains its existing pattern scope. Word-specific distinctions below.
COPY = {
 'Spatial Location':('Where','Shows where something happens or is located.'),
 'Spatial Framing':('Where','Shows where something happens or is located.'),
 'Temporal Framing':('When','Places an event in a time period, such as a month or year.'),
 'Destination':('Where to','Shows where someone or something is going.'),
 'Directional Link':('Where to','Points to a destination or recipient.'),
 'Directional Goal':('Where to','Shows where someone or something is going.'),
 "Personal 'a'":('Before a person','Used before a specific person receiving the action, as in veo a Ana (I see Ana).'),
 'Purpose':('What for','Links an action to its purpose: what someone wants to do or achieve.'),
 'Recipient':('Who for','Shows who something is for.'),
 'Beneficiary / Target':('Who for','Shows who something is for.'),
 'Accompaniment':('Who with','Shows who shares an action or is together with someone.'),
 'Instrument and Manner':('How / with what','Shows the tool used or the way something is done.'),
 'Cause / Motive':('Why','Gives the reason for an action, feeling or result.'),
 'Trajectory':('Through / along','Shows the route or place someone or something moves through.'),
 'Manner / Simile':('Like / in the same way','Compares how something is done with another example.'),
 'Capacity / Role':('As / in a role','Shows the role or job someone has in a situation.'),
 'Contrast':('But','Adds a contrasting idea or an unexpected difference.'),
 'Addition':('And','Joins items, ideas or actions.'),
 'Condition':('If','Gives a possible situation and what happens if it is true.'),
 'Prepositional Object':('After a preposition','Refers to him after a preposition: com ele (with him), para ele (for him).'),
 'Privation / Absence':('Without','Shows what is missing or absent.'),
 'Absence / Omission':('Without','Shows what is missing or left out.'),
 'Thematic Topic':('About','Introduces the topic someone talks or thinks about.'),
 'Spatial Surface':('On / above','Shows that something is on or above a surface.'),
 'Terminal Boundary':('Until / as far as','Shows where a movement ends or how long something lasts.'),
 'Scalar Focus':('Even','Includes an example that may be surprising.'),
 'Causal Reason':('Because','Gives the reason why something happens.'),
 'Temporal Subordination':('When','Connects an event to the time or situation when it happens.'),
 'Neutral Demonstrative':('That','Refers to an idea, situation or thing already mentioned or near the listener.'),
 'Neuter Demonstrative':('That','Refers to an idea, situation or thing already mentioned or near the listener.'),
 'Immediate Demonstrative':('This','Refers to a thing or idea close to the speaker or being introduced now.'),
 'Universal Totality':('Everything','Refers to everything in the situation.'),
 'Indefinite Entity':('Something','Refers to an unspecified thing or amount.'),
}
CONTRACTIONS={
 'no':('em + o','in / on / at the'),'na':('em + a','in / on / at the'),
 'do':('de + o','of / from the'),'da':('de + a','of / from the'),
 'ao':('a + o','to / at the'),'à':('a + a','to / at the'),
 'pelo':('por + o','through / by / for the'),'pela':('por + a','through / by / for the'),
 'num':('em + um','in / on / at a'),'numa':('em + uma','in / on / at a'),
 'del':('de + el','of / from the'),
}

def simpler_copy(lang, word, index, relation):
    tag=relation['tag']
    if word in CONTRACTIONS and index==0:
        parts,meaning=CONTRACTIONS[word]
        return meaning.capitalize(),f'Combines {parts}: “{meaning}”.'
    if tag=='Temporal Nexus':
        return ('When doing something','Means “when” doing something; followed by the infinitive (dictionary form).') if word=='ao' else ('When','Connects an event to the time or situation when it happens.')
    if tag in ('Definite Article','Indefinite Article'):
        meaning='the' if tag=='Definite Article' else 'a / an'
        return meaning.capitalize(),f'Means “{meaning}”. Use the form that matches the noun’s gender and number.'
    if tag=='Subject Pronoun':
        meaning={'eu':'I','yo':'I','tú':'you','ele':'he / it','ela':'she / it'}[word]
        return meaning, f'Means “{meaning}”. Names who does the action; the pronoun can often be left out.'
    if tag in ('Object Pronoun','Indirect Object','Direct Object Pronoun'):
        meaning={'me':'me / to me','te':'you / to you','lhe':'to him / her / you','le':'to him / her / you','a':'her / it','la':'her / it','os':'them','los':'them'}[word]
        return meaning.capitalize(), f'Refers to “{meaning}”. The surrounding verb and sentence show who or what is meant.'
    if tag=='Reflexive Clitic' and word=='me':
        return 'Myself / part of a verb','Can mean “myself”, or belong with a verb, such as lembrar-se (remember). These examples use the after-verb form.'
    if tag=='Possession':
        meaning={'mi':'my','tu':'your (informal)','su':'his / her / their / your (formal)','dele':'his / of him','dela':'hers / of her'}[word]
        return meaning.capitalize(),f'Shows who something belongs to: “{meaning}”.'
    if tag not in COPY: raise ValueError((lang,word,index,tag))
    return COPY[tag]


def expand(originals, pilot):
    result=deepcopy(originals);ledger=[]
    for lang,words in result.items():
        for word,entry in words.items():
            reviewed=word in pilot[lang]
            if reviewed: words[word]=entry=deepcopy(pilot[lang][word])
            entry['previewReviewStatus']='source-reviewed' if reviewed else 'copy-reviewed; source review pending'
            for i,r in enumerate(entry['relations']):
                before=deepcopy(originals[lang][word]['relations'][i]);types={}
                if not reviewed:
                    r['tag'],r['rule']=simpler_copy(lang,word,i,r)
                    def replace(m):
                        side,label=m.groups();new,kind=SLOTS[label];types[side]=kind
                        return f'<span class="fw-token-{side}">{escape(new)}</span>'
                    r['formulaHTML']=re.sub(r'<span class="fw-token-([vc])">(.*?)</span>',replace,r['formulaHTML'])
                else:
                    for side,label in re.findall(r'<span class="fw-token-([vc])">(.*?)</span>',r['formulaHTML']):
                        kind=next((kind for new,kind in SLOTS.values() if new==label),None)
                        if kind is None:
                            kind={'noun / verb / pronoun':'mixed','detail / action':'mixed','what happens':'clause','a possible situation':'clause','what happens then':'clause','masculine singular noun':'noun','masculine plural noun':'noun','destination':'phrase','pronoun':'pron'}.get(label)
                        if kind is None:raise ValueError(('Unreviewed pilot slot',label))
                        types[side]=kind
                if reviewed and word=='que' and i==0:
                    types['c']='clause'  # Implicit in formula, still typed in example highlights.
                r['slotTypes']=types
                slot_notes=apply_slot_review(lang,word,i,r)
                ledger.append(dict(language=lang,word=word,pattern=i,before={k:before[k] for k in ('tag','formulaHTML','rule')},after={k:r[k] for k in ('tag','formulaHTML','rule','slotTypes')},example_review=entry['previewReviewStatus'],slot_notes=slot_notes))
    return result,ledger


def write_report(out,ledger):
    (out/'full-suite-review.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n')
    lines=['# Full-suite copy and slot review','',f'{len(ledger)} patterns. All existing suite members are included; no missing-word candidates were added.','',
    'Explicit slotTypes control colour, independently of display wording. Verb phrases can use the verb colour as a whole. Mixed slots and clauses retain side colours. This is display metadata, not an automatic sentence classifier.','',
    'Twelve pilot cards retain their reviewed source examples. Other sentence wording, translations and source labels remain unchanged; reviewed slot highlights are updated. These examples are marked as awaiting source review; this extension is not a claim of full sentence calibration.','']
    for r in ledger:
        lines += [f"## {r['language']} · {r['word']} · {r['pattern']}",'',f"Before: {r['before']['tag']} — {plain(r['before']['formulaHTML'])}",r['before']['rule'],'',f"After: {r['after']['tag']} — {plain(r['after']['formulaHTML'])}",r['after']['rule'],'',f"Slots: {r['after']['slotTypes']}. Examples: {r['example_review']}.",'',f"Remaining slot issues: {r['slot_notes']}" if r['slot_notes'] else '', '']
    (out/'full-suite-review.md').write_text('\n'.join(lines))
