# News Crawler MVP

공개 뉴스 기사 URL 하나에서 구조화된 기사 데이터를 추출하는 Python 3.11+ CLI입니다. robots.txt, 로그인, 유료벽, CAPTCHA를 우회하지 않습니다.

## 설치

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 실행

```bash
python main.py "https://www.theguardian.com/world/live/2025/oct/01/mette-frederiksen-denmark-europe-russia-vladimir-putin-volodymyr-zelenskyy-ukraine-hybrid-war-security-europe-live-news"
```

표준 출력으로 다음 JSON을 출력합니다.

```json
{
  "url": "...",
  "title": "...",
  "publisher": "...",
  "author": "...",
  "published_at": "...",
  "article_text": "...",
  "lead_image": "...",
  "images": ["..."]
}
```

## 추출 전략

1. JSON-LD의 `NewsArticle`/`Article`을 먼저 사용합니다.
2. OpenGraph 및 일반 HTML metadata를 보완합니다.
3. `trafilatura`로 본문을 자동 추출하고, 실패하면 `article`, `main`, `role=main`의 텍스트 후보를 사용합니다.
4. 대표 및 본문 이미지 URL을 절대 URL로 정규화하고 중복·로고·아이콘·광고/추적 픽셀 후보를 제외합니다.

## 테스트

```bash
python -m unittest discover -s tests -v
```

## 한계

- JavaScript 렌더링 후에만 나타나는 내용은 수집하지 않습니다.
- 사이트별 DOM selector를 의도적으로 사용하지 않으므로 비표준 마크업에서는 정확도가 떨어질 수 있습니다.
- 이미지 제외 규칙은 URL/속성 기반 휴리스틱이며 모든 광고·로고를 보장해 판별하지는 않습니다.
- 접근 제한, 유료벽, CAPTCHA 및 robots 정책을 우회하지 않습니다.
