"""Reproducible, polite extractor for the five user-selected light-pollution pages."""
from __future__ import annotations
import csv, hashlib, json, re, time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser
from lxml import html

ROOT=Path(__file__).resolve().parent; OUT=ROOT/'data'/'web_sources'
UA='LaylHackathonResearchBot/1.0 (+https://github.com/baraa0abd/HACKTHONN)'
SOURCES=[
 ('darksky_principles','https://darksky.org/resources/guides-and-how-tos/lighting-principles/'),
 ('nasa_nighttime_lights','https://www.earthdata.nasa.gov/topics/human-dimensions/nighttime-lights'),
 ('globe_at_night','https://globeatnight.org/'),
 ('nasa_worldview','https://worldview.earthdata.nasa.gov/'),
 ('nasa_black_marble','https://www.earthdata.nasa.gov/data/projects/black-marble'),
]
def clean(x):return re.sub(r'\s+',' ',x or '').strip()
def allowed(url):
    u=urlparse(url);rp=RobotFileParser();rp.set_url(f'{u.scheme}://{u.netloc}/robots.txt')
    try:rp.read();return rp.can_fetch(UA,url)
    except Exception:return None
def parse_page(raw,url):
    doc=html.fromstring(raw,base_url=url)
    for bad in doc.xpath('//script|//style|//noscript|//form|//nav|//footer|//header|//aside'):bad.drop_tree()
    title=clean(' '.join(doc.xpath('//title/text()')))
    desc=clean(' '.join(doc.xpath('//meta[@name="description"]/@content|//meta[@property="og:description"]/@content')))
    roots=doc.xpath('//main|//article');root=max(roots,key=lambda x:len(clean(x.text_content()))) if roots else doc
    sections=[];current={'heading':title or 'Page','level':0,'text':[]}
    seen=set()
    for el in root.iter():
        tag=el.tag.lower() if isinstance(el.tag,str) else ''
        if tag not in ('h1','h2','h3','h4','p','li'):continue
        text=clean(el.text_content())
        if not text or text in seen or (tag in ('p','li') and len(text)<3):continue
        seen.add(text)
        if tag in ('h1','h2','h3','h4'):
            if current['text']:sections.append({**current,'text':' '.join(current['text'])})
            current={'heading':text,'level':int(tag[1]),'text':[]}
        else:current['text'].append(text)
    if current['text']:sections.append({**current,'text':' '.join(current['text'])})
    links=[]
    for a in root.xpath('.//a[@href]'):
        href=urljoin(url,a.get('href'));label=clean(a.text_content())
        if href.startswith(('http://','https://')) and (label or href):links.append({'label':label,'url':href})
    links=list({x['url']:(x) for x in links}.values())
    return {'title':title,'description':desc,'sections':sections,'links':links}
def fetch_one(source_id,url):
    stamp=datetime.now(timezone.utc).isoformat();robot=allowed(url)
    base={'source_id':source_id,'url':url,'retrieved_utc':stamp,'robots_allowed':robot}
    if robot is False:return {**base,'status':'blocked_by_robots','error':'robots.txt disallows this URL'}
    try:
        req=Request(url,headers={'User-Agent':UA,'Accept':'text/html,application/xhtml+xml'})
        with urlopen(req,timeout=30) as r:raw=r.read();ctype=r.headers.get('Content-Type','')
        if 'html' not in ctype:return {**base,'status':'unsupported_content','content_type':ctype}
        parsed=parse_page(raw,url);status='ok' if parsed['sections'] else 'metadata_only'
        return {**base,'status':status,'http_sha256':hashlib.sha256(raw).hexdigest(),'content_type':ctype,**parsed}
    except Exception as exc:return {**base,'status':'error','error':f'{type(exc).__name__}: {exc}'}
def build():
    OUT.mkdir(parents=True,exist_ok=True);records=[]
    for i,(sid,url) in enumerate(SOURCES):
        if i:time.sleep(1)
        records.append(fetch_one(sid,url))
    manifest={'schema_version':'1.0','generated_utc':datetime.now(timezone.utc).isoformat(),'collector':'scrape_sources.py','user_agent':UA,'records':records}
    (OUT/'sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    with (OUT/'sections.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['source_id','source_url','retrieved_utc','section_index','heading','level','text']);w.writeheader()
        for r in records:
            for i,s in enumerate(r.get('sections',[])):w.writerow({'source_id':r['source_id'],'source_url':r['url'],'retrieved_utc':r['retrieved_utc'],'section_index':i,**s})
    prompt={'role':'مرجع معرفي موثق عن التلوث الضوئي وبيانات الإضاءة الليلية','rules':['استخدم الحقائق الموجودة فقط','اذكر source_url عند كل إجابة','لا تعامل صفحات التوثيق كقياسات ميدانية','إذا كان status ليس ok فصرّح بعدم توفر المحتوى'],'documents':[{'source_id':r['source_id'],'source_url':r['url'],'retrieved_utc':r['retrieved_utc'],'status':r['status'],'title':r.get('title'),'sections':r.get('sections',[])} for r in records]}
    (OUT/'model_prompt.json').write_text(json.dumps(prompt,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'manifest.json').write_text(json.dumps({'generated_utc':manifest['generated_utc'],'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (OUT/'sources.json',OUT/'sections.csv',OUT/'model_prompt.json')},'source_status':{r['source_id']:r['status'] for r in records}},ensure_ascii=False,indent=2),encoding='utf-8')
    return manifest
if __name__=='__main__':
    result=build();print(json.dumps({r['source_id']:r['status'] for r in result['records']},ensure_ascii=False))
