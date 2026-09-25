# لوحة ASI الموحدة للبيانات الحقيقية

اللوحة طبقة عرض للملفات الحقيقية الموجودة للتحديين، ولا تجلب مجموعات البيانات أو تعيد توليدها أو أخذ عينات منها أو حسابها من جديد.

## التشغيل

```powershell
cd C:\Users\liqaa\Desktop\HACKTHON\dashboard
.\run_dashboard.ps1
```

افتح العنوان `http://127.0.0.1:8902`. يشغّل الأمر اختبارات التحديين، ويحفظ نتائج التحقق الفعلية، ويعيد توليد دليل `PRESENTING.md` من الملفات الحالية، ثم يبدأ الخادم المحلي.

## تحديث البيانات الأصلية

التحدي الأول:

```powershell
cd C:\Users\liqaa\Desktop\HACKTHON
python fetch_challenge1_data.py
.\run_demo.ps1
```

التحدي الثاني:

```powershell
cd C:\Users\liqaa\Desktop\HACKTHON\challenge2
python fetch_data.py
.\run_demo.ps1
```

تحتاج أوامر جلب البيانات إلى الإنترنت. تعمل لوحة المعلومات دون اتصال بعد توفر المخرجات المتحقق منها.




