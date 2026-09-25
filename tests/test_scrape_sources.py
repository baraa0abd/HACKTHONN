import unittest
from scrape_sources import parse_page
class ScraperTests(unittest.TestCase):
 def test_structured_extraction_and_dedup(self):
  raw=b'<html><head><title>T</title><meta name="description" content="D"></head><body><main><h1>A</h1><p>Fact one.</p><p>Fact one.</p><h2>B</h2><ul><li>Fact two.</li></ul><a href="/data">Data</a></main></body></html>'
  x=parse_page(raw,'https://example.org/page');self.assertEqual(x['title'],'T');self.assertEqual(len(x['sections']),2);self.assertEqual(x['links'][0]['url'],'https://example.org/data')
if __name__=='__main__':unittest.main()
