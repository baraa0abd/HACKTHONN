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
    (destination / "challenge1_tests.json").write_text(json.dumps(ch1, indent=2), encoding="utf-8")
    from data_loader import dashboard_data
    data = dashboard_data(); c1=data["challenges"]["challenge1"]["data"];backtest=c1["backtest"]
    guide=f"""# دليل تقديم «ليل» — التحدي الأول

تم توليد هذا الدليل من الملفات المتحقق منها حالياً. شغّل `run_dashboard.ps1` ثم افتح العنوان المحلي الظاهر.

## 1. النظرة العامة

اعرض الدليل الأساسي: **{data['overview']['tests_passed']}/{data['overview']['tests_run']} اختباراً ناجحاً** و**{data['overview']['real_inputs_processed']:,} سجلاً وعينة حقيقية**. وضّح أن اللوحة تعيد قراءة الملفات المحلية عند التحديث وتعرض خطأ واضحاً عند فقدان أي ملف مطلوب.

## 2. البيانات الحقيقية

تحتوي بيانات World Bank وNASA الحقيقية على **{c1['analysis']['records']:,} سجل منطقة وسنة** يغطي **{c1['analysis']['districts']} منطقة عراقية** من **{c1['analysis']['years'][0]} إلى {c1['analysis']['years'][-1]}**. اضغط علامة «المصدر» لإظهار ملف التحليل وتاريخ الاسترجاع.

اعرض الاتجاه الوطني، ثم فحص المناطق المظلمة، ثم قائمة الزيادة السريعة. أكّد أن النتائج مؤشرات لفحص الإشعاع المتجه إلى الأعلى، وأن الموقع المرشح يحتاج تحققاً ميدانياً من الوصول والأفق والطقس والأمان وقياسات SQM المعايرة.

## 3. إثبات التحسن

اعرض اختبار **{backtest['recommended']['nights']} ليلة**: نجاح التوصيات **{backtest['recommended']['successful_night_rate']:.1%}**، والرحلات المهدرة **{backtest['recommended']['wasted_trip_rate']:.1%}**، وكسب الدرجة مقابل نقطة الأصل **{backtest['decision_gain_vs_origin']:.3f}**.

## 4. القرار الحي

اختر 100 كم وسبعة أيام واضغط «احسب القرار الحي». اعرض ترتيب المواقع ووقت الرصد والقرار وأهم القيود. وضّح أن الظروف تأتي من Open-Meteo وأن درجة الضوء مشتقة من أحدث إشعاع Black Marble في نينوى.

## 5. الخاتمة

SQM وBortle وNELM محجوبة حتى تتوفر معايرة أرضية؛ النظام لا يختلق قياسات غير موجودة.
"""
    (ROOT / "dashboard" / "PRESENTING.md").write_text(guide, encoding="utf-8")
    print(f"Challenge 1: {ch1['passed']}/{ch1['run']}")
    return 0 if ok1 else 1


if __name__ == "__main__": sys.exit(main())
