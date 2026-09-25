import unittest

from crawler.extractor import extract_article


HTML = """
<html><head>
 <title>Fallback title</title><meta property="og:site_name" content="Example News">
 <meta property="og:image" content="/assets/hero.jpg"><meta name="author" content="Meta Author">
 <script type="application/ld+json">{"@context":"https://schema.org","@type":"NewsArticle","headline":"JSON-LD headline","author":{"name":"Jane Doe"},"datePublished":"2026-01-02T03:04:05Z","publisher":{"name":"Example News"},"image":"/assets/hero.jpg","articleBody":"JSON-LD article body."}</script>
 </head><body><header><img src="/logo.png"></header><article><p>JSON-LD article body.</p><img src="/assets/hero.jpg"><img data-src="images/body.jpg"><img src="/avatar.png"><img src="/pixel.gif" width="1" height="1"></article></body></html>
"""


class ExtractArticleTests(unittest.TestCase):
    def test_jsonld_takes_priority_and_images_are_cleaned(self):
        result = extract_article("https://news.example/story", HTML)
        self.assertEqual(result["title"], "JSON-LD headline")
        self.assertEqual(result["author"], "Jane Doe")
        self.assertEqual(result["published_at"], "2026-01-02T03:04:05Z")
        self.assertEqual(result["article_text"], "JSON-LD article body.")
        self.assertEqual(result["lead_image"], "https://news.example/assets/hero.jpg")
        self.assertEqual(result["images"], ["https://news.example/assets/hero.jpg", "https://news.example/images/body.jpg"])

    def test_html_metadata_and_article_fallback(self):
        html = "<html><head><meta property='og:title' content='OG title'></head><body><main><h1>Ignored h1</h1><p>Useful fallback copy.</p></main></body></html>"
        result = extract_article("https://example.org/a", html)
        self.assertEqual(result["title"], "OG title")
        self.assertIn("Useful fallback copy.", result["article_text"])
