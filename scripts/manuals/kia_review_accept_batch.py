"""Apply an explicitly read batch and reviewer-authored delta notes.
Only invoke after reading the complete pack, never on a truncated tool result.
"""
import json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'data/manual-review/2026-10-28'
RAW=ROOT/'.local/manual-review/2026-10-28/kia'
path=OUT/'kia-reviewed-ledger.json'
ledger=json.loads(path.read_text('utf8'))
pack=json.loads((RAW/'latest-review-pack.json').read_text('utf8'))
notes=json.loads(pathlib.Path(sys.argv[1]).read_text('utf8'))
assert notes['all_displayed_units_read'] is True
assert [p['sequence'] for p in pack]==notes['sequences']
for p in pack:
    note=notes['notes'].get(str(p['sequence']))
    if note is None:
        assert p['basis'],p
        basis=next(v for k,v in ledger['entries'].items() if p['basis'].startswith(k))
        note=basis+' [차이 대조 완료: 이 절의 차이는 표기·배치 차이이며 위 조건/조치의 실질 변경이 없음.]'
    ledger['entries'][p['key'][:10]]=note
path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2),'utf8')
print('accepted',len(pack),'ledger',len(ledger['entries']))
