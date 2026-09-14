import urllib.request
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from core.models import CurriculumDocument

# مصدر المصحف: مجمع الملك فهد لطباعة المصحف الشريف (نسخة نصية عالية الجودة)
QURAN_PDF_URL = 'https://www.quran-pdf.com/arabic-quran.pdf'


class Command(BaseCommand):
    """
    أمر لمرة واحدة: بينزّل نسخة إلكترونية من المصحف الشريف (مصدرها مجمع الملك
    فهد لطباعة المصحف الشريف) ويحفظها كملف منهج بعلامة "هل هو المصحف؟" مفعّلة،
    عشان تظهر مباشرة في بورتال المعلمة (المنهج + السبورة التفاعلية) من غير
    ما تحتاجي ترفعيه يدويًا من لوحة الأدمن.

    الاستخدام:
        python manage.py seed_quran_pdf

    ملحوظة: محتاج السيرفر يكون عنده اتصال بالإنترنت وقت تشغيل الأمر (على
    عكس بيئة تطوير Claude اللي معزولة عن الإنترنت). لو الرابط اتغير أو
    اتقفل مستقبلًا، ارفعي أي ملف PDF للمصحف بنفسك من لوحة الأدمن (ملفات
    المنهج) وفعّلي عليه "هل هو المصحف؟" بدل ما تشغلي الأمر ده.
    """
    help = 'ينزّل نسخة من المصحف الشريف من مجمع الملك فهد ويضيفها كملف منهج (المصحف)'

    def handle(self, *args, **options):
        if CurriculumDocument.objects.filter(is_quran=True, is_active=True).exists():
            self.stdout.write(self.style.WARNING('فيه مصحف مفعّل بالفعل في ملفات المنهج - الأمر متوقف عشان ميتكررش.'))
            return

        self.stdout.write('بنزّل المصحف من: ' + QURAN_PDF_URL + ' ... (ملف كبير، ممكن ياخد شوية دقايق)')
        try:
            req = urllib.request.Request(QURAN_PDF_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=180) as response:
                data = response.read()
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'مقدرتش أنزّل الملف: {e}'))
            self.stderr.write('ارفعي ملف المصحف يدويًا من لوحة الأدمن (ملفات المنهج) وفعّلي عليه "هل هو المصحف؟".')
            return

        if len(data) < 1024 * 1024:  # أقل من 1 ميجا يبقى غالبًا مش الملف الصحيح
            self.stderr.write(self.style.ERROR('الملف اللي اتنزل صغير جدًا وغالبًا مش المصحف الصحيح - راجعي الرابط.'))
            return

        doc = CurriculumDocument.objects.create(title='المصحف الشريف', is_quran=True, is_active=True, order=0)
        doc.file.save('quran.pdf', ContentFile(data))
        self.stdout.write(self.style.SUCCESS(f'تم! المصحف اتضاف بنجاح ({len(data) // (1024*1024)} ميجا) وهيظهر دلوقتي في بورتال المعلمة.'))
