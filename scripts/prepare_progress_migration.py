#!/usr/bin/env python3
"""Prepare an owner-scoped, reviewable migration. Never accesses the live database.
Use a fresh remote export as --current before applying its guarded SQL. Original
archives remain read-only; --output must be outside the repository.
"""
import argparse,collections,datetime,hashlib,json,sqlite3
from pathlib import Path

def iso(value):return value.astimezone(datetime.timezone.utc).isoformat(timespec='milliseconds').replace('+00:00','Z')
def ts(value):
    if not value:return 0
    return datetime.datetime.fromisoformat(value.replace('Z','+00:00')).timestamp()
def classify(row):
    c,w=row['correct_count'],row['incorrect_count']
    if not c and not w:return 'new'
    lc,lw=ts(row['last_correct_at']),ts(row['last_incorrect_at'])
    if not c or lw>lc:return 'practice'
    return 'known_once' if c==1 and w==0 else 'known_multiple'
def key(r):return (r['lang_code'],r['item_id'],r['mode'])
def read(path,owner):
    db=sqlite3.connect(f'file:{path}?mode=ro',uri=True);db.row_factory=sqlite3.Row
    result={key(r):dict(r) for r in db.execute('SELECT * FROM item_state WHERE user_id=?',(owner,))};db.close();return result

def prepare(current,baseline,original,owner,at):
    assert not any(r.get('migration_review_at') for r in current.values()), 'This account already has an import review date; do not migrate twice'
    due=iso(at+datetime.timedelta(days=14));watermark=iso(at);counts=collections.Counter();examples=collections.defaultdict(list);changes=[]
    for ident,currentrow in current.items():
        before=dict(currentrow);after=dict(before)
        # Only undo the old *known* copy's invented dates when the learner has
        # not answered that row since the archived copy. Newer answers win.
        old=baseline.get(ident);real=original.get(ident)
        fields=['correct_count','incorrect_count','last_correct_at','last_incorrect_at','last_seen_at','srs_stage']
        if old and real and all(before[x]==old[x] for x in fields) and before['correct_count']==real['correct_count'] and before['incorrect_count']==real['incorrect_count']:
            if before['correct_count']==1 and not before['incorrect_count'] and old['srs_stage']==4:
                for f in ['first_seen_at','last_correct_at','last_seen_at']:after[f]=real[f]
            elif before['last_correct_at']==real['last_correct_at'] and before['last_incorrect_at']==real['last_incorrect_at'] and not real['last_seen_at']:
                after['last_seen_at']=''
        category=classify(after);counts[category]+=1
        c,w=after['correct_count'],after['incorrect_count']
        raw=after['srs_stage'];stage=(min(9,max(1,int(raw))) if raw is not None and raw>=0 else min(9,max(1,c-w))) if c else 0
        after['srs_stage']=stage;after['unresolved']=int(category=='practice')
        after['migration_review_at']=due if category.startswith('known') else None
        if category.startswith('known'):after['due_at']=due
        elif category=='practice':after['due_at']=after['last_incorrect_at'] or after['last_seen_at'] or after['last_correct_at'] or None
        else:after['due_at']=None
        after['updated_at']=watermark
        assert all(before[f]==after[f] for f in ['correct_count','incorrect_count','item_id','lang_code','mode','item_type','parent_id'])
        changes.append({'before':before,'after':after,'category':category})
        if len(examples[category])<3:examples[category].append({'word':after['label'],'type':after['item_type'],'correct':c,'wrong':w,'last_correct_before':before['last_correct_at'],'last_correct_after':after['last_correct_at'],'next_review':after['due_at']})
    return {'owner':owner,'migration_at':watermark,'known_review_at':due,'rows':len(changes),'counts':dict(counts),'examples':dict(examples),'changes':changes}

def literal(v):
    if v is None:return 'NULL'
    if isinstance(v,(float,int)):return str(v)
    return "'"+str(v).replace("'","''")+"'"
def sql(plan):
    statements=['-- Owner-scoped guarded conversion; genuine post-snapshot answers are never overwritten.']
    columns=['srs_stage','unresolved','due_at','migration_review_at','first_seen_at','last_correct_at','last_seen_at','updated_at']
    for r in plan['changes']:
        a,b=r['after'],r['before'];sets=', '.join(f'{f}={literal(a[f])}' for f in columns)
        check=['user_id','lang_code','item_id','mode','correct_count','incorrect_count','last_correct_at','last_incorrect_at','first_seen_at','last_seen_at','updated_at','srs_stage']
        where=' AND '.join(f'{f} IS {literal(b[f])}' for f in check)
        statements.append('UPDATE item_state SET '+sets+' WHERE '+where+';')
    return '\n'.join(statements)+'\n'

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--current',type=Path,required=True);p.add_argument('--baseline',type=Path,required=True);p.add_argument('--original',type=Path,required=True);p.add_argument('--owner',required=True);p.add_argument('--source-owner',default='JST');p.add_argument('--output',type=Path,required=True);p.add_argument('--at',required=True);a=p.parse_args()
    assert a.output.resolve()!=a.current.resolve()
    now=datetime.datetime.fromisoformat(a.at.replace('Z','+00:00'));assert now.tzinfo
    plan=prepare(read(a.current,a.owner),read(a.baseline,a.owner),read(a.original,a.source_owner),a.owner,now)
    assert plan['rows']>0,'No matching owner rows'
    a.output.mkdir(parents=True,exist_ok=True)
    plan['input_sha256']={str(x):hashlib.sha256(x.read_bytes()).hexdigest() for x in [a.current,a.baseline,a.original]}
    (a.output/'plan.json').write_text(json.dumps(plan,indent=2));(a.output/'migration.sql').write_text(sql(plan))
    review={k:v for k,v in plan.items() if k!='changes'};(a.output/'review.json').write_text(json.dumps(review,indent=2));print(json.dumps({'counts':plan['counts'],'rows':plan['rows'],'next_review':plan['known_review_at']}))
if __name__=='__main__':main()
