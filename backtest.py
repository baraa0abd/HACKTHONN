"""Twelve-month ERA5 backtest for Layl versus transparent naive baselines."""
from collections import defaultdict
from datetime import date,timedelta
import json,math
from decision_engine import ROOT,CACHE,_fetch,_site_layer,haversine,status

END=date.today()-timedelta(days=7); START=END-timedelta(days=364); ORIGIN=(36.34,43.13)
def weather(site):
    p={'latitude':site['lat'],'longitude':site['lon'],'start_date':START.isoformat(),'end_date':END.isoformat(),'timezone':'Asia/Baghdad','hourly':'cloud_cover_low,cloud_cover_mid,cloud_cover_high,relative_humidity_2m,wind_speed_10m'}
    return _fetch('https://archive-api.open-meteo.com/v1/archive',p,f"history_{site['id']}_{START}_{END}")['hourly']
def nightly(site):
    h=weather(site);days=defaultdict(list)
    for i,t in enumerate(h['time']):
        hr=int(t[11:13]);vals=[h[k][i] for k in ('cloud_cover_low','cloud_cover_mid','cloud_cover_high','relative_humidity_2m','wind_speed_10m')]
        if any(v is None for v in vals) or not (hr>=19 or hr<=4):continue
        lo,mid,hi,rh,wind=vals;cloud=max(lo,.7*mid,.4*hi)/100
        night=1-(.60*cloud+.20*max(0,(rh-45)/55)+.20*min(1,wind/45))
        score=site['static']*max(0,night);days[t[:10]].append((score,t))
    return {d:max(v) for d,v in days.items()}
def run():
    sites=[]
    for x in _site_layer():sites.append({**x,'distance_km':haversine(ORIGIN,(x['lat'],x['lon']))})
    series={s['id']:nightly(s) for s in sites};dates=sorted(set.intersection(*(set(v) for v in series.values())))
    origin=next(s for s in sites if s['id']=='mosul');nearest=min((s for s in sites if s['id']!='mosul'),key=lambda x:x['distance_km'])
    recommended=[]
    for d in dates:
        best=max(sites,key=lambda s:series[s['id']][d][0]);recommended.append((d,best,series[best['id']][d][0]))
    def metrics(choices):
        vals=[x[2] for x in choices];return {'nights':len(vals),'mean_score':sum(vals)/len(vals),'successful_night_rate':sum(v>=.72 for v in vals)/len(vals),'wasted_trip_rate':sum(v<.48 for v in vals)/len(vals)}
    base_origin=[(d,origin,series['mosul'][d][0]) for d in dates];base_near=[(d,nearest,series[nearest['id']][d][0]) for d in dates]
    result={'period':[START.isoformat(),END.isoformat()],'source':'Open-Meteo Historical Weather API (ERA5); latest repository Black Marble ADM2 layer','recommended':metrics(recommended),'naive_origin':metrics(base_origin),'naive_nearest':metrics(base_near),'decision_gain_vs_origin':sum(x[2]-y[2] for x,y in zip(recommended,base_origin))/len(dates),'decision_gain_vs_nearest':sum(x[2]-y[2] for x,y in zip(recommended,base_near))/len(dates),'limitations':['Historical AOD was unavailable in this backtest and is omitted','Static light layer uses latest year for all nights','Straight-line candidate radius; no road routing']}
    out=ROOT/'output'/'real'/'backtest_summary.json';out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8');return result
if __name__=='__main__':print(json.dumps(run(),ensure_ascii=False,indent=2))
