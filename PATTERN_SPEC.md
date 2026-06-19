# Pattern Specification: Contract-First Agentic Design Pattern

## 1. Pattern Name

Contract-First Agentic Design Pattern

## 2. Intent

에이전트가 실행 전에 검증 가능한 완료 계약을 만들고, 그 계약을 기준으로 실행, 검증, 수리를 반복하게 한다.

이 패턴의 목적은 다음과 같다.

- 사용자와 에이전트 사이의 완료 기준을 명확히 한다.
- 결과물의 성공/실패를 증거 기반으로 판단한다.
- 실패한 요구사항만 대상으로 수리 범위를 좁힌다.
- 긴 작업에서 목표 이탈과 맥락 드리프트를 줄인다.

## 3. Context

다음 조건에서 이 패턴이 특히 유용하다.

- 결과물을 실행하거나 검사할 수 있다.
- 작업 실패 비용이 있다.
- 사용자의 요구가 여러 조건으로 구성되어 있다.
- 검증 가능한 산출물이 필요하다.
- 에이전트가 여러 도구를 호출하거나 여러 단계를 거쳐야 한다.

## 4. Problem

에이전트가 바로 실행하면 빠르지만, 다음 문제가 생긴다.

- 목표와 완료 기준이 암묵적이다.
- 검증 기준이 작업 중간에 바뀌거나 잊힌다.
- 실패 원인을 기준별로 분해하기 어렵다.
- 에이전트가 그럴듯한 결과를 성공으로 착각할 수 있다.
- 최종 보고에서 무엇이 통과했는지 증명하기 어렵다.

## 5. Forces

이 패턴은 다음 긴장 관계를 다룬다.

| 힘 | 설명 |
|---|---|
| 속도 vs 검증 가능성 | 바로 실행하면 빠르지만 검증이 약해진다. |
| 자율성 vs 통제 | 에이전트가 자율적으로 움직이되 완료 기준은 통제되어야 한다. |
| 유연성 vs 안정성 | 작업 중 배운 내용을 반영하되 계약 변경은 추적되어야 한다. |
| 단일 결과 vs 기준별 증거 | 최종 산출물뿐 아니라 각 기준의 통과 증거가 필요하다. |

## 6. Solution

작업을 시작하기 전에 계약을 만든다. 계약은 목표, 범위, 제외 범위, 가정, 수용 기준, 검증 방법, 증거 타입, 실패 정책, 수리 정책을 포함한다.

그 뒤 에이전트는 다음 순서로 동작한다.

1. 계약 생성
2. 위험한 가정 확인
3. 결과물 생성
4. 계약 기준별 검증
5. 실패 기준별 수리 계획 생성
6. 수리 실행
7. 모든 필수 기준 통과 시 최종 보고

## 7. Participants

| 참여자 | 책임 |
|---|---|
| Contract Generator | 사용자 요청을 구조화된 계약으로 변환 |
| Assumption Gate | 위험한 가정을 확인하거나 보수적 기본값으로 잠금 |
| Executor | 계약을 만족하는 결과물 생성 |
| Verifier | 기준별 통과 여부와 증거 기록 |
| Repair Planner | 실패 기준별 원인과 수정 행동 도출 |
| Repair Executor | 실패 기준만 대상으로 수정 |
| Final Reporter | 통과 기준, 실패 기준, 증거, 잔여 위험 보고 |

## 8. Contract Model

계약은 다음 속성을 가져야 한다.

| 필드 | 필수 | 설명 |
|---|---|---|
| `goal` | 예 | 작업 목표 |
| `scope` | 예 | 포함 범위 |
| `out_of_scope` | 예 | 제외 범위 |
| `assumptions` | 예 | 가정 목록 |
| `acceptance_criteria` | 예 | 수용 기준 |
| `failure_policy` | 예 | 완료 판정 규칙 |
| `repair_policy` | 예 | 수리 규칙 |
| `max_iterations` | 예 | 최대 반복 횟수 |

각 수용 기준은 다음 속성을 가진다.

| 필드 | 필수 | 설명 |
|---|---|---|
| `id` | 예 | 기준 식별자 |
| `priority` | 예 | `must`, `should`, `could` |
| `category` | 예 | 기준 유형 |
| `statement` | 예 | 기준 내용 |
| `verification` | 예 | 검증 방법 |
| `evidence` | 예 | 성공/실패 판단 증거 |

## 9. Completion Rule

기본 완료 규칙은 다음과 같다.

```text
All must acceptance criteria must pass.
```

`should`와 `could` 기준은 품질 향상에는 사용하지만, 기본적으로 완료 판정의 필수 조건으로 삼지 않는다. 단, 도메인에 따라 `should` 실패를 승인 필요 상태로 설정할 수 있다.

## 10. Repair Rule

수리는 실패한 기준에만 집중한다.

```text
failed_criteria -> diagnosis -> repair_action -> re-verification
```

이 규칙은 수정 범위를 줄이고, 통과한 기준을 다시 망가뜨릴 위험을 낮춘다.

## 11. Resulting Context

패턴 적용 후 기대되는 상태는 다음과 같다.

- 작업의 성공 기준이 명확하다.
- 검증 증거가 기준별로 남는다.
- 실패 기준과 수리 계획이 추적 가능하다.
- 최종 보고가 설명이 아니라 증거 중심이 된다.

## 12. Known Risks

| 위험 | 대응 |
|---|---|
| 잘못된 계약으로 최적화 | 가정, 범위, 제외 범위를 명시하고 위험 가정을 확인한다. |
| 과도한 기준 생성 | `must`, `should`, `could`로 우선순위를 둔다. |
| 형식적 통과 | Verifier를 Executor와 분리하고 숨겨진 테스트를 둔다. |
| 계약 부패 | 계약 변경 시 버전과 변경 이유를 기록한다. |
| 비용 증가 | 단순 작업에는 적용하지 않는다. |

## 13. Minimal Example

```text
Request:
CSV 파일을 읽어 월별 매출 요약을 만드는 Python 스크립트를 만들어줘.

Contract:
- C1: CLI 인자로 CSV 경로를 받는다.
- C2: 필수 컬럼을 검증한다.
- C3: 월별 합계를 정렬해서 출력한다.
- C4: 숫자가 아닌 revenue를 거부한다.
- C5: 빈 month를 거부한다.
- C6: 없는 파일을 traceback 없이 처리한다.

Loop:
first implementation -> verifier fails C2/C4/C5/C6
repair plan -> repaired implementation -> all criteria pass
```

## 14. When To Use

- 코드 생성 에이전트
- 데이터 분석 에이전트
- 문서 변환 에이전트
- 보고서 생성 에이전트
- 장기 자동화 에이전트
- 다중 도구 워크플로우

## 15. When Not To Use

- 짧은 일반 질의응답
- 즉흥적인 창작 작업
- 기준을 고정하기 어려운 탐색형 브레인스토밍
- 계약 작성 비용이 결과물보다 큰 작업
