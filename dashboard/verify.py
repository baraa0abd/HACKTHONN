"""Run verification tests only and save their real results for the read-only dashboard."""
import io
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def run_suite(test_dir, pattern="test*.py"):
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(test_dir), pattern=pattern)
    outcome = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    summary = {"run": outcome.testsRun,
               "passed": outcome.testsRun-len(outcome.failures)-len(outcome.errors)-len(outcome.skipped),
               "failures": len(outcome.failures), "errors": len(outcome.errors), "skipped": len(outcome.skipped),
               "log": stream.getvalue()}
    return summary, outcome.wasSuccessful()


def main():
    destination = ROOT / "dashboard" / "verified"; destination.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(ROOT))
    ch1, ok1 = run_suite(ROOT / "tests")
    # Challenge 2 modules use direct imports, so make its root importable for discovery.
    sys.path.insert(0, str(ROOT / "challenge2"))
    ch2, ok2 = run_suite(ROOT / "challenge2" / "tests")
    (destination / "challenge1_tests.json").write_text(json.dumps(ch1, indent=2), encoding="utf-8")
    (destination / "challenge2_tests.json").write_text(json.dumps(ch2, indent=2), encoding="utf-8")
    from data_loader import dashboard_data
    data = dashboard_data(); c1=data["challenges"]["challenge1"]["data"];c2=data["challenges"]["challenge2"]["data"]
    flags=c2["flagged_passes"];design=c2["design"]
    guide=f"""# دليل تقديم لوحة ASI الموحدة

تم توليد هذا الدليل من الملفات المتحقق منها حالياً. شغّل `run_dashboard.ps1` ثم افتح العنوان المحلي الظاهر.

## 1. النظرة العامة

اعرض الدليل الأساسي: **{data['overview']['tests_passed']}/{data['overview']['tests_run']} اختباراً ناجحاً** و**{data['overview']['real_inputs_processed']:,} سجلاً وعينة حقيقية**. وضّح أن اللوحة تعيد قراءة الملفات المحلية عند التحديث وتعرض خطأ واضحاً عند فقدان أي ملف مطلوب.

## 2. التحدي الأول — ليل

تحتوي بيانات World Bank وNASA الحقيقية على **{c1['analysis']['records']:,} سجل منطقة وسنة** يغطي **{c1['analysis']['districts']} منطقة عراقية** من **{c1['analysis']['years'][0]} إلى {c1['analysis']['years'][-1]}**. اضغط علامة «المصدر» لإظهار ملف التحليل وتاريخ الاسترجاع.

اعرض الاتجاه الوطني، ثم فحص المناطق المظلمة، ثم قائمة الزيادة السريعة. أكّد أن النتائج مؤشرات لفحص الإشعاع المتجه إلى الأعلى، وأن الموقع المرشح يحتاج تحققاً ميدانياً من الوصول والأفق والطقس والأمان وقياسات SQM المعايرة.

## 3. التحدي الثاني — أوربت بنش

يغطي الدليل الأساسي **{len(c2['analysis']['satellites'])} أقمار CubeSat** و**{len(c2['analysis']['passes'])} ملف قياس** و**{c2['accepted_samples']:,} عينة مقبولة**، مع رفض **{c2['rejected_rows']:,} صفاً غير مكتمل**. اعرض جدول الأقمار وملفات القياس المعلّمة البالغ عددها **{len(flags)}**، ثم افتح المصدر لإظهار نسخة BIRDS المثبتة.

اعرض أداة التصميم أخيراً: حللت **{design.get('simulation_count','غير متاح')} حالة** وحفظت مرشح دورة تشغيل **{design.get('candidate_duty',0):.0%}** بأقل فائض محسوب **{design.get('worst_net_wh_per_orbit',0):.4f} واط·ساعة/مدار**. هذه أداة تحليل ثانوية ولا تثبت الجاهزية للطيران أو مستوى TRL معتمداً.

## 4. الخاتمة

ارجع إلى النظرة العامة. يوفر النظامان أدلة فحص وهندسة قابلة للتتبع من بيانات خارجية حقيقية. التحقق الميداني بـSQM واختبار العتاد ضمن الحلقة هما المرحلتان التاليتان.
"""
    (ROOT / "dashboard" / "PRESENTING.md").write_text(guide, encoding="utf-8")
    print(f"Challenge 1: {ch1['passed']}/{ch1['run']}; Challenge 2: {ch2['passed']}/{ch2['run']}")
    return 0 if ok1 and ok2 else 1


if __name__ == "__main__": sys.exit(main())
