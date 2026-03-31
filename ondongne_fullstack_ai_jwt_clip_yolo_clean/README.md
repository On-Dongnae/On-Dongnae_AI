# 온동네 Fullstack AI (JWT + Upload + CLIP/YOLO)

이 프로젝트는 다음을 한 번에 포함합니다.
- PostgreSQL 16
- Redis
- FastAPI 백엔드
- JWT 로그인
- 이미지 업로드
- AI 서비스 (히든 미션 랭킹 + 실제 이미지 입력 기반 인증 검증)
- CLIP + YOLO 추론 연결

## 실행
```bash
cp .env.example .env
docker compose up --build
```

- 백엔드 Swagger: http://localhost:8000/docs
- AI Swagger: http://localhost:8010/docs

## 추천 테스트 순서
1. `POST /api/v1/auth/signup`
2. `POST /api/v1/auth/login` -> access token 복사
3. Swagger 우측 상단 Authorize에서 `Bearer <token>` 입력
4. `POST /api/v1/verifications/ai-evaluate-and-save` 에서 이미지 업로드
5. `GET /api/v1/verifications`
6. `GET /api/v1/rankings/personal`

## 주요 엔드포인트
### 인증
- `POST /api/v1/auth/signup`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### 히든 미션
- `POST /api/v1/hidden-missions/ai-generate-and-save`
- `GET /api/v1/hidden-missions/{week_id}`

### 인증 검증
- `POST /api/v1/verifications/ai-evaluate-and-save`
  - multipart/form-data
  - fields: `mission_type`, `title`, `description_text`, `files`

### 업로드 파일 조회
- `GET /api/v1/uploads/{path}`

## CLIP/YOLO 동작 방식
- CLIP: 미션 타입별 프롬프트와 이미지 유사도 계산
- YOLO: person, bottle, trash can 등 탐지
- 최종 판정: 기존 학습된 LogisticRegression 분류기 입력으로 연결

## 주의
처음 AI 컨테이너 실행 시 CLIP/YOLO 가중치를 다운로드하므로 시간이 더 걸릴 수 있습니다.
