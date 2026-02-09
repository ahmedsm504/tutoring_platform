# qna/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, F, Exists, OuterRef
from django.views.generic import ListView, DetailView, CreateView
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from .models import (
    PublicQuestion, QuestionAnswer, QuestionCategory, UserVote,
    CommunityAnswer, CommunityAnswerVote, QuestionReport, QuestionSubscription
)
from .forms import PublicQuestionForm, CommunityAnswerForm
import json

class QuestionListView(ListView):
    """عرض قائمة الأسئلة مع كل خيارات التصفية"""
    model = PublicQuestion
    template_name = 'qna/question_list.html'
    context_object_name = 'questions'
    paginate_by = 15
    
    def get_queryset(self):
        """الحصول على قائمة الأسئلة المفلترة"""
        queryset = PublicQuestion.objects.filter(status='approved')
        
        # إضافة annotation للتحقق من وجود إجابة رسمية
        queryset = queryset.annotate(
            has_official=Exists(
                QuestionAnswer.objects.filter(question=OuterRef('pk'))
            ),
            has_featured=Exists(
                QuestionAnswer.objects.filter(
                    question=OuterRef('pk'),
                    is_featured=True
                )
            ),
            # إضافة annotation للتحقق من وجود إجابات مجتمعية
            has_community_answers=Exists(
                CommunityAnswer.objects.filter(
                    question=OuterRef('pk'),
                    is_spam=False
                )
            )
        )
        
        # البحث
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(question_text__icontains=search_query) |
                Q(visitor_name__icontains=search_query)
            )
        
        # التصفية بالفئة
        category_slug = self.request.GET.get('category', '').strip()
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # التصفية بالنوع
        filter_type = self.request.GET.get('filter', '').strip()
        if filter_type == 'featured':
            queryset = queryset.filter(has_featured=True)
        elif filter_type == 'unanswered':
            # سؤال بلا إجابة رسمية ولا مجتمعية
            queryset = queryset.filter(has_official=False, has_community_answers=False)
        elif filter_type == 'frequent':
            queryset = queryset.filter(is_frequent=True)
        elif filter_type == 'answered':
            # سؤال لديه إجابة رسمية أو مجتمعية
            queryset = queryset.filter(Q(has_official=True) | Q(has_community_answers=True))
        
        # الترتيب
        sort_by = self.request.GET.get('sort', 'newest')
        if sort_by == 'oldest':
            queryset = queryset.order_by('created_at')
        elif sort_by == 'most_viewed':
            queryset = queryset.order_by('-view_count', '-created_at')
        else:  # newest
            queryset = queryset.order_by('-created_at')
        
        return queryset.select_related('category').prefetch_related('official_answer')
    
    def get_context_data(self, **kwargs):
        """إضافة بيانات إضافية للقالب"""
        context = super().get_context_data(**kwargs)
        
        # الفئات مع عدد الأسئلة
        context['categories'] = QuestionCategory.objects.annotate(
            question_count=Count(
                'publicquestion',
                filter=Q(publicquestion__status='approved')
            )
        ).filter(question_count__gt=0)
        
        # الإحصائيات - تحديث العد الصحيح
        context['total_questions'] = PublicQuestion.objects.filter(
            status='approved'
        ).count()
        
        # عد الأسئلة التي لها إجابة رسمية أو مجتمعية
        context['answered_count'] = PublicQuestion.objects.filter(
            status='approved'
        ).annotate(
            has_official=Exists(
                QuestionAnswer.objects.filter(question=OuterRef('pk'))
            ),
            has_community_answers=Exists(
                CommunityAnswer.objects.filter(
                    question=OuterRef('pk'),
                    is_spam=False
                )
            )
        ).filter(Q(has_official=True) | Q(has_community_answers=True)).count()
        
        # عد الأسئلة المميزة
        context['featured_count'] = PublicQuestion.objects.filter(
            status='approved'
        ).filter(
            Exists(
                QuestionAnswer.objects.filter(
                    question=OuterRef('pk'),
                    is_featured=True
                )
            )
        ).count()
        
        # الحفاظ على معاملات البحث
        context['current_search'] = self.request.GET.get('search', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_filter'] = self.request.GET.get('filter', '')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        
        # إحصاءات إضافية
        context['community_answers_count'] = CommunityAnswer.objects.filter(
            is_spam=False
        ).count()
        
        return context

class QuestionDetailView(DetailView):
    """عرض صفحة سؤال واحدة مع معالجة إضافة الإجابات المجتمعية"""
    model = PublicQuestion
    template_name = 'qna/question_detail.html'
    context_object_name = 'question'
    
    def get_queryset(self):
        """الحصول على الأسئلة المعتمدة فقط"""
        return PublicQuestion.objects.filter(status='approved')
    
    def get_object(self, queryset=None):
        """الحصول على السؤال وزيادة عداد المشاهدات"""
        slug = self.kwargs.get('slug')
        obj = get_object_or_404(PublicQuestion, slug=slug, status='approved')
        
        # زيادة عداد المشاهدات مرة واحدة فقط في GET
        if self.request.method == 'GET':
            PublicQuestion.objects.filter(pk=obj.pk).update(
                view_count=F('view_count') + 1
            )
            obj.refresh_from_db()
        
        return obj
    
    def post(self, request, *args, **kwargs):
        """معالجة إضافة إجابة مجتمعية في نفس الصفحة"""
        self.object = self.get_object()
        
        # إنشاء النموذج مع تمرير المستخدم
        form = CommunityAnswerForm(request.POST, user=request.user)
        
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = self.object
            
            # ربط بالمستخدم المسجل
            if request.user.is_authenticated:
                answer.answered_by = request.user
                answer.visitor_name = ''
                answer.visitor_email = ''
            
            # حفظ IP
            answer.ip_address = self.get_client_ip()
            answer.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            
            # حفظ الإجابة
            answer.save()
            
            # إرسال إشعارات
            self.send_subscription_notifications(self.object, answer)
            
            # رسائل نجاح
            messages.success(
                request,
                '✅ شكراً لإجابتك! تم نشر إجابتك بنجاح.',
                extra_tags='success'
            )
            
            messages.info(
                request,
                '⭐ إجابتك ظاهرة الآن للجميع. قد تحصل على شارة "تم التحقق" من المشرفين إذا كانت إجابتك مفيدة وموثوقة.',
                extra_tags='info'
            )
            
            # إعادة التوجيه لنفس صفحة السؤال مع anchor للإجابات
            return redirect(self.object.get_absolute_url() + '#answers-section')
        
        else:
            # عرض أخطاء النموذج بشكل تفصيلي
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        error_messages.append(error)
                    else:
                        field_label = form.fields[field].label if field in form.fields else field
                        error_messages.append(f"{field_label}: {error}")
            
            messages.error(
                request,
                '❌ عذراً، هناك أخطاء في النموذج:\n' + '\n'.join(error_messages),
                extra_tags='danger'
            )
            
            # إعادة عرض الصفحة مع الأخطاء
            context = self.get_context_data(object=self.object)
            context['form'] = form
            return self.render_to_response(context)
    
    def get_context_data(self, **kwargs):
        """إضافة بيانات إضافية للقالب"""
        context = super().get_context_data(**kwargs)
        
        # إضافة النموذج إذا لم يكن موجود
        if 'form' not in context:
            context['form'] = CommunityAnswerForm(user=self.request.user)
        
        # إجابات المجتمع (غير الرسمية)
        context['community_answers'] = self.object.answers.filter(
            is_spam=False
        ).order_by('-is_verified', '-likes', '-created_at')
        
        # التحقق من وجود إجابة رسمية بطريقة آمنة
        try:
            official_answer = QuestionAnswer.objects.filter(question=self.object).first()
            context['has_official_answer'] = official_answer is not None
            context['official_answer'] = official_answer
        except:
            context['has_official_answer'] = False
            context['official_answer'] = None
        
        # التحقق من الاشتراك
        if self.request.user.is_authenticated:
            context['is_subscribed'] = QuestionSubscription.objects.filter(
                question=self.object,
                user=self.request.user,
                is_active=True
            ).exists()
        else:
            context['is_subscribed'] = False
        
        # أسئلة ذات صلة
        if self.object.category:
            context['related_questions'] = PublicQuestion.objects.filter(
                category=self.object.category,
                status='approved'
            ).exclude(id=self.object.id).select_related('category').prefetch_related('official_answer').order_by('-view_count')[:5]
        else:
            context['related_questions'] = PublicQuestion.objects.filter(
                status='approved'
            ).exclude(id=self.object.id).select_related('category').prefetch_related('official_answer').order_by('-created_at')[:5]
        
        # Schema.org markup
        context['schema_markup'] = self.generate_schema_markup()
        
        # IP المستخدم
        context['user_ip'] = self.get_client_ip()
        
        return context
    
    def get_client_ip(self):
        """الحصول على IP الزائر"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def send_subscription_notifications(self, question, answer):
        """إرسال إشعارات للمشتركين"""
        try:
            subscriptions = QuestionSubscription.objects.filter(
                question=question,
                is_active=True
            )
            
            for subscription in subscriptions:
                email = subscription.user.email if subscription.user else subscription.email
                if email:
                    subject = f'🆕 إجابة جديدة: {question.title[:50]}'
                    message = f"""
إجابة جديدة على السؤال:

{question.title}

الإجابة:
{answer.answer_text[:200]}...

اضغط هنا لقراءة الإجابة الكاملة: {self.request.build_absolute_uri(question.get_absolute_url())}
                    """
                    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=True)
        except Exception as e:
            print(f"Failed to send subscription notifications: {e}")
    
    def generate_schema_markup(self):
        """إنشاء بيانات منظمة لمحركات البحث"""
        from django.utils.html import escape
        
        question = self.object
        schema = {
            "@context": "https://schema.org",
            "@type": "QAPage",
            "mainEntity": {
                "@type": "Question",
                "name": escape(question.title),
                "text": escape(question.question_text),
                "dateCreated": question.created_at.isoformat(),
                "author": {
                    "@type": "Person",
                    "name": escape(question.visitor_name)
                },
                "answerCount": 0,
            }
        }
        
        # إضافة الإجابة الرسمية
        try:
            official_answer = QuestionAnswer.objects.filter(question=question).first()
            if official_answer:
                schema["mainEntity"]["answerCount"] = 1
                schema["mainEntity"]["acceptedAnswer"] = {
                    "@type": "Answer",
                    "text": escape(official_answer.answer_text),
                    "dateCreated": official_answer.answered_at.isoformat(),
                    "author": {
                        "@type": "Person",
                        "name": official_answer.answered_by.get_full_name() or official_answer.answered_by.username
                    },
                    "upvoteCount": official_answer.likes
                }
        except:
            pass
        
        return json.dumps(schema, ensure_ascii=False, indent=2)


class AskQuestionView(CreateView):
    """صفحة طرح سؤال جديد"""
    form_class = PublicQuestionForm
    template_name = 'qna/ask_question.html'
    success_url = reverse_lazy('qna:question_list')
    
    def get_context_data(self, **kwargs):
        """إضافة بيانات إضافية للقالب"""
        context = super().get_context_data(**kwargs)
        
        # إحصائيات
        context['total_questions'] = PublicQuestion.objects.filter(
            status='approved'
        ).count()
        
        context['total_answers'] = QuestionAnswer.objects.count()
        
        # أمثلة على أسئلة جيدة
        context['example_questions'] = PublicQuestion.objects.filter(
            status='approved'
        ).annotate(
            has_official=Exists(
                QuestionAnswer.objects.filter(question=OuterRef('pk'))
            )
        ).filter(has_official=True).order_by('-view_count')[:3]
        
        return context
    
    def form_valid(self, form):
        """معالجة النموذج الصحيح"""
        question = form.save(commit=False)
        
        # حفظ IP و User Agent
        question.ip_address = self.get_client_ip()
        question.user_agent = self.request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # الكشف عن الأسئلة المتكررة
        similar_questions = PublicQuestion.objects.filter(
            Q(title__icontains=question.title[:30]) |
            Q(question_text__icontains=question.question_text[:100])
        ).filter(status__in=['approved', 'pending'])
        
        if similar_questions.count() >= 2:
            question.is_frequent = True
        
        # تعيين الحالة كـ pending
        question.status = 'pending'
        question.save()
        
        # إرسال إشعار للمشرفين
        self.send_admin_notification(question)
        
        # رسائل نجاح واضحة ومفصلة
        messages.success(
            self.request,
            '✅ تم استلام سؤالك بنجاح!',
            extra_tags='success'
        )
        
        messages.info(
            self.request,
            '⏳ سؤالك الآن في قائمة المراجعة. سيتم نشره خلال 24 ساعة بعد التأكد من مطابقته لشروط النشر.',
            extra_tags='info'
        )
        
        if question.visitor_email:
            messages.info(
                self.request,
                f'📧 سنرسل لك إشعاراً على {question.visitor_email} عند نشر السؤال والإجابة عليه.',
                extra_tags='info'
            )
        
        return redirect(self.success_url)
    
    def form_invalid(self, form):
        """معالجة النموذج الخاطئ"""
        messages.error(
            self.request,
            '❌ عذراً، هناك أخطاء في النموذج. الرجاء التحقق من البيانات المدخلة.',
            extra_tags='danger'
        )
        return super().form_invalid(form)
    
    def get_client_ip(self):
        """الحصول على IP الزائر"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip
    
    def send_admin_notification(self, question):
        """إرسال إشعار للمشرفين"""
        try:
            subject = f'📧 سؤال جديد يحتاج مراجعة: {question.title[:50]}'
            message = f"""
سؤال جديد يحتاج مراجعة:

العنوان: {question.title}
من: {question.visitor_name}
البريد: {question.visitor_email or 'غير متوفر'}
الهاتف: {question.visitor_phone or 'غير متوفر'}
الفئة: {question.category.name if question.category else 'غير محدد'}

نص السؤال:
{question.question_text[:300]}...

للمراجعة والموافقة: {self.request.build_absolute_uri('/admin/qna/publicquestion/')}
            """
            
            if hasattr(settings, 'ADMINS') and settings.ADMINS:
                admin_emails = [email for name, email in settings.ADMINS]
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    admin_emails,
                    fail_silently=True,
                )
        except Exception as e:
            print(f"Failed to send admin notification: {e}")


# ============================================
# دوال AJAX للتصويت والتفاعل
# ============================================

@require_POST
def vote_answer(request, answer_id):
    """التصويت على إجابة رسمية"""
    try:
        answer = get_object_or_404(QuestionAnswer, id=answer_id)
        
        # الحصول على IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # التحقق من التصويت المسبق
        vote, created = UserVote.objects.get_or_create(
            answer=answer,
            ip_address=ip
        )
        
        if created:
            answer.likes = F('likes') + 1
            answer.save(update_fields=['likes'])
            answer.refresh_from_db()
            
            return JsonResponse({
                'success': True,
                'likes': answer.likes,
                'message': 'شكراً لتصويتك!'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'لقد صوّت مسبقاً على هذه الإجابة'
            })
    
    except Exception as e:
        print(f"Vote error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ أثناء التصويت'
        }, status=500)


@require_POST
def vote_community_answer(request, answer_id):
    """التصويت على إجابة مجتمعية"""
    try:
        answer = get_object_or_404(CommunityAnswer, id=answer_id, is_spam=False)
        
        # الحصول على IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # التحقق من التصويت المسبق
        vote, created = CommunityAnswerVote.objects.get_or_create(
            answer=answer,
            ip_address=ip
        )
        
        if created:
            answer.likes = F('likes') + 1
            answer.save(update_fields=['likes'])
            answer.refresh_from_db()
            
            return JsonResponse({
                'success': True,
                'likes': answer.likes,
                'message': 'شكراً لتصويتك!'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'لقد صوّت مسبقاً على هذه الإجابة'
            })
    
    except Exception as e:
        print(f"Vote community error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ أثناء التصويت'
        }, status=500)


@login_required
@require_POST
def verify_community_answer(request, answer_id):
    """التحقق من إجابة مجتمعية (للمشرفين)"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'غير مصرح لك بهذا الإجراء'
        }, status=403)
    
    try:
        answer = get_object_or_404(CommunityAnswer, id=answer_id)
        answer.is_verified = not answer.is_verified
        answer.save(update_fields=['is_verified'])
        
        return JsonResponse({
            'success': True,
            'is_verified': answer.is_verified,
            'message': 'تم التحديث بنجاح'
        })
    
    except Exception as e:
        print(f"Verify error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ أثناء التحقق'
        }, status=500)


@login_required
@require_POST
def delete_community_answer(request, answer_id):
    """حذف إجابة مجتمعية (للمشرفين)"""
    if not request.user.is_staff:
        return JsonResponse({
            'success': False,
            'message': 'غير مصرح لك بهذا الإجراء'
        }, status=403)
    
    try:
        answer = get_object_or_404(CommunityAnswer, id=answer_id)
        answer.is_spam = True
        answer.save(update_fields=['is_spam'])
        
        return JsonResponse({
            'success': True,
            'message': 'تم الحذف بنجاح'
        })
    
    except Exception as e:
        print(f"Delete error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ أثناء الحذف'
        }, status=500)


@require_POST
def report_content(request, slug):
    """الإبلاغ عن محتوى"""
    try:
        question = get_object_or_404(PublicQuestion, slug=slug)
        
        report_type = request.POST.get('report_type')
        description = request.POST.get('description', '').strip()
        reporter_email = request.POST.get('reporter_email', '').strip()
        
        if not report_type or not description:
            return JsonResponse({
                'success': False,
                'message': 'الرجاء ملء جميع الحقول المطلوبة'
            })
        
        # IP المبلغ
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        QuestionReport.objects.create(
            question=question,
            report_type=report_type,
            description=description,
            reporter_ip=ip,
            reporter_email=reporter_email
        )
        
        return JsonResponse({
            'success': True,
            'message': 'شكراً لإبلاغك، سنراجع المحتوى في أقرب وقت'
        })
    
    except Exception as e:
        print(f"Report error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ أثناء إرسال البلاغ'
        }, status=500)


@require_POST
def subscribe_to_question(request, slug):
    """الاشتراك في سؤال"""
    try:
        question = get_object_or_404(PublicQuestion, slug=slug)
        
        if request.user.is_authenticated:
            subscription, created = QuestionSubscription.objects.get_or_create(
                question=question,
                user=request.user,
                defaults={'is_active': True}
            )
            
            if not created:
                subscription.is_active = not subscription.is_active
                subscription.save()
            
            return JsonResponse({
                'success': True,
                'is_subscribed': subscription.is_active,
                'message': 'تم الاشتراك بنجاح' if subscription.is_active else 'تم إلغاء الاشتراك'
            })
        
        else:
            email = request.POST.get('email', '').strip()
            if not email:
                return JsonResponse({
                    'success': False,
                    'message': 'الرجاء إدخال البريد الإلكتروني'
                })
            
            subscription, created = QuestionSubscription.objects.get_or_create(
                question=question,
                email=email,
                defaults={'is_active': True}
            )
            
            if not created:
                subscription.is_active = not subscription.is_active
                subscription.save()
            
            return JsonResponse({
                'success': True,
                'is_subscribed': subscription.is_active,
                'message': 'تم الاشتراك بنجاح' if subscription.is_active else 'تم إلغاء الاشتراك'
            })
    
    except Exception as e:
        print(f"Subscribe error: {e}")
        return JsonResponse({
            'success': False,
            'message': 'حدث خطأ أثناء الاشتراك'
        }, status=500)