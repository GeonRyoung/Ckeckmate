"""Export explicitly reviewed exact-hash ledger; never promotes unread units."""
import json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[2]
OUT=ROOT/'data/manual-review/2026-10-28'
RAW=ROOT/'.local/manual-review/2026-10-28/kia'
units=json.loads((RAW/'unique-sections.json').read_text('utf8'))
ledger=json.loads((OUT/'kia-reviewed-ledger.json').read_text('utf8'))['entries']
rows=[]
for prefix,note in ledger.items():
 found=[u for u in units if u['key'].startswith(prefix)]
 assert len(found)==1,(prefix,len(found))
 u=found[0]
 rows.append({'id':'kia-review-'+u['key'][:16],'section_text_sha256':u['key'],'label':u['label'],'review_status':'SOURCE_TEXT_REVIEWED','reviewer':'AI','runtime_approved':False,'expert_approved':False,'review_note_ko':note,'scope':'inline source meaning and response; linked procedures remain separately auditable','cross_reference_review':'PENDING' if u['cross_references'] else 'NO_LINK_IN_UNIT','sources':u['occurrences'],'cross_references':u['cross_references']})
reviewed={r['section_text_sha256'] for r in rows}
inventory=json.loads((OUT/'kia-inventory.json').read_text('utf8'))
for row in inventory['entries']:row['review_status']='SOURCE_TEXT_REVIEWED' if row['section_text_hash'] in reviewed else 'INVENTORIED_NOT_REVIEWED'
inventory['all_reviewed']=False
inventory['reviewed_unique_sections']=len(rows)
inventory['unreviewed_unique_sections']=len(units)-len(rows)
(OUT/'kia-inventory.json').write_text(json.dumps(inventory,ensure_ascii=False,indent=2),'utf8')
(OUT/'kia-rules.json').write_text(json.dumps({'all_countermeasures_reviewed':False,'total_unique_sections':len(units),'reviewed_unique_sections':len(rows),'records':rows},ensure_ascii=False,indent=2),'utf8')
print('reviewed',len(rows),'remaining',len(units)-len(rows),'occurrences',sum(len(r['sources']) for r in rows))
