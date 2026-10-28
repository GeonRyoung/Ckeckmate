"""Independent source spot checks; not approval of all Kia rules."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
ds=json.loads((ROOT/'data/manual-research/2026-10-28/kia_manifest.json').read_text(encoding='utf8'))['documents']
items=[('CT1','t00068','배터리 시스템 냉각수 경고','EV4는 주행을 중지하고 서비스 점검한다. 운전자 냉각수 확인·보충으로 정규화하지 않는다.'),('CV1','t00585','배터리 시스템 냉각수 경고','EV6는 주행을 중지하고 냉각수량을 확인한다. EV4의 점검 지시와 문구가 다르며 임의 보충 허가를 뜻하지 않는다.'),('MQ4','t00193','오일압력/TPMS/DPF/ABS/EBD','오일 압력 회복 뒤 D2.2 제한 자동 해제와 G2.5 T-GDI 재시동 조건을 구분한다. TPMS 약 1분 점멸 후 지속 점등은 고장이고 저압 지속 점등과 다르다. DPF 약 60km/h 이상 또는 2단 이상 1500–2500rpm 약 25분 조건을 다른 동력계에 확장하지 않는다. ABS 이동 중 경고는 안전 정차·시동 끄기 후 재시동 자기진단을 따르며 재점등/지속은 정비한다. ABS와 브레이크 동시 점등은 고속·급제동을 피하고 즉시 정비한다.')]
rows=[]
for code,topic,loc,note in items:
 d=next(d for d in ds if d['id']==f'kia_{code}_2027');a=next(a for a in d['assets'] if a['source_url'].endswith('/'+topic+'.html'))
 rows.append(dict(documentId=d['id'],sourceURL=a['source_url'],sourceSha256=hashlib.sha256((ROOT/a['local_path']).read_bytes()).hexdigest(),locator=loc,reviewNote=note,reviewStatus='SOURCE_TEXT_REVIEWED',reviewer='AI',runtimeApproved=False))
rows.append({**rows[-1],'locator':'전방 안전 경고등, 노란색 항목','reviewStatus':'SOURCE_INCONSISTENCY_HOLD','reviewNote':'노란색 설명이 빨간색 작동 점멸 설명과 중복되어 있다. 노란색의 기능 해제·고장 의미를 이 문구만으로 자동 수정하지 않고 제조사 확인 대상으로 보류한다.'})
(ROOT/'data/manual-review/2026-10-28/audit-kia-spotcheck.json').write_text(json.dumps({'scope':'독립 원문 표본 대조이며 기아 전 항목 승인 아님','records':rows,'runtimeApproved':False},ensure_ascii=False,indent=2),encoding='utf8')
print(len(rows))
