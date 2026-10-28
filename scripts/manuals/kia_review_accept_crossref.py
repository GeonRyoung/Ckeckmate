import json,pathlib,sys
R=pathlib.Path(__file__).resolve().parents[2]; O=R/'data/manual-review/2026-10-28'; raw=R/'.local/manual-review/2026-10-28/kia'
items=json.loads((raw/'crossref-units.json').read_text('utf8')); notes=json.loads(pathlib.Path(sys.argv[1]).read_text('utf8')); p=O/'kia-crossref-reviewed.json'
ledger=json.loads(p.read_text('utf8')) if p.exists() else {'reviewer':'AI','expertApproved':False,'runtimeApproved':False,'entries':{}}
for u in items:
 if str(u['sequence']) in notes:
  note=notes[str(u['sequence'])]
  if note=='__INHERIT__':
   pack=json.loads((raw/'crossref-latest-pack.json').read_text('utf8'));base=next(p['basis'] for p in pack if p['key']==u['key']);assert base
   note=ledger['entries'][base]['review_note_ko']+' [기준 전체본문과 이번 모든 변경부분 직접대조: 의미조건/수치/금지 변경 없음.]'
  ledger['entries'][u['key']]={'label':u['label'],'review_note_ko':note,'source_status':'SOURCE_TEXT_REVIEWED','occurrences':u['occurrences'],'runtimeApproved':False}
p.write_text(json.dumps(ledger,ensure_ascii=False,indent=2),'utf8');print('reviewed crossrefs',len(ledger['entries']))
