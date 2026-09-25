# 뉴스 기사 크롤러

공개적으로 접근 가능한 뉴스 기사 URL 한 건을 분석해 제목, 언론사, 기자, 작성일, 본문과 이미지 정보를 추출하는 간단한 로컬 애플리케이션입니다. Streamlit 화면에서 결과를 확인하고 JSON 또는 Markdown 파일로 내려받을 수 있으며, CLI에서도 파일로 저장할 수 있습니다.

로그인, 유료벽, CAPTCHA 또는 robots.txt 제한을 우회하지 않습니다. `robots.txt`가 명시적으로 차단한 페이지는 수집하지 않으며, 요청마다 타임아웃을 적용합니다. 같은 URL의 Streamlit 재요청은 10분간 캐시되어 불필요한 요청을 줄입니다.

## Python 버전

Python 3.11 이상을 권장합니다.

## 설치 방법

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## 실행 방법

웹 UI는 아래 명령으로 실행합니다.

```bash
streamlit run app.py
```

브라우저에서 표시된 로컬 주소를 열고 기사 URL을 입력한 뒤 **크롤링**을 누르세요. 대표 이미지와 본문 이미지는 화면에서 미리 볼 수 있고, 하단 버튼으로 UTF-8 JSON 또는 Markdown을 다운로드합니다.

## CLI 사용법

표준 출력으로 UTF-8 JSON을 받습니다.

```bash
python main.py "https://example.com/news/article"
```

파일 저장 옵션도 사용할 수 있습니다.

```bash
python main.py "https://example.com/news/article" --json article.json --markdown article.md
```

## Streamlit 사용법

1. `streamlit run app.py`를 실행합니다.
2. `http://` 또는 `https://` 기사 URL을 입력합니다.
3. **크롤링**을 클릭하고 로딩이 끝날 때까지 기다립니다.
4. 추출된 메타데이터·본문·이미지를 확인하고 원하는 형식으로 다운로드합니다.

URL 형식, 사설/로컬 네트워크 접근, 네트워크 오류, 접근 제한은 이해하기 쉬운 메시지로 표시됩니다. 원본 URL은 결과 화면과 모든 내보내기 결과에 보존됩니다.

## JSON schema

```json
{
  "url": "string (최종 기사 URL)",
  "source_url": "string (사용자가 입력한 원본 URL)",
  "title": "string",
  "publisher": "string",
  "author": "string",
  "published_at": "string",
  "article_text": "string",
  "lead_image": "string",
  "images": [{"url": "string", "caption": "string", "alt": "string", "credit": "string"}],
  "quality": {"title": true, "author": true, "date": true, "body_length": 0, "image_count": 0, "score": 0.0, "warnings": []}
}
```

모든 텍스트 출력은 UTF-8이며 한국어를 이스케이프하지 않습니다. Markdown에는 YAML front matter(`title`, `publisher`, `author`, `published_at`, `source_url`), 본문, 대표 이미지 및 본문 이미지 설명을 포함합니다.

## 프로젝트 구조

```text
app.py                 Streamlit UI
main.py                CLI 진입점
crawler/fetcher.py     URL 검증, robots 정책, HTTP 요청/타임아웃
crawler/extractor.py   본문·메타데이터·이미지 통합 추출
crawler/metadata.py    JSON-LD/OpenGraph/HTML 메타데이터
crawler/images.py      이미지 URL 정규화 및 필터링
crawler/exporters.py   JSON/Markdown 내보내기
tests/                 자동 테스트
```

## 테스트

```bash
pytest -q
```

## 알려진 한계

- JavaScript 실행 뒤에만 표시되는 기사 내용은 추출하지 못할 수 있습니다.
- 사이트별 전용 선택자를 사용하지 않으므로 비표준 HTML에서는 메타데이터나 본문 정확도가 낮아질 수 있습니다.
- 접근 권한이 필요한 기사, 유료벽, CAPTCHA, `robots.txt` 차단 페이지는 수집하지 않습니다.
- 이미지 필터는 휴리스틱 방식이므로 광고·로고를 완벽히 구분하지 못할 수 있습니다.
