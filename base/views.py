from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Count, Sum, Avg
from .models import *
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.core.paginator import Paginator


@login_required
def dashboard(request):
    # Beneficiary statistics
    total_beneficiaries = Beneficiary.objects.filter(is_active=True).count()
    beneficiaries_by_level = Beneficiary.objects.filter(is_active=True).values('current_level').annotate(count=Count('id'))
    beneficiaries_by_gender = Beneficiary.objects.filter(is_active=True).values('gender').annotate(count=Count('id'))
    
    # Institution statistics
    total_institutions = Institution.objects.filter(is_active=True).count()
    institutions_by_type = Institution.objects.filter(is_active=True).values('institution_type').annotate(count=Count('id'))
    
    # Payment statistics
    total_payments = Payment.objects.filter(
        payment_date__year=datetime.now().year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Performance statistics
    graduation_rate = 92  # This would be calculated from your data
    
    # Recent activities
    recent_activities = ActivityLog.objects.all().order_by('-date_recorded')[:5]
    
    # Upcoming events
    upcoming_events = Event.objects.filter(
        start_date__gte=datetime.now(),
        is_active=True
    ).order_by('start_date')[:3]
    
    # Unread notifications for the user
    unread_notifications = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()
    
    context = {
        'total_beneficiaries': total_beneficiaries,
        'beneficiaries_by_level': list(beneficiaries_by_level),
        'beneficiaries_by_gender': list(beneficiaries_by_gender),
        'total_institutions': total_institutions,
        'institutions_by_type': list(institutions_by_type),
        'total_payments': total_payments,
        'graduation_rate': graduation_rate,
        'recent_activities': recent_activities,
        'upcoming_events': upcoming_events,
        'unread_notifications': unread_notifications,
        'user': request.user,  # Changed from User to request.user
    }
    
    return render(request, 'dashboard.html', context)


def get_beneficiary_distribution(request):
    # This would be called via AJAX for the chart data
    level_data = Beneficiary.objects.filter(is_active=True).values('current_level').annotate(count=Count('id'))
    gender_data = Beneficiary.objects.filter(is_active=True).values('gender').annotate(count=Count('id'))
    
    return JsonResponse({
        'level_data': list(level_data),
        'gender_data': list(gender_data),
    })

def get_performance_trends(request):
    # This would be called via AJAX for the chart data
    term = request.GET.get('term', '1')
    performance_data = AcademicPerformance.objects.filter(term=term).values('academic_year').annotate(
        avg_score=Avg('average_score')
    ).order_by('academic_year')
    
    return JsonResponse({
        'performance_data': list(performance_data),
    })



def login_view(request):
    if request.method == "POST":
        username = request.POST.get('email')  # Using email as username
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)  # Always call login() to set up the session        
            messages.success(request, 'Login successful')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password')

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been Logged out successfully')
    return redirect('login_view')

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Beneficiary, Institution, Sponsor


@login_required
def beneficiaries_list(request):
    # Get filter parameters
    education_level = request.GET.get('education_level')
    status_filter = request.GET.get('status')
    year = request.GET.get('year')
    sponsor_id = request.GET.get('sponsor')
    search_query = request.GET.get('search', '')

    # Start with all active beneficiaries
    beneficiaries = Beneficiary.objects.filter(is_active=True).select_related('institution', 'sponsor')

    # Apply filters
    if education_level:
        beneficiaries = beneficiaries.filter(current_level=education_level)
    
    if status_filter:
        if status_filter == 'active':
            beneficiaries = beneficiaries.filter(is_active=True, current_level__ne='graduated')
        elif status_filter == 'inactive':
            beneficiaries = beneficiaries.filter(is_active=False)
        elif status_filter == 'pending':
            beneficiaries = beneficiaries.filter(is_active=True, status='pending')
        elif status_filter == 'graduated':
            beneficiaries = beneficiaries.filter(current_level='graduated')

    if year:
        beneficiaries = beneficiaries.filter(enrollment_date__year=year)

    if sponsor_id:
        beneficiaries = beneficiaries.filter(sponsor__id=sponsor_id)

    if search_query:
        beneficiaries = beneficiaries.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(national_id__icontains=search_query)
        )

    # Get distinct enrollment years for filter dropdown
    enrollment_years = Beneficiary.objects.dates('enrollment_date', 'year').order_by('-enrollment_date')

    # Pagination
    paginator = Paginator(beneficiaries, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'beneficiaries': page_obj,
        'education_levels': Beneficiary.LEVEL_CHOICES,
        'enrollment_years': [date.year for date in enrollment_years],
        'sponsors': Sponsor.objects.all(),
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        'is_paginated': paginator.num_pages > 1,
    }

    return render(request, 'benef.html', context)

# views.py
# views.py
@login_required
def add_beneficiary(request):
    if request.method == 'POST':
        # Get all form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')
        national_id = request.POST.get('national_id')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        current_level = request.POST.get('current_level')
        institution_id = request.POST.get('institution')
        enrollment_date = request.POST.get('enrollment_date')
        sponsor_id = request.POST.get('sponsor')
        photo = request.FILES.get('photo')
        
        # Validate required fields
        errors = {}
        if not first_name:
            errors['first_name'] = 'First name is required'
        if not last_name:
            errors['last_name'] = 'Last name is required'
        if not date_of_birth:
            errors['date_of_birth'] = 'Date of birth is required'
        if not gender:
            errors['gender'] = 'Gender is required'
        if not current_level:
            errors['current_level'] = 'Education level is required'
        if not enrollment_date:
            errors['enrollment_date'] = 'Enrollment date is required'
            
        if errors:
            # Get all institutions and sponsors for the form
            institutions = Institution.objects.all()
            sponsors = Sponsor.objects.all()
            
            context = {
                'errors': errors,
                'institutions': institutions,
                'sponsors': sponsors,
                'education_levels': Beneficiary.LEVEL_CHOICES,
                'genders': Beneficiary.GENDER_CHOICES,
                'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
                'form_data': request.POST  # To repopulate form
            }
            return render(request, 'beneficiary_add.html', context)
        
        try:
            # Create the beneficiary
            beneficiary = Beneficiary(
                first_name=first_name,
                last_name=last_name,
                gender=gender,
                date_of_birth=date_of_birth,
                national_id=national_id,
                phone_number=phone_number,
                email=email,
                current_level=current_level,
                institution_id=institution_id,
                enrollment_date=enrollment_date,
                sponsor_id=sponsor_id,
                is_active=True
            )
            
            if photo:
                beneficiary.photo = photo
                
            beneficiary.save()
            
            messages.success(request, 'Beneficiary added successfully!')
            return redirect('beneficiary_detail', pk=beneficiary.pk)
            
        except Exception as e:
            messages.error(request, f'Error saving beneficiary: {str(e)}')
            return redirect('add_beneficiary')
    
    else:
        # GET request - show empty form
        institutions = Institution.objects.all()
        sponsors = Sponsor.objects.all()
        
        context = {
            'institutions': institutions,
            'sponsors': sponsors,
            'education_levels': Beneficiary.LEVEL_CHOICES,
            'genders': Beneficiary.GENDER_CHOICES,
            'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count()
        }
        return render(request, 'beneficiary_add.html', context)

@login_required
def beneficiary_detail(request, pk):
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    payments = Payment.objects.filter(beneficiary=beneficiary).order_by('-payment_date')
    performances = AcademicPerformance.objects.filter(beneficiary=beneficiary).order_by('-academic_year', 'term')

    context = {
        'beneficiary': beneficiary,
        'payments': payments,
        'performances': performances,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    return render(request, 'beneficiary_detail.html', context)

# views.py
@login_required
def edit_beneficiary(request, pk):
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    
    if request.method == 'POST':
        # Get all form data
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        gender = request.POST.get('gender')
        date_of_birth = request.POST.get('date_of_birth')
        national_id = request.POST.get('national_id')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        current_level = request.POST.get('current_level')
        institution_id = request.POST.get('institution')
        enrollment_date = request.POST.get('enrollment_date')
        sponsor_id = request.POST.get('sponsor')
        photo = request.FILES.get('photo')
        is_active = request.POST.get('is_active') == 'on'
        
        # Validate required fields
        errors = {}
        if not first_name:
            errors['first_name'] = 'First name is required'
        if not last_name:
            errors['last_name'] = 'Last name is required'
        if not date_of_birth:
            errors['date_of_birth'] = 'Date of birth is required'
        if not gender:
            errors['gender'] = 'Gender is required'
        if not current_level:
            errors['current_level'] = 'Education level is required'
        if not enrollment_date:
            errors['enrollment_date'] = 'Enrollment date is required'
            
        if errors:
            # Get all institutions and sponsors for the form
            institutions = Institution.objects.all()
            sponsors = Sponsor.objects.all()
            
            context = {
                'beneficiary': beneficiary,
                'errors': errors,
                'institutions': institutions,
                'sponsors': sponsors,
                'education_levels': Beneficiary.LEVEL_CHOICES,
                'genders': Beneficiary.GENDER_CHOICES,
                'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
                'form_data': request.POST  # To repopulate form
            }
            return render(request, 'beneficiary_edit.html', context)
        
        try:
            # Update the beneficiary
            beneficiary.first_name = first_name
            beneficiary.last_name = last_name
            beneficiary.gender = gender
            beneficiary.date_of_birth = date_of_birth
            beneficiary.national_id = national_id
            beneficiary.phone_number = phone_number
            beneficiary.email = email
            beneficiary.current_level = current_level
            beneficiary.institution_id = institution_id
            beneficiary.enrollment_date = enrollment_date
            beneficiary.sponsor_id = sponsor_id
            beneficiary.is_active = is_active
            
            if photo:
                beneficiary.photo = photo
                
            beneficiary.save()
            
            messages.success(request, 'Beneficiary updated successfully!')
            return redirect('beneficiary_detail', pk=beneficiary.pk)
            
        except Exception as e:
            messages.error(request, f'Error updating beneficiary: {str(e)}')
            return redirect('edit_beneficiary', pk=beneficiary.pk)
    
    else:
        # GET request - show form with current data
        institutions = Institution.objects.all()
        sponsors = Sponsor.objects.all()
        
        context = {
            'beneficiary': beneficiary,
            'institutions': institutions,
            'sponsors': sponsors,
            'education_levels': Beneficiary.LEVEL_CHOICES,
            'genders': Beneficiary.GENDER_CHOICES,
            'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count()
        }
        return render(request, 'beneficiary_edit.html', context)

@login_required
def delete_beneficiary(request, pk):
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    if request.method == 'POST':
        beneficiary.is_active = False
        beneficiary.save()
        messages.success(request, f'{beneficiary.full_name} has been deactivated.')
        return redirect('beneficiaries_list')
    
    context = {
        'beneficiary': beneficiary,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    return render(request, 'beneficiary_confirm_delete.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from .models import FinancialAid, Beneficiary, Sponsor
from datetime import datetime

@login_required
def financial_dashboard(request):
    # Financial metrics
    total_disbursed = FinancialAid.objects.filter(status='disbursed').aggregate(
        total=Sum('amount_approved')
    )['total'] or 0
    
    beneficiaries_supported = FinancialAid.objects.filter(
        status='disbursed'
    ).values('beneficiary').distinct().count()
    
    average_award = FinancialAid.objects.filter(
        status='disbursed'
    ).aggregate(avg=Avg('amount_approved'))['avg'] or 0
    
    # Get current academic year (format: 2023-2024)
    current_year = datetime.now().year
    academic_year = f"{current_year}-{current_year + 1}"
    
    # Budget data (this would come from your budget model or settings)
    total_budget = 7000000  # Example value
    remaining_budget = total_budget - total_disbursed
    
    # Recent disbursements
    recent_disbursements = FinancialAid.objects.filter(
        status='disbursed'
    ).select_related('beneficiary').order_by('-disbursement_date')[:6]
    
    # Status distribution
    status_distribution = FinancialAid.objects.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('amount_approved')
    )
    
    context = {
        'total_disbursed': total_disbursed,
        'beneficiaries_supported': beneficiaries_supported,
        'average_award': average_award,
        'remaining_budget': remaining_budget,
        'total_budget': total_budget,
        'recent_disbursements': recent_disbursements,
        'status_distribution': status_distribution,
        'academic_year': academic_year,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'financial_dashboard.html', context)

@login_required
def financial_aid_list(request):
    # Get filter parameters
    education_level = request.GET.get('education_level')
    status = request.GET.get('status')
    year = request.GET.get('year')
    sponsor_id = request.GET.get('sponsor')
    search_query = request.GET.get('search', '')
    
    # Start with all records
    financial_aids = FinancialAid.objects.all().select_related(
        'beneficiary', 'beneficiary__institution', 'beneficiary__sponsor'
    ).order_by('-request_date')
    
    # Apply filters
    if education_level:
        financial_aids = financial_aids.filter(
            beneficiary__current_level=education_level
        )
    
    if status:
        financial_aids = financial_aids.filter(status=status)
    
    if year:
        financial_aids = financial_aids.filter(academic_year=year)
    
    if sponsor_id:
        financial_aids = financial_aids.filter(
            beneficiary__sponsor__id=sponsor_id
        )
    
    if search_query:
        financial_aids = financial_aids.filter(
            Q(beneficiary__first_name__icontains=search_query) |
            Q(beneficiary__last_name__icontains=search_query) |
            Q(receipt_number__icontains=search_query)
        )
    
    # Get distinct academic years for filter dropdown
    academic_years = FinancialAid.objects.values_list(
        'academic_year', flat=True
    ).distinct().order_by('-academic_year')
    
    # Pagination
    paginator = Paginator(financial_aids, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'financial_aids': page_obj,
        'education_levels': Beneficiary.LEVEL_CHOICES,
        'academic_years': academic_years,
        'sponsors': Sponsor.objects.all(),
        'status_choices': FinancialAid.STATUS_CHOICES,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        'is_paginated': paginator.num_pages > 1,
    }
    
    return render(request, 'financial_aid_list.html', context)

@login_required
def add_financial_aid(request):
    if request.method == 'POST':
        beneficiary_id = request.POST.get('beneficiary')
        academic_year = request.POST.get('academic_year')
        term = request.POST.get('term')
        amount_requested = request.POST.get('amount_requested')
        notes = request.POST.get('notes', '')
        
        # Validate
        errors = {}
        if not beneficiary_id:
            errors['beneficiary'] = 'Beneficiary is required'
        if not academic_year:
            errors['academic_year'] = 'Academic year is required'
        if not term:
            errors['term'] = 'Term is required'
        if not amount_requested:
            errors['amount_requested'] = 'Amount requested is required'
        
        if errors:
            beneficiaries = Beneficiary.objects.filter(is_active=True)
            context = {
                'beneficiaries': beneficiaries,
                'term_choices': FinancialAid.TERM_CHOICES,
                'errors': errors,
                'form_data': request.POST,
                'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
            }
            return render(request, 'financial_aid_add.html', context)
        
        try:
            financial_aid = FinancialAid(
                beneficiary_id=beneficiary_id,
                academic_year=academic_year,
                term=term,
                amount_requested=amount_requested,
                notes=notes,
                status='pending'
            )
            financial_aid.save()
            
            messages.success(request, 'Financial aid request submitted successfully!')
            return redirect('financial_aid_detail', pk=financial_aid.pk)
        
        except Exception as e:
            messages.error(request, f'Error creating financial aid request: {str(e)}')
            return redirect('add_financial_aid')
    
    else:
        # GET request
        beneficiaries = Beneficiary.objects.filter(is_active=True)
        current_year = datetime.now().year
        academic_year = f"{current_year}-{current_year + 1}"
        
        context = {
            'beneficiaries': beneficiaries,
            'term_choices': FinancialAid.TERM_CHOICES,
            'default_academic_year': academic_year,
            'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        }
        return render(request, 'financial_aid_add.html', context)

@login_required
def financial_aid_detail(request, pk):
    financial_aid = get_object_or_404(FinancialAid, pk=pk)
    
    context = {
        'financial_aid': financial_aid,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    return render(request, 'financial_aid_detail.html', context)

@login_required
def update_financial_aid_status(request, pk):
    financial_aid = get_object_or_404(FinancialAid, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        amount_approved = request.POST.get('amount_approved')
        notes = request.POST.get('notes', '')
        
        if not new_status:
            messages.error(request, 'Status is required')
            return redirect('financial_aid_detail', pk=financial_aid.pk)
        
        if new_status == 'approved' and not amount_approved:
            messages.error(request, 'Approved amount is required when approving')
            return redirect('financial_aid_detail', pk=financial_aid.pk)
        
        try:
            financial_aid.status = new_status
            if amount_approved:
                financial_aid.amount_approved = amount_approved
            if notes:
                financial_aid.notes = notes
            if new_status == 'approved':
                financial_aid.approved_by = request.user
            financial_aid.save()
            
            messages.success(request, f'Financial aid status updated to {financial_aid.get_status_display()}')
            return redirect('financial_aid_detail', pk=financial_aid.pk)
        
        except Exception as e:
            messages.error(request, f'Error updating financial aid: {str(e)}')
            return redirect('financial_aid_detail', pk=financial_aid.pk)
    
    return redirect('financial_aid_detail', pk=financial_aid.pk)

@login_required
def financial_reports(request):
    # Generate reports data
    disbursements_by_term = FinancialAid.objects.filter(
        status='disbursed'
    ).values('academic_year', 'term').annotate(
        total_amount=Sum('amount_approved'),
        count=Count('id')
    ).order_by('academic_year', 'term')
    
    disbursements_by_level = FinancialAid.objects.filter(
        status='disbursed'
    ).values('beneficiary__current_level').annotate(
        total_amount=Sum('amount_approved'),
        count=Count('id')
    ).order_by('beneficiary__current_level')
    
    funding_sources = FinancialAid.objects.filter(
        status='disbursed'
    ).values('beneficiary__sponsor__name').annotate(
        total_amount=Sum('amount_approved'),
        count=Count('id')
    ).order_by('-total_amount')
    
    context = {
        'disbursements_by_term': disbursements_by_term,
        'disbursements_by_level': disbursements_by_level,
        'funding_sources': funding_sources,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    return render(request, 'financial_reports.html', context)



# Add to views.py

from django.db.models import Avg, Max, Min, Count, Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from django.db import transaction
from .models import AcademicPerformance, SubjectPerformance, Beneficiary, Subject, Notification, PerformanceReport, ActivityLog


@login_required
def performance_dashboard(request):
    # Get filter parameters
    education_level = request.GET.get('education_level', '')
    term = request.GET.get('term', '')
    year = request.GET.get('year', datetime.now().year)
    subject = request.GET.get('subject', '')
    
    # Base queryset
    performances = AcademicPerformance.objects.all()
    subject_performances = SubjectPerformance.objects.all()
    
    # Apply filters
    if education_level:
        performances = performances.filter(beneficiary__current_level=education_level)
        subject_performances = subject_performances.filter(beneficiary__current_level=education_level)
    
    if term:
        performances = performances.filter(term=term)
        subject_performances = subject_performances.filter(term=term)
    
    if year:
        performances = performances.filter(academic_year=year)
        subject_performances = subject_performances.filter(academic_year=year)
    
    if subject:
        subject_performances = subject_performances.filter(subject_id=subject)
    
    # Calculate metrics
    avg_score = performances.aggregate(avg=Avg('average_score'))['avg'] or 0
    top_score = performances.aggregate(max=Max('average_score'))['max'] or 0
    passing_rate = performances.filter(average_score__gte=50).count() / performances.count() * 100 if performances.count() > 0 else 0
    
    # Get top performers with improvement
    top_performers = performances.select_related('beneficiary').order_by('-average_score')[:5]
    top_performers = [
        {
            'beneficiary': p.beneficiary,
            'average_score': p.average_score,
            'improvement': abs(p.average_score - 70),  # Calculate absolute improvement from 70
            'is_positive': p.average_score >= 70  # Determine if improvement is positive
        } for p in top_performers
    ]
    
    # Get subject averages
    subject_averages = subject_performances.values(
        'subject__name'
    ).annotate(
        avg_score=Avg('score'),
        count=Count('id')
    ).order_by('-avg_score')
    
    # Get performance trends
    performance_trends = performances.values(
        'term', 'academic_year'
    ).annotate(
        avg_score=Avg('average_score')
    ).order_by('academic_year', 'term')
    
    context = {
        'education_levels': Beneficiary.LEVEL_CHOICES,
        'subjects': Subject.objects.all(),
        'selected_level': education_level,
        'selected_term': term,
        'selected_year': year,
        'selected_subject': subject,
        # Metrics
        'avg_score': avg_score,
        'top_score': top_score,
        'passing_rate': passing_rate,
        # Data for charts
        'top_performers': top_performers,
        'subject_averages': subject_averages,
        'performance_trends': list(performance_trends),
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        'years_range': range(2020, datetime.now().year + 1),
    }
    
    return render(request, 'performance_dashboard.html', context)

@login_required
def performance_data_api(request):
    # API endpoint for AJAX requests
    education_level = request.GET.get('education_level', '')
    term = request.GET.get('term', '')
    year = request.GET.get('year', '')
    subject = request.GET.get('subject', '')
    data_type = request.GET.get('type', 'trend')
    
    if data_type == 'trend':
        # Return performance trend data
        performances = AcademicPerformance.objects.all()
        
        if education_level:
            performances = performances.filter(beneficiary__current_level=education_level)
        if term:
            performances = performances.filter(term=term)
        if year:
            performances = performances.filter(academic_year=year)
        
        data = performances.values(
            'term', 'academic_year'
        ).annotate(
            avg_score=Avg('average_score')
        ).order_by('academic_year', 'term')
        
        return JsonResponse({'data': list(data)})
    
    elif data_type == 'subject':
        # Return subject performance data
        performances = SubjectPerformance.objects.all()
        
        if education_level:
            performances = performances.filter(beneficiary__current_level=education_level)
        if term:
            performances = performances.filter(term=term)
        if year:
            performances = performances.filter(academic_year=year)
        if subject:
            performances = performances.filter(subject_id=subject)
        
        data = performances.values(
            'subject__name'
        ).annotate(
            avg_score=Avg('score'),
            count=Count('id')
        ).order_by('-avg_score')
        
        return JsonResponse({'data': list(data)})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def export_performance_report(request):
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        academic_year = request.POST.get('academic_year')
        term = request.POST.get('term', '')
        education_level = request.POST.get('education_level', '')
        
        report = PerformanceReport.objects.create(
            title=f"{report_type.capitalize()} Report - {academic_year} {term}",
            report_type=report_type,
            academic_year=academic_year,
            term=term if term else None,
            generated_by=request.user
        )
        
        messages.success(request, f"Report generated successfully (ID: {report.id})")
        return redirect('performance_dashboard')
    
    return redirect('performance_dashboard')

@login_required
@transaction.atomic
def add_performance(request):
    if request.method == 'POST':
        try:
            # Extract AcademicPerformance data
            beneficiary_id = request.POST.get('beneficiary')
            term = request.POST.get('term')
            academic_year = request.POST.get('academic_year')
            average_score = request.POST.get('average_score')
            rank = request.POST.get('rank')
            comments = request.POST.get('comments', '')

            # Validate required fields
            if not all([beneficiary_id, term, academic_year, average_score, rank]):
                messages.error(request, "All required fields must be filled.")
                return redirect('add_performance')

            # Get beneficiary
            try:
                beneficiary = Beneficiary.objects.get(id=beneficiary_id)
            except Beneficiary.DoesNotExist:
                messages.error(request, "Selected beneficiary does not exist.")
                return redirect('add_performance')

            # Validate numeric fields
            try:
                average_score = float(average_score)
                if not 0 <= average_score <= 100:
                    raise ValueError("Average score must be between 0 and 100.")
                rank = int(rank)
                if rank < 1:
                    raise ValueError("Rank must be a positive integer.")
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('add_performance')

            # Create AcademicPerformance
            academic_performance = AcademicPerformance.objects.create(
                beneficiary=beneficiary,
                term=term,
                academic_year=academic_year,
                average_score=average_score,
                rank=rank,
                comments=comments
            )

            # Extract SubjectPerformance data
            subject_ids = request.POST.getlist('subject[]')
            scores = request.POST.getlist('score[]')
            grades = request.POST.getlist('grade[]')
            subject_comments = request.POST.getlist('subject_comments[]')

            if not subject_ids:
                messages.error(request, "At least one subject performance record is required.")
                return redirect('add_performance')

            for i, subject_id in enumerate(subject_ids):
                try:
                    subject = Subject.objects.get(id=subject_id)
                    score = float(scores[i])
                    if not 0 <= score <= 100:
                        raise ValueError(f"Score for {subject.name} must be between 0 and 100.")
                    grade = grades[i].upper()
                    if grade not in ['A', 'B', 'C', 'D', 'E', 'F']:
                        raise ValueError(f"Invalid grade for {subject.name}. Use A, B, C, D, E, or F.")
                    comment = subject_comments[i] if i < len(subject_comments) else ''

                    SubjectPerformance.objects.create(
                        beneficiary=beneficiary,
                        subject=subject,
                        term=term,
                        academic_year=academic_year,
                        score=score,
                        grade=grade,
                        comments=comment
                    )
                except (Subject.DoesNotExist, ValueError) as e:
                    messages.error(request, str(e))
                    return redirect('add_performance')

            # Log activity
            ActivityLog.objects.create(
                activity_type='performance',
                description=f"Added performance record for {beneficiary.full_name} - Term {term} {academic_year}",
                recorded_by=request.user,
                related_beneficiary=beneficiary
            )

            messages.success(request, f"Performance record for {beneficiary.full_name} added successfully.")
            return redirect('performance_dashboard')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('add_performance')

    # GET request: Render form
    context = {
        'beneficiaries': Beneficiary.objects.filter(is_active=True).order_by('last_name', 'first_name'),
        'subjects': Subject.objects.all().order_by('name'),
        'years_range': range(2020, datetime.now().year + 1),
        'term_choices': [
            ('term1', 'Term 1'),
            ('term2', 'Term 2'),
            ('term3', 'Term 3')
        ],
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    return render(request, 'add_performance.html', context)

@login_required
def performance_detail(request, pk):
    beneficiary = get_object_or_404(Beneficiary, pk=pk)
    academic_performances = AcademicPerformance.objects.filter(beneficiary=beneficiary).order_by('-academic_year', '-term')
    subject_performances = SubjectPerformance.objects.filter(beneficiary=beneficiary).order_by('-academic_year', '-term', 'subject__name')
    
    # Calculate metrics for the beneficiary
    avg_score = academic_performances.aggregate(avg=Avg('average_score'))['avg'] or 0
    top_score = academic_performances.aggregate(max=Max('average_score'))['max'] or 0
    subject_averages = subject_performances.values('subject__name').annotate(
        avg_score=Avg('score')
    ).order_by('-avg_score')
    
    context = {
        'beneficiary': beneficiary,
        'academic_performances': academic_performances,
        'subject_performances': subject_performances,
        'avg_score': avg_score,
        'top_score': top_score,
        'subject_averages': subject_averages,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'performance_detail.html', context)
