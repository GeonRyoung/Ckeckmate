"""Display full source or lossless textual edits against an already read same-label source.
No review states are written by this display tool.
"""
import json,pathlib,re,difflib,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
RAW=ROOT/'.local/manual-review/2026-10-28/kia'
OUT=ROOT/'data/manual-review/2026-10-28'
items=json.loads((RAW/'unique-sections.json').read_text('utf8'))
ledger=json.loads((OUT/'kia-reviewed-ledger.json').read_text('utf8'))['entries']
read=[e for e in items if any(e['key'].startswith(k) for k in ledger)]
def normlabel(s):return re.sub(r'\s+','',s)
start=int(sys.argv[1]);count=int(sys.argv[2])
pending=[e for e in items if not any(e['key'].startswith(k) for k in ledger)]
pack=[]
for e in pending[start:start+count]:
    candidates=[b for b in read if normlabel(b['label'])==normlabel(e['label'])]
    base=max(candidates,key=lambda b:difflib.SequenceMatcher(None,b['text'],e['text'],autojunk=False).ratio(),default=None)
    ratio=difflib.SequenceMatcher(None,base['text'],e['text'],autojunk=False).ratio() if base else 0
    print('\nUNIT',e['sequence'],e['key'][:10],e['label'],'DOCS',','.join(o['document_id'] for o in e['occurrences']))
    if base and ratio>=.68:
        print('COMPARE',base['key'][:10],'similarity',round(ratio,3))
        sm=difflib.SequenceMatcher(None,base['text'],e['text'],autojunk=False)
        for tag,i,j,a,b in sm.get_opcodes():
            if tag!='equal':print('CONTEXT',e['text'][max(0,a-22):a], 'REMOVE',repr(base['text'][i:j]),'ADD',repr(e['text'][a:b]),'AFTER',e['text'][b:b+22])
    else: print('FULL',e['text'])
    pack.append({'key':e['key'],'sequence':e['sequence'],'basis':base['key'] if base and ratio>=.68 else None,'label':e['label']})
(RAW/'latest-review-pack.json').write_text(json.dumps(pack,ensure_ascii=False,indent=2),'utf8')
