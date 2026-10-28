"""Persist completed direct readings, with explicit unreviewed reference scope."""
import json,re,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'data/manual-review/2026-10-28';RAW=ROOT/'.local/manual-review/2026-10-28/audit/adas'
NOTES={
'FCA':'고장과 센서 가림에 의한 제한을 분리한다. 해당 카메라·레이더 주변의 이물질 또는 원문에 명시된 후방 장비를 제거하며 지속 경고는 지정 정비망에서 점검한다. 경고가 없거나 재시동해도 정상 인식을 보증하지 않는다.',
'LKA':'주황/황색 고장 경고와 카메라 오염·역광에 따른 제한을 구분한다. 오염·역광 해소 뒤에도 지속하면 점검한다. 재시동이 가림을 없애지 않는다. 차선 불명확·견인·급조향·ESC 개입·과적 등 기능 제한에 대비해 직접 조향한다.',
'LFA':'고장 경고는 지정 정비망에서 점검한다. 차로 이탈방지 보조의 인식·경고 제한이 연결되며 과적·편중 적재는 조향 보조 성능을 낮춘다. 전체 작동 속도를 차종 간 공통값으로 두지 않는다.',
'BCA':'후측방 보조 자체 및 미러/DSM 경고 표시 장치 고장을 점검한다. 눈·비·장착 짐칸·캐리어 등 가림을 제거한 뒤 원문 조건대로 재시동하며 지속 시 정비한다. 짐칸·견인 장비 사용 중 기능을 끄고 직접 주변을 확인한다.',
'SEA':'센서 가림과 기능/미러 경고등 고장을 구분한다. 장착 장비·오염 제거 및 원문 재시동 조건 뒤에도 지속하면 점검한다. 안전 하차를 시스템 표시만으로 판단하지 않는다. 트윈 스윙 도어 등 차종별 가림 조건을 보존한다.',
'SEW':'안전 하차 경고 및 미러 경고등 고장은 점검한다. 후측방 가림·캐리어를 제거하고 원문 복구 조건을 확인한다. 센서 초기화 약 3초 및 경고 부재에서도 인식 불가할 수 있어 직접 확인한다.',
'ISLA':'센서 오염을 제거하고도 속도 제한 경고가 지속되면 점검한다. 재시동으로 가림이 해결된다고 보장하지 않는다. 표지판·지도·GPS·재부팅·도로 공사 때문에 표시가 틀릴 수 있으므로 운전자가 실제 제한속도를 확인한다.',
'DAW':'기능 고장은 점검하며 카메라 오염 가림은 제거 후 원문에 따라 주행 시 복구한다. 재시동만으로 고장·가림이 해소되지 않는다. 피로 상태의 운행 지속 허가로 해석하지 않는다.',
'SCC':'기능 고장과 전방 레이더 가림을 구분한다. 오염을 제거하고 지속 시 점검한다. 경고 부재·재시동 직후에도 정상 인식이 보장되지 않으므로 운전자가 속도·차간거리를 직접 제어한다.',
'HDA':'기능 고장은 점검한다. IC/JC/휴게소 진입, 내비게이션 부팅·업데이트, 차선 인식 실패·핸즈오프 등 자동 해제를 구분하고 직접 조작한다. 견인 시 사용하지 않는다.',
'HBA':'고장 경고는 지정 정비망에서 점검한다. 정상적으로 작동하지 않으면 전조등을 수동 전환한다. 카메라 초기화 및 조명·도로 인식 한계에 대비한다.',
'PDW':'경고가 뜨면 초음파 센서 손상·가림을 확인하고 표면 오염을 제거한다. 계속 경고하면 점검한다. 물체 접근음은 고장음과 분리하며 장착 센서 방향을 확인한다.',
'PCA':'관련 부품 고장 시 기능 전체 또는 고장 방향이 자동 해제될 수 있다. 카메라·초음파 주변 오염을 제거하고 지속 경고는 점검한다. 운전자가 실제 주변을 확인하고 제동한다.',
'RCCA':'센서 및 미러 표시 장치 고장을 점검한다. 후측방 가림 장비·오염 제거 및 원문 재시동 조건을 보존한다. 견인 장비 사용 중 끄고 직접 확인한다. 가림이 남은 재시동은 해결책이 아니다.',
'RSPA':'고장 경고면 기능 사용을 중지하고 점검한다. 준비 중 대기와 스마트키 저전압·유틸리티 모드 같은 미작동 조건을 고장과 구분하고 해당 화면 지시를 따른다.',
'BVM':'미작동·깜빡임·비정상 영상은 점검한다. 방향지시등 종료·비상등·다른 중요 정보로 인한 정상 해제를 구분한다. 렌즈를 깨끗이 하되 강알칼리·휘발유·아세톤을 쓰지 않고 실제 거리를 직접 확인한다.',
'SVM':'녹색·파란색·회색·검정색 등 비정상 화면 또는 깜빡임·영상 이상은 지정 정비망에서 점검한다. 영상만으로 주변 안전을 보증하지 않는다.'}
def main():
 es=json.loads((OUT/'audit-hyundai-adas-inventory.json').read_text(encoding='utf8'))['entries'];us=json.loads((RAW/'fault-units.json').read_text(encoding='utf8'))
 assert len(us)==973
 rows=[]
 for i,e in enumerate(es):
  ids=[u['id'] for u in us if i in u['entries']]
  system=re.search(r'\(([A-Z]+)\)',e['system']).group(1)
  rows.append({'reviewId':f'AUDIT-ADAS-{i:03}','documentId':e['documentId'],'system':e['system'],'sourceURL':e['sourceURL'],'sourceSha256':e['sourceSha256'],'pdfPageRange':e['pdfPages'],
   'reviewedUnitIds':ids,'reviewedUnitHashes':[us[j]['hash'] for j in ids],
   'reviewStatus':'FAULT_OBSTRUCTION_TEXT_REVIEWED','reviewNote':NOTES.get(system,'관련 고장·가림 본문 직접 확인; 개별 조치는 원문 문맥 보존 필요.'),
   'reviewMethod':'고장·가림 전반부 원문 문장을 공백 제거 후 동일 문장만 공유하고 973개 고유 문장/문맥 직접 읽음',
   'limitations':'표제의 전체 일반 성능 한계, 인식 도해 및 모든 재귀 참조 완료를 뜻하지 않음. 실행용 규칙으로 변환·승인하지 않음.',
   'linkedSensorPrecautions':'PENDING_ADDITIONAL_READ','reviewer':'AI','runtimeApproved':False})
 extra=json.loads((RAW/'extra-manifest.json').read_text(encoding='utf8'));eu=json.loads((RAW/'extra-units.json').read_text(encoding='utf8'));sensors=json.loads((RAW/'sensor-manifest.json').read_text(encoding='utf8'));su=json.loads((RAW/'sensor-units.json').read_text(encoding='utf8'))
 assert len(eu)==822 and len(su)==293
 linked=[]
 for kind,manifest,units in [('extra',extra,eu),('sensor',sensors,su)]:
  for i,e in enumerate(manifest):
   if e['code'].startswith(('HR-','HREV-')):continue
   ids=[u['id'] for u in units if i in u['entries']]
   if not ids:continue
   code,year=e['code'].split('-')
   if '모니터링' in e['title']:
    note='전방 주시 고장은 점검한다. 실내 카메라와 얼굴 사이 가림을 제거하고 얼굴이 일정 시간 인식되면 복구한다. 부드럽고 깨끗한 천으로 닦고 날카로운 도구·화학약품·물 유입·압력/충격을 피한다. 30km/h 이상 및 눈 감음 3초/전방 보기 2초 조건은 이 원문 범위이며 다른 차종에 자동 확장하지 않는다.'
   elif '센서' in e['title'] or kind=='sensor':
    note='센서 또는 주변부를 분리·충격·도장·장식물로 변경하지 않는다. 충격 후 경고가 없어도 점검한다. 레이더 커버·초음파 센서는 부드러운 천을 쓰고 고압 분사·누르기·긁기를 피한다. 광각 렌즈는 원문 허용 순한 비누/중성세제 및 물 세척 조건과 강알칼리·휘발유·아세톤 금지를 보존한다. 정확한 장착 위치는 차종 그림을 참조하며 임의 추정하지 않는다.'
   else:
    note='예외 목차 PDF 해당 페이지의 고장·가림 및 연결 문맥 직접 검토. 가림 제거·원문 복구 조건 뒤 지속 시 정비하며 재시동만으로 남아 있는 가림을 해소하지 않는다. 정상 기능 해제·부주의/휴식 경고와 장치 고장을 구분한다. 센서 주의사항은 별도 연결 기록을 참조한다.'
   linked.append(dict(reviewId=f'AUDIT-ADAS-{kind}-{i:03}',documentId='HYUNDAI-'+e['code'],title=e['title'],sourceURL=f'https://ownersmanual.hyundai.com/full_pdf/{code}/{year}/ko_KR',sourceSha256=e['hash'],pdfPageRange=e['pages'],reviewedUnitHashes=[units[j]['hash'] for j in ids],reviewStatus='SOURCE_TEXT_REVIEWED',reviewNote=note,reviewer='AI',runtimeApproved=False,scope='경고 대처와 센서 취급 필수 문맥; 일반 기능 성능의 전수 승인 아님'))
 for r in rows:
  r['linkedSensorPrecautions']='TEXT_REVIEWED_SEE_LINKED_RECORDS'
 (OUT/'audit-hyundai-adas-review.json').write_text(json.dumps({'reviewedUniqueUnits':{'faultObstruction':973,'extraContextAndDMS':822,'sensorPrecautions':293},'rows':rows,'linkedRecords':linked,'allCountermeasuresReviewed':False,'runtimeApproved':False,'scopeExclusions':['각 기능의 모든 일반 성능 한계와 인식 도해의 재귀 검토','HR/HREV 고장 절차는 현대 담당자의 hyundai-legacy-adas-review.json에 별도 기록'],'remainingSourceIssues':['원문 일부 함수명/문장 오탈자는 전차 공통 규칙으로 정규화하지 않음','SDK 신호 및 실제 사양에 대한 실행 매핑·전문가 승인 미실시']},ensure_ascii=False,indent=2),encoding='utf8')
 print(len(rows))
if __name__=='__main__':main()
