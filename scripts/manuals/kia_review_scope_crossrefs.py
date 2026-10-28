"""Apply explicit scope decisions; these are never semantic review approvals."""
import json,pathlib,re,collections
R=pathlib.Path(__file__).resolve().parents[2];RAW=R/'.local/manual-review/2026-10-28/kia';O=R/'data/manual-review/2026-10-28'
units=json.loads((RAW/'crossref-units.json').read_text('utf8'))
out=[]
for u in units:
 title=u['label'];reason=None
 if re.search('연료 필터의 교체|냉각수 교체|점화플러그|에어클리너|폭설',title):reason='정기 교체·일반 관리 절. 해당 경고의 즉시 운전자 대처를 완결하는 필수 참조가 아님.'
 elif re.search('소화기 (비치|사용)|안전삼각대|^설치 방법$|차량 고정용 고리',title):reason='부품 구성·장착·비치의 일반 사용 설명. 경고 대처의 중지/정차/견인 방식과 제한은 별도 해당 절에서 검토.'
 elif re.search('교차로|건널목|^사고 발생 시$|^사고 또는 고장 발생 시$|노상에서 주행 중',title):reason='도로 위치별 사고·고장 일반 행동. 경고가 요구한 정차/운행중지와 핵심 비상제동·견인·EV 화재 제한은 별도 절 검토.'
 elif len(u['text'])<=90 and len(u['text'])<len(title)+70:reason='상위 제목/목차뿐인 페이지. 같은 문서의 실제 하위 행동 절로 대체.'
 scope='SUBSTITUTE_REFERENCE' if reason and reason.startswith('상위') else 'OUT_OF_SCOPE' if reason else 'REQUIRED_ACTION_REVIEW'
 out.append({'key':u['key'],'sequence':u['sequence'],'label':title,'scope_disposition':scope,'reason':reason or '해당 경고의 점검/중지/재출발/비상제동/타이어 임시조치/견인·충전·화재 행동 및 필수 주의.','source_urls':[a['source_url'] for a in u['occurrences']]})
(O/'kia-crossref-scope.json').write_text(json.dumps({'scope_note':'659 is acquisition candidate denominator, not required count; no scope disposition is semantic approval.','counts':dict(collections.Counter(x['scope_disposition'] for x in out)),'entries':out},ensure_ascii=False,indent=2),'utf8')
print(collections.Counter(x['scope_disposition'] for x in out))
