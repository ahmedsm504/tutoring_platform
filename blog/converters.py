# أنشئ هذا الملف في: blog/converters.py

class UnicodeSlugConverter:
    """
    Converter يدعم الحروف العربية والـ Unicode في الـ URLs
    """
    regex = r'[\w\-]+'
    
    def to_python(self, value):
        return value
    
    def to_url(self, value):
        return value