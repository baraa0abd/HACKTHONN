"""Build a traceable last-night astronomy record for Mosul/Al-Hadbaa."""
import csv,json,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parent
RAW=ROOT/'output/real/mosul_last_night_raw.json';OUT=ROOT/'output/real'
def build():
 d=json.loads(RAW.read_text(encoding='utf-8-sig'));w=d['weather']['hourly'];a=d['air_quality']['hourly'];ai={t:i for i,t in enumerate(a['time'])};hours=[]
 for i,t in enumerate(w['time']):
  if '2026-09-24T19:00'<=t<='2026-09-25T04:00':
   j=ai[t];hours.append({'local_time':t,'cloud_low_pct':w['cloud_cover_low'][i],'cloud_mid_pct':w['cloud_cover_mid'][i],'cloud_high_pct':w['cloud_cover_high'][i],'humidity_pct':w['relative_humidity_2m'][i],'wind_kmh':w['wind_speed_10m'][i],'visibility_m':w['visibility'][i],'aod':a['aerosol_optical_depth'][j],'dust_ug_m3':a['dust'][j],'pm10_ug_m3':a['pm10'][j],'pm2_5_ug_m3':a['pm2_5'][j]})
 analysis=json.loads((OUT/'iraq_nightlights_analysis.json').read_text(encoding='utf-8'));mosul=next(x for x in analysis['district_results'] if x['district']=='Al-Mosul')
 avg=lambda k:statistics.fmean(x[k] for x in hours)
 report={'location':d['location'],'night':{'start':'2026-09-24T19:00:00+03:00','end':'2026-09-25T04:00:00+03:00'},'hourly':hours,'summary':{'mean_low_cloud_pct':avg('cloud_low_pct'),'mean_mid_cloud_pct':avg('cloud_mid_pct'),'mean_high_cloud_pct':avg('cloud_high_pct'),'mean_humidity_pct':avg('humidity_pct'),'mean_wind_kmh':avg('wind_kmh'),'mean_visibility_km':avg('visibility_m')/1000,'mean_aod':avg('aod'),'mean_dust_ug_m3':avg('dust_ug_m3'),'weather_assessment_ar':'جو صاف وجاف وغبار منخفض؛ الرؤية الجوية جيدة','astronomy_assessment_ar':'القمر شديد السطوع خفّض جودة رصد المجرات والسدم والأجرام الخافتة'},'astronomy':{'sunset_local':'18:01','astronomical_night_start_local':'19:27','moon_phase':'Waxing gibbous','moon_illumination_pct':96.0,'moonrise_local':'16:49','moon_upper_transit_local':'22:32','moon_transit_altitude_deg':45.4,'moonset_local':'03:21','planet_notes':{'Saturn':'مرئي جيداً طوال الليل تقريباً؛ عبور 00:41','Uranus':'يشرق 20:59؛ يحتاج أداة بصرية','Neptune':'متاح لكن صعب نسبياً؛ عبور 00:06','Mars':'يشرق 00:44','Jupiter':'يشرق 02:28'}},'light_pollution_context':{'district':'Al-Mosul','latest_year':mosul['latest_year'],'annual_adm2_radiance_nw_cm2_sr':mosul['latest_radiance'],'meaning_ar':'سياق سنوي مجمع للقضاء، وليس قياساً لليلة 24 سبتمبر ولا SQM أرضياً'},'sources':{'weather':'https://api.open-meteo.com/v1/forecast','air_quality':'https://air-quality-api.open-meteo.com/v1/air-quality','astronomy':'https://www.timeanddate.com/astronomy/iraq/mosul','moon_month':'https://www.timeanddate.com/moon/iraq/mosul?month=9','black_marble_context':'data/real/worldbank_iraq_annual.json derived from NASA Black Marble','nasa_black_marble':'https://www.earthdata.nasa.gov/data/projects/black-marble','worldview':'https://worldview.earthdata.nasa.gov/','globe_at_night':'https://globeatnight.org/'},'data_limits':['لم يثبت وجود قراءة Globe at Night أو SQM ميدانية في الحدباء لهذه الليلة','Worldview واجهة عرض؛ لم تُستخرج قيمة بكسل يومية للحدباء','قيمة Black Marble المعروضة سنوية ومجمعة إدارياً','الطقس وجودة الهواء مخرجات نماذج وليست محطة أرضية في الحي']}
 (OUT/'mosul_al_hadbaa_2026-09-24.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 with (OUT/'mosul_al_hadbaa_2026-09-24_hourly.csv').open('w',encoding='utf-8-sig',newline='') as f:
  wr=csv.DictWriter(f,fieldnames=hours[0]);wr.writeheader();wr.writerows(hours)
 return report
if __name__=='__main__':print(json.dumps(build()['summary'],ensure_ascii=False,indent=2))
