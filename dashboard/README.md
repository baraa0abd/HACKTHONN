# ليل — لوحة التحدي الأول

اللوحة مخصصة للتحدي الأول فقط. تعرض بيانات Black Marble الحقيقية، اختباراً رجعياً لـ365 ليلة، وتوصيات حية من Open-Meteo.

## التشغيل

```powershell
cd C:\Users\liqaa\Desktop\HACKTHON\dashboard
.\run_dashboard.ps1
```

افتح العنوان `http://127.0.0.1:8903`. يشغّل الأمر اختبارات التحدي الأول ويحفظ نتائجها ثم يبدأ الخادم المحلي.

## تحديث البيانات الأصلية

```powershell
cd C:\Users\liqaa\Desktop\HACKTHON
python fetch_challenge1_data.py
.\run_demo.ps1
```

تحتاج أوامر جلب البيانات إلى الإنترنت. تعمل لوحة المعلومات دون اتصال بعد توفر المخرجات المتحقق منها.





