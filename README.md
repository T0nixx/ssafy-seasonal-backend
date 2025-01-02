# FAST BIZ

## 프로젝트 개요

- 취업 준비생과 주식 투자자가 기업에 대한 비재무적 정보를 쉽게 탐색 및 분석할 수 있도록 QA 기반 챗봇 서비스

## 사용법

- 프론트엔드 repository는 이 [링크](https://github.com/T0nixx/ssafy-seasonal-frontend/)를 참조해주세요.

1. .env 파일을 생성하고 UPSTAGE_API_KEY와 PINECONE_API_KEY를 환경변수로 지정합니다.
2. embedded-docs 폴더를 생성하고 pdf 문서를 넣은 후 embed.py를 실행시킵니다.
3. pinecone에 index 생성이 완료되면 app.py를 실행시킵니다.

- 로컬 실행 방법<br>

  ```
  pip install -r requirements.txt
  ```

  ```
  python app.py
  ```

## 배포된 링크

- https://main.d236dnvke84iow.amplifyapp.com/
