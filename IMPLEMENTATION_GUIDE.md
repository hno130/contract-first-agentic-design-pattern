# Implementation Guide

## 목표

이 문서는 Contract-First Agentic Design Pattern을 실제 에이전트 시스템에 구현할 때 필요한 구조와 체크리스트를 정리한다.

## 권장 모듈 구조

```text
contract_first_agent/
  contract_generator
  assumption_gate
  executor
  verifier
  repair_planner
  repair_executor
  final_reporter
```

## 구현 단계

1. 사용자 요청을 받는다.
2. 계약을 생성한다.
3. 계약 스키마를 검증한다.
4. 위험한 가정을 확인한다.
5. 계약을 기준으로 실행한다.
6. 기준별로 검증한다.
7. 실패 기준만 수리 계획에 넣는다.
8. 수리 후 다시 검증한다.
9. 반복 한도에 도달하거나 모든 필수 기준이 통과하면 종료한다.
10. 최종 리포트에 증거와 잔여 위험을 남긴다.

## 필수 체크리스트

- 계약이 구조화된 데이터로 저장되는가?
- 각 기준에 `id`, `priority`, `verification`, `evidence`가 있는가?
- 완료 판정이 코드로 명시되어 있는가?
- 검증 결과가 기준별로 기록되는가?
- 실패 기준별 수리 계획이 남는가?
- 최종 리포트가 통과 기준과 잔여 위험을 모두 포함하는가?
- 재실행해도 같은 결과를 얻을 수 있는가?

## Verifier 설계 원칙

Verifier는 가능하면 Executor와 분리한다. 같은 모델이나 같은 코드 경로가 결과 생성과 검증을 모두 담당하면 형식적 통과 위험이 커진다.

좋은 Verifier는 다음 특성을 가진다.

- 기준별로 통과/실패를 반환한다.
- 실패 세부 정보를 증거로 남긴다.
- stdout, stderr, exit code, 파일 diff, 테스트 결과처럼 관찰 가능한 값을 사용한다.
- 숨겨진 테스트 또는 독립 샘플을 일부 포함한다.

## Repair Planner 설계 원칙

Repair Planner는 실패한 기준 전체를 하나로 뭉개지 않는다. 각 기준에 대해 다음을 만든다.

- 실패 기준 ID
- 진단
- 수정 행동
- 재검증 방법

예시:

```json
{
  "criterion_id": "C4",
  "diagnosis": "ValueError가 그대로 traceback으로 노출된다.",
  "action": "숫자 변환 오류를 잡아 행 번호가 포함된 에러 메시지로 반환한다."
}
```

## 완료 판정

기본 완료 판정은 다음과 같이 두는 것이 가장 안전하다.

```text
pass = all(criteria where priority == "must")
```

`should` 기준은 품질 경고로, `could` 기준은 확장 아이디어로 다룬다.

## 로그와 산출물

최소 산출물:

- `contract.json`
- `contract.md`
- `verification_trace.json`
- `repair_plan_attempt_N.json`
- `final_report.md`
- 실제 결과물

권장 산출물:

- `manifest.json`
- `execution_summary.json`
- 계약 버전 기록
- 숨겨진 테스트 결과

## 실제 프레임워크에 붙이는 방법

LangGraph, OpenAI Agents SDK, CrewAI 같은 프레임워크에서는 각 참여자를 노드나 tool로 분리하면 된다.

```text
contract_node -> assumption_node -> executor_node -> verifier_node
verifier_node -> reporter_node if pass
verifier_node -> repair_planner_node -> executor_node if fail
```

## 품질 기준

좋은 Contract-First 구현은 다음 질문에 답할 수 있어야 한다.

- 무엇이 끝나야 완료인가?
- 그 기준을 어떻게 검증했는가?
- 어떤 기준이 실패했는가?
- 실패 원인은 무엇인가?
- 무엇을 고쳤는가?
- 최종적으로 어떤 증거로 통과를 주장하는가?
