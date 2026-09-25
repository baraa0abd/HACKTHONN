"""Transparent observation-decision engine using live Open-Meteo data."""
from __future__ import annotations
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import json, math, time, subprocess, tempfile
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parent; CACHE=ROOT/'data'/'cache'; CACHE.mkdir(parents=True,exist_ok=True)
SITES=[
 {'id':'mosul','name_ar':'الموصل (الخيار الساذج)','lat':36.34,'lon':43.13,'district':'Al-Mosul'},
 {'id':'bashiqa','name_ar':'بعشيقة','lat':36.45,'lon':43.35,'district':'Al-Hamdaniya'},
 {'id':'alqosh','name_ar':'ألقوش','lat':36.73,'lon':43.10,'district':'Tilkaef'},
 {'id':'hammam','name_ar':'حمام العليل','lat':36.16,'lon':43.26,'district':'Al-Mosul'},
 {'id':'hatra','name_ar':'الحضر','lat':35.59,'lon':42.72,'district':'Al-Hatra'},
]

def sqm_to_nelm(sqm): return 7.93-5*math.log10(10**(4.316-(sqm/5))+1)
def sqm_to_bortle(s):
    return 1 if s>=21.7 else 2 if s>=21.3 else 3 if s>=20.4 else 4 if s>=19.1 else 5 if s>=18.0 else 6 if s>=17.0 else 7 if s>=16 else 8 if s>=15 else 9
def status(score): return 'GO' if score>=.72 else 'MARGINAL' if score>=.48 else 'NO-GO'
def haversine(a,b):
    lat1,lon1,lat2,lon2=map(math.radians,(a[0],a[1],b[0],b[1]));dlat=lat2-lat1;dlon=lon2-lon1
    return 6371*2*math.asin(math.sqrt(math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2))
def _site_layer():
    data=json.loads((ROOT/'output'/'real'/'iraq_nightlights_analysis.json').read_text(encoding='utf-8'))
    ninewa={x['district']:x['latest_radiance'] for x in data['district_results'] if x['governorate']=='Ninewa'}
    logs=[math.log1p(x) for x in ninewa.values()];lo,hi=min(logs),max(logs)
    # Keep a non-zero floor: even the brightest district can have usable hours;
    # the normalized Black Marble contrast supplies the remaining 75%.
    return [{**x,'radiance':ninewa[x['district']], 'static':.25+.75*(1-(math.log1p(ninewa[x['district']])-lo)/(hi-lo))} for x in SITES]
def _fetch(base,params,key):
    path=CACHE/f'{key}.json'
    if path.exists() and time.time()-path.stat().st_mtime<3600:return json.loads(path.read_text(encoding='utf-8'))
    url=base+'?'+urlencode(params)
    try:
        with urlopen(url,timeout=15) as r:data=json.load(r)
    except Exception:
        # Some managed Windows environments block Python sockets while allowing
        # the system TLS client. Arguments are passed without a shell.
        with tempfile.NamedTemporaryFile(suffix='.json',delete=False) as tmp: tmp_path=Path(tmp.name)
        try:
            subprocess.run(['curl.exe','-sS','--fail','--max-time','20',url,'-o',str(tmp_path)],check=True)
            data=json.loads(tmp_path.read_text(encoding='utf-8'))
        finally:
            tmp_path.unlink(missing_ok=True)
    path.write_text(json.dumps(data),encoding='utf-8');return data
def _weather(site,days):
    common={'latitude':site['lat'],'longitude':site['lon'],'timezone':'Asia/Baghdad','forecast_days':days}
    w=_fetch('https://api.open-meteo.com/v1/forecast',{**common,'hourly':'cloud_cover_low,cloud_cover_mid,cloud_cover_high,relative_humidity_2m,wind_speed_10m'},f"w_{site['id']}_{days}")
    q=_fetch('https://air-quality-api.open-meteo.com/v1/air-quality',{**common,'hourly':'aerosol_optical_depth,dust'},f"q_{site['id']}_{days}")
    qi={t:i for i,t in enumerate(q['hourly']['time'])}; out=[]
    now_local=datetime.now(ZoneInfo('Asia/Baghdad')).replace(minute=0,second=0,microsecond=0)
    for i,t in enumerate(w['hourly']['time']):
        local_time=datetime.fromisoformat(t).replace(tzinfo=ZoneInfo('Asia/Baghdad'))
        hour=local_time.hour;j=qi.get(t)
        if local_time<now_local or j is None or not (18<=hour or hour<=5):continue
        vals={k:w['hourly'][k][i] for k in ('cloud_cover_low','cloud_cover_mid','cloud_cover_high','relative_humidity_2m','wind_speed_10m')}
        vals.update(aerosol_optical_depth=q['hourly']['aerosol_optical_depth'][j],dust=q['hourly']['dust'][j])
        if any(v is None for v in vals.values()):continue
        cloud=max(vals['cloud_cover_low'],.7*vals['cloud_cover_mid'],.4*vals['cloud_cover_high'])/100
        penalties={'السحب':cloud,'الغبار والهباء':min(1,vals['aerosol_optical_depth']/1.2+vals['dust']/1000),'الرطوبة':max(0,(vals['relative_humidity_2m']-45)/55),'الرياح':min(1,vals['wind_speed_10m']/45)}
        night=1-(.45*penalties['السحب']+.25*penalties['الغبار والهباء']+.15*penalties['الرطوبة']+.15*penalties['الرياح'])
        score=site['static']*max(0,night)
        out.append({'time':t,'score':round(score,3),'status':status(score),'conditions':vals,'reasons':[k for k,v in sorted(penalties.items(),key=lambda x:x[1],reverse=True)[:3]]})
    return out
def _night_outlook(site,days):
    """P(clear night) per upcoming night from the model trained on real forecast-vs-ERA5 nights (train_sky_model.py)."""
    from datetime import date as _date, timedelta as _td
    import pandas as pd
    from build_sky_dataset import NIGHT_HOURS, night_features
    import train_sky_model
    from train_sky_model import clear_probability
    h=_fetch('https://api.open-meteo.com/v1/forecast',{'latitude':site['lat'],'longitude':site['lon'],'timezone':'Asia/Baghdad','forecast_days':min(days+1,16),
             'hourly':'cloud_cover,relative_humidity_2m,wind_speed_10m,precipitation'},f"n_{site['id']}_{days}")['hourly']
    idx={t:i for i,t in enumerate(h['time'])};rows=[];dates=[]
    for k in range(days):
        d=datetime.now(ZoneInfo('Asia/Baghdad')).date()+_td(days=k)
        hrs=[f"{(d if x>=19 else d+_td(days=1)).isoformat()}T{x:02d}:00" for x in NIGHT_HOURS]
        if any(t not in idx for t in hrs):continue
        col=lambda v:[h[v][idx[t]] for t in hrs]
        vals=[col(v) for v in ('cloud_cover','relative_humidity_2m','wind_speed_10m','precipitation')]
        if any(x is None for c in vals for x in c):continue
        rows.append(night_features(d,*vals,site['static']));dates.append(d.isoformat())
    if not rows:return []
    p=clear_probability(pd.DataFrame(rows));go=train_sky_model._bundle['go_threshold']
    return [{'night':d,'p_clear':round(float(x),3),'go':bool(x>=go)} for d,x in zip(dates,p)]
def recommend(origin=(36.34,43.13),max_travel_km=100,days=7,mode='naked_eye'):
    sites=[]
    for raw in _site_layer():
        site={**raw,'distance_km':round(haversine(origin,(raw['lat'],raw['lon'])),1)}
        if site['distance_km']>max_travel_km:continue
        hours=_weather(site,days)
        if not hours:continue
        best=max(hours,key=lambda x:x['score'])
        try:nights=_night_outlook(site,days)
        except Exception as exc:nights=[];print('clear-sky model unavailable:',exc)
        sites.append({**site,'best':best,'nights':nights,'sqm_status':'غير متاح: يحتاج معايرة SQM أرضية','hours':hours})
    sites.sort(key=lambda x:x['best']['score'],reverse=True)
    base=next((x for x in sites if x['id']=='mosul'),None)
    for x in sites:x['decision_gain_vs_origin']=round(x['best']['score']-(base['best']['score'] if base else 0),3)
    return {'generated_utc':datetime.now(timezone.utc).isoformat(),'input':{'origin':origin,'max_travel_km':max_travel_km,'days':days,'mode':mode},'sites':sites[:5],'source':'Open-Meteo live forecast + latest Ninewa Black Marble ADM2 radiance + clear-night model trained on 4,805 real forecast-vs-ERA5 nights','limitations':['لا توجد معايرة SQM عراقية بعد','الإشعاع مجمع على مستوى القضاء','السلامة والوصول غير مقيمين']}
