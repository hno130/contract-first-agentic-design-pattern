# Improvement Brief

## 보완 전 한계

1. 패턴의 차별점이 약했다.
   - 기존 Plan-and-Execute, ReAct, Reflexion, TDD Agent와 무엇이 다른지 설명이 부족했다.

2. 계약 스키마가 단순했다.
   - 목표, 가정, 수용 기준은 있었지만 범위, 제외 범위, 기준 우선순위, 증거 타입이 없었다.

3. 완료 판정 기준이 명시적이지 않았다.
   - 모든 기준이 같은 무게로 취급되어 `must`와 `should`를 구분하기 어려웠다.

4. 수리 루프가 설명 수준에 가까웠다.
   - 실패 기준을 보고하긴 했지만, 실패 기준별 수리 계획이 별도 산출물로 남지 않았다.

5. 최종 보고 산출물이 약했다.
   - 실행 로그는 있었지만, 통과 기준과 잔여 위험을 요약하는 최종 리포트가 없었다.

6. 검증 케이스가 조금 얕았다.
   - 필수 컬럼 누락과 잘못된 revenue는 검증했지만, 빈 month와 파일 없음 같은 운영 오류 검증이 없었다.

## 적용한 보완

1. README에 차별점 표를 추가했다.
   - Plan-and-Execute, ReAct, Reflexion, TDD Agent와 비교해 Contract-First의 위치를 선명하게 만들었다.

2. 계약 스키마를 확장했다.
   - `scope`, `out_of_scope`, `priority`, `category`, `evidence`, `failure_policy`, `repair_policy`를 추가했다.

3. 완료 판정을 `must` 기준 중심으로 바꿨다.
   - 데모에서는 모든 `must` 기준이 통과해야 최종 성공으로 판정한다.

4. Repair Planner를 추가했다.
   - 실패한 기준마다 원인 진단과 수정 행동을 만들고 `repair_plan_attempt_1.json`으로 저장한다.

5. Final Reporter를 추가했다.
   - 최종 상태, 시도 횟수, 통과 기준, 수리 계획, 잔여 위험을 `final_report.md`로 저장한다.

6. 검증 케이스를 확장했다.
   - 기존 C1-C4에 더해 C5 빈 month 검증, C6 파일 없음 검증을 추가했다.

## 보완 후 데모가 보여주는 것

- 에이전트가 바로 구현하지 않고 계약을 먼저 만든다.
- 계약에는 범위, 제외 범위, 가정, 우선순위, 증거 타입이 있다.
- 첫 구현은 일부 기준을 실패한다.
- Verifier가 실패 기준을 분리해서 기록한다.
- Repair Planner가 실패 기준별 수리 계획을 만든다.
- 두 번째 구현은 수리 계획을 반영한다.
- 모든 `must` 기준 통과 후 최종 리포트를 생성한다.

## 남은 확장 아이디어

- 실제 LLM 호출을 붙여 Contract Generator와 Executor를 동적으로 만들기
- Verifier를 별도 프로세스나 별도 모델로 분리하기
- 숨겨진 테스트 케이스를 추가해 형식적 통과를 줄이기
- 계약 버전 관리와 변경 사유 기록 추가하기
- LangGraph, OpenAI Agents SDK, CrewAI 같은 프레임워크로 workflow 구현하기
