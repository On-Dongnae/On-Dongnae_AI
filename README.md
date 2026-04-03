# ondongnae_ai

## 개요
이 프로젝트 패키지는 서로 연결되는 두 부분으로 구성되어 있습니다.

1. **AI 서비스 (`ai_service/`)**: Python/FastAPI로 구현되었으며, 미션 평가와 인증 추론을 담당합니다.
2. **백엔드 연동 모듈 (`backend_module/`)**: Java/Spring 스타일 구조로 구현되었으며, 선택된 도메인 엔티티와 AI 서비스를 연결하는 역할을 합니다.

이 패키지는 다음 엔티티 범위에 대해서만 AI 관련 백엔드 연동에 집중하도록 구성되어 있습니다.
- `Mission`
- `UserMission`
- `MissionVerification`
- `VerificationImage`

그 외 백엔드 도메인은 이 패키지에 포함되어 있지 않습니다.

---

## 프로젝트 구조

```text
semo/
└── ai/
    ├── ai_service/
    │   ├── app/
    │   │   └── main.py
    │   ├── data/
    │   │   ├── hidden_mission/
    │   │   │   └── hidden_mission_candidates.csv
    │   │   └── verification/
    │   │       └── verification_final_decision.csv
    │   ├── models/
    │   │   ├── hidden_mission_preprocessor.joblib
    │   │   ├── hidden_mission_approve_clf.joblib
    │   │   ├── hidden_mission_score_regressor.joblib
    │   │   └── verification_final_decision_clf.joblib
    │   ├── scripts/
    │   │   ├── generate_seed_data.py
    │   │   ├── train_hidden_mission_ranker.py
    │   │   └── train_verification_decision_model.py
    │   ├── Dockerfile
    │   └── requirements.txt
    │
    ├── backend_module/
    │   └── src/
    │       └── main/
    │           └── java/
    │               └── com/
    │                   └── semo/
    │                       └── group1/
    │                           └── on_dongnae/
    │                               ├── client/
    │                               │   └── AiServiceClient.java
    │                               ├── config/
    │                               ├── controller/
    │                               │   ├── MissionAiController.java
    │                               │   └── MissionVerificationAiController.java
    │                               ├── dto/
    │                               │   ├── HiddenMissionAiRequest.java
    │                               │   ├── HiddenMissionAiResponse.java
    │                               │   └── VerificationAiResponse.java
    │                               ├── repository/
    │                               │   ├── MissionRepository.java
    │                               │   ├── UserMissionRepository.java
    │                               │   ├── MissionVerificationRepository.java
    │                               │   └── VerificationImageRepository.java
    │                               └── service/
    │                                   ├── MissionAiService.java
    │                                   └── MissionVerificationAiService.java
    │
    ├── .env
    ├── docker-compose.yml
    └── README.md
```

---

## AI 서비스

### 목적
AI 서비스는 다음 두 기능 영역을 지원하는 추론 엔드포인트를 제공합니다.

1. **히든 미션 평가**
2. **미션 인증 분석**

### 1) 히든 미션 평가
이 부분은 전체 비즈니스 워크플로를 생성하는 것이 아니라, 히든 미션 후보를 평가하는 역할을 합니다.

#### 입력 특성
히든 미션 모델은 다음과 같은 구조화된 미션 관련 입력값을 사용합니다.
- 미션 제목
- 미션 설명
- 계절
- 지역 유형
- 주간 날씨 조건
- 평균 기온
- 강수 일수
- 야외활동 가능 일수
- 대기질 불량 일수
- 미션 유형
- 실외/단체 여부 플래그
- 난이도
- 보너스 점수

#### 출력
모델은 다음과 같은 값을 반환합니다.
- 미션 승인 확률
- 예측된 종합 점수

#### 관련 파일
- `ai_service/scripts/train_hidden_mission_ranker.py`
- `ai_service/models/hidden_mission_preprocessor.joblib`
- `ai_service/models/hidden_mission_approve_clf.joblib`
- `ai_service/models/hidden_mission_score_regressor.joblib`

### 2) 미션 인증 분석
이 부분은 업로드된 인증 입력을 분석하고, 권장 인증 상태를 반환합니다.

#### 추론 흐름
서비스는 여러 신호를 결합합니다.
- CLIP 기반 이미지-텍스트 매칭 점수
- YOLO 기반 객체/인원 탐지
- 이미지 품질 추정
- 미션 유형 메타데이터
- 설명 텍스트 길이 및 규칙 기반 검사

#### 출력
인증 엔드포인트는 다음과 같은 데이터를 반환합니다.
- CLIP 매칭 점수
- 가장 잘 매칭된 프롬프트
- 인원 수
- 탐지된 클래스
- 객체 존재 요약
- 이미지 품질 점수
- 권장 인증 상태
- 신뢰도 점수

#### 관련 파일
- `ai_service/app/main.py`
- `ai_service/models/verification_final_decision_clf.joblib`

---

## 학습 데이터 및 학습 스크립트

이 패키지는 AI 서비스용 시드 데이터셋과 재학습 스크립트를 포함합니다.

### 포함된 데이터셋
- `ai_service/data/hidden_mission/hidden_mission_candidates.csv`
- `ai_service/data/verification/verification_final_decision.csv`

### 포함된 학습 스크립트
- `ai_service/scripts/generate_seed_data.py`
- `ai_service/scripts/train_hidden_mission_ranker.py`
- `ai_service/scripts/train_verification_decision_model.py`
  
## 2. 학습 실행 절차

작업 위치:
```bash
cd semo/ai/ai_service
```

필요 패키지 설치:
```bash
pip install -r requirements.txt
```

학습 실행:
```bash
python scripts/train_hidden_mission_ranker.py
python scripts/train_verification_decision_model.py
```

학습이 끝나면 모델 파일이 `models/` 폴더에 저장된다.

### 모델 산출물
사전 학습된 산출물이 `ai_service/models/` 아래에 포함되어 있어, 재학습 없이도 즉시 서비스와 연결할 수 있습니다.

---

## 백엔드 연동 모듈

### 범위
백엔드 연동 코드는 미션 관련 엔티티 영역으로 제한되어 있으며, 다음 엔티티 흐름에 AI 기능을 연결하도록 설계되어 있습니다.
- `Mission`
- `UserMission`
- `MissionVerification`
- `VerificationImage`

### 포함된 백엔드 구성 요소

#### 1) Client
- `client/AiServiceClient.java`

이 구성 요소는 백엔드 애플리케이션에서 Python AI 서비스를 호출하는 역할을 담당합니다.

#### 2) DTO
- `dto/HiddenMissionAiRequest.java`
- `dto/HiddenMissionAiResponse.java`
- `dto/VerificationAiResponse.java`

이 클래스들은 백엔드와 AI 서비스 사이에서 교환되는 요청/응답 페이로드를 정의합니다.

#### 3) Service
- `service/MissionAiService.java`
- `service/MissionVerificationAiService.java`

이 서비스들은 미션 관련 백엔드 로직을 AI 서비스와 연결합니다.

주요 역할은 다음과 같습니다.
- 미션 데이터로부터 AI 입력 준비
- 히든 미션 평가 요청
- 인증 분석 요청
- AI 응답을 백엔드 워크플로 객체로 다시 매핑

#### 4) Controller
- `controller/MissionAiController.java`
- `controller/MissionVerificationAiController.java`

이 컨트롤러들은 AI 관련 작업을 실행할 수 있는 백엔드 측 엔드포인트를 제공합니다.

#### 5) Repository
- `repository/MissionRepository.java`
- `repository/UserMissionRepository.java`
- `repository/MissionVerificationRepository.java`
- `repository/VerificationImageRepository.java`

이 리포지토리들은 미션 관련 AI 연동에 사용되는 영속성 계층 범위를 나타냅니다.

---

## 백엔드-AI 연동 설계

### 히든 미션 연동
백엔드는 `Mission` 도메인에서 미션 후보 데이터를 수집하고, 이를 `HiddenMissionAiRequest`로 변환한 뒤 AI 서비스로 전송하여 히든 미션 평가를 지원할 수 있습니다.

### 인증 연동
백엔드는 `MissionVerification`의 인증 메타데이터와 `VerificationImage`의 관련 이미지 참조를 수집하고, AI 인증 분석 엔드포인트를 호출한 뒤 반환된 상태 및 신뢰도 값을 인증 처리 지원에 활용할 수 있습니다.

### 사용자-미션 연동
`UserMission`은 사용자 진행 상태와 미션별 AI 보조 로직을 연결하는 관계 지점으로 활용될 수 있습니다.

---

## 인프라 파일

### `.env`
포함된 환경 파일에는 PostgreSQL 및 Redis 설정값이 들어 있습니다.

### `docker-compose.yml`
compose 파일은 다음 인프라 컨테이너를 정의합니다.
- PostgreSQL 16
- Redis 7

이 파일은 인프라 서비스에 한정되며, Java 백엔드나 Python AI 서비스의 전체 런타임은 정의하지 않습니다.

---

## 사용 목적
이 패키지는 다음 목적을 위한 집중형 연동 단위로 설계되었습니다.
- AI 모델 서빙 및 재학습
- 백엔드와 AI 간 요청/응답 연결
- 미션 및 인증 관련 도메인 연동
