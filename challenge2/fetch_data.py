"""Fetch public BIRDS research inputs; never generate replacement telemetry."""
import concurrent.futures
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request

ROOT=Path(__file__).resolve().parent
REPO='BIRDSOpenSource/EPS_dataset'
FILES=['NEPALISAT.xlsx','RAAVANA.xlsx','TSURU.xlsx','UGUISU.xlsx','README.md','LICENSE',
       'On-orbit electrical power system dataset of 1U CubeSat constellation.pdf']


def download(url):
    request=urllib.request.Request(url,headers={'User-Agent':'OrbitBench/2.0 research downloader'})
    with urllib.request.urlopen(request,timeout=60) as response:
        return response.read()


def main():
    out=ROOT/'data'/'birds';out.mkdir(parents=True,exist_ok=True)
    commit=json.loads(download(f'https://api.github.com/repos/{REPO}/commits/main'))['sha']
    def fetch(name):
        url=f'https://raw.githubusercontent.com/{REPO}/{commit}/{urllib.parse.quote(name)}'
        content=download(url)
        if name.endswith('.xlsx') and not content.startswith(b'PK'):
            raise ValueError(f'{name}: expected XLSX ZIP, not a Git LFS pointer or error page')
        path=out/name
        path.write_bytes(content)
        return {'file':name,'url':url,'sha256':hashlib.sha256(content).hexdigest(),'bytes':len(content)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        records=list(pool.map(fetch,FILES))
    manifest={'repository':f'https://github.com/{REPO}','commit':commit,
              'retrieved_utc':datetime.now(timezone.utc).isoformat(),
              'evidence':'public on-orbit telemetry published by dataset authors',
              'files':records}
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(json.dumps(manifest,indent=2))


if __name__=='__main__':
    main()
