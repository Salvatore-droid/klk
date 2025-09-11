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
    school_filter = request.GET.get('school')
    gender_filter = request.GET.get('gender')
    form_filter = request.GET.get('form')
    year_joined_filter = request.GET.get('year_joined')
    sponsor_filter = request.GET.get('sponsor')
    search_query = request.GET.get('search', '')
    search_by = request.GET.get('search_by', 'name')  # name, admission_number, school

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

    if school_filter:
        beneficiaries = beneficiaries.filter(
            Q(current_school__icontains=school_filter) | 
            Q(previous_school__icontains=school_filter) |
            Q(institution__name__icontains=school_filter)
        )
    
    if gender_filter:
        beneficiaries = beneficiaries.filter(gender=gender_filter)
    
    if form_filter:
        beneficiaries = beneficiaries.filter(current_level=form_filter)
    
    if year_joined_filter:
        beneficiaries = beneficiaries.filter(enrollment_date__year=year_joined_filter)
    
    if sponsor_filter:
        beneficiaries = beneficiaries.filter(sponsor__id=sponsor_filter)

    # Apply search
    if search_query:
        if search_by == 'admission_number':
            # Assuming you have an admission_number field
            beneficiaries = beneficiaries.filter(admission_number__icontains=search_query)
        elif search_by == 'school':
            beneficiaries = beneficiaries.filter(
                Q(current_school__icontains=search_query) | 
                Q(previous_school__icontains=search_query) |
                Q(institution__name__icontains=search_query)
            )
        else:  # search by name
            beneficiaries = beneficiaries.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(guardian_full_name__icontains=search_query)
            )

    # Get distinct enrollment years for filter dropdown
    enrollment_years = Beneficiary.objects.dates('enrollment_date', 'year').order_by('-enrollment_date')

    # Pagination
    paginator = Paginator(beneficiaries, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'beneficiaries': page_obj,
        'schools': Beneficiary.objects.filter(is_active=True).exclude(current_school__isnull=True).exclude(current_school='').values_list('current_school', flat=True).distinct(),
        'genders': Beneficiary.GENDER_CHOICES,
        'forms': Beneficiary.LEVEL_CHOICES,
        'years_joined': Beneficiary.objects.dates('enrollment_date', 'year').order_by('-enrollment_date'),
        'sponsors': Sponsor.objects.all(),
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        'is_paginated': paginator.num_pages > 1,
        'search_by': search_by,
        'search_query': search_query,
        'school_filter': school_filter,
        'gender_filter': gender_filter,
        'form_filter': form_filter,
        'year_joined_filter': year_joined_filter,
        'sponsor_filter': sponsor_filter,
        'education_levels': Beneficiary.LEVEL_CHOICES,
        'enrollment_years': [date.year for date in enrollment_years],
        'sponsors': Sponsor.objects.all(),
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        'is_paginated': paginator.num_pages > 1,

    }

    return render(request, 'benef.html', context)

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
        previous_school = request.POST.get('previous_school')
        current_school = request.POST.get('current_school')
        admission_letter = request.FILES.get('admission_letter')
        fee_structure = request.FILES.get('fee_structure')
        fee_statement = request.FILES.get('fee_statement')
        receipts = request.FILES.get('receipts')
        letters = request.FILES.get('letters')
        
        # Parent/Guardian details
        guardian_type = request.POST.get('guardian_type')
        guardian_full_name = request.POST.get('guardian_full_name')
        guardian_phone = request.POST.get('guardian_phone')
        guardian_id_copy = request.FILES.get('guardian_id_copy')
        guardian_email = request.POST.get('guardian_email')
        
        # Residence information
        residence_address = request.POST.get('residence_address')
        residence_directions = request.POST.get('residence_directions')
        
        # Referrals
        referral_source = request.POST.get('referral_source')
        
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
                is_active=True,
                previous_school=previous_school,
                current_school=current_school,
                guardian_type=guardian_type,
                guardian_full_name=guardian_full_name,
                guardian_phone=guardian_phone,
                guardian_email=guardian_email,
                residence_address=residence_address,
                residence_directions=residence_directions,
                referral_source=referral_source,
            )
            if admission_letter:
                beneficiary.admission_letter = admission_letter
            if fee_structure:
                beneficiary.fee_structure = fee_structure
            if fee_statement:
                beneficiary.fee_statement = fee_statement
            if receipts:
                beneficiary.receipts = receipts
            if letters:
                beneficiary.letters = letters
            if guardian_id_copy:
                beneficiary.guardian_id_copy = guardian_id_copy
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
            'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
            'guardian_types': Beneficiary.GUARDIAN_TYPE_CHOICES,
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


from django.db.models import Avg, Max, Count
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from datetime import datetime
from django.db import transaction
from .models import AcademicPerformance, SubjectPerformance, Beneficiary, Subject, Notification
import csv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors
import os

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
    
    # Get top performers with improvement and score history
    top_performers = performances.select_related('beneficiary').order_by('-average_score')[:5]
    top_performers = [
        {
            'beneficiary': p.beneficiary,
            'average_score': p.average_score,
            'improvement': abs(p.average_score - (AcademicPerformance.objects.filter(
                beneficiary=p.beneficiary,
                academic_year__lt=p.academic_year
            ).aggregate(avg=Avg('average_score'))['avg'] or p.average_score)),
            'is_positive': p.average_score >= (AcademicPerformance.objects.filter(
                beneficiary=p.beneficiary,
                academic_year__lt=p.academic_year
            ).aggregate(avg=Avg('average_score'))['avg'] or p.average_score),
            'academic_performance_id': p.id,
            'rank': p.rank,
            'score_history': list(AcademicPerformance.objects.filter(
                beneficiary=p.beneficiary
            ).order_by('-academic_year', '-term')[:3].values_list('average_score', flat=True))
        } for p in top_performers
    ]
    
    # Get subject averages
    subject_averages = subject_performances.values(
        'subject__name'
    ).annotate(
        avg_score=Avg('score'),
        count=Count('id')
    ).order_by('-avg_score')
    
    context = {
        'education_levels': Beneficiary.LEVEL_CHOICES,
        'subjects': Subject.objects.all(),
        'selected_level': education_level,
        'selected_term': term,
        'selected_year': year,
        'selected_subject': subject,
        'avg_score': avg_score,
        'top_score': top_score,
        'passing_rate': passing_rate,
        'top_performers': top_performers,
        'subject_averages': subject_averages,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        'years_range': range(2020, datetime.now().year + 1),
    }
    
    return render(request, 'performance_dashboard.html', context)

@login_required
def performance_data_api(request):
    education_level = request.GET.get('education_level', '')
    term = request.GET.get('term', '')
    year = request.GET.get('year', '')
    subject = request.GET.get('subject', '')
    data_type = request.GET.get('type', 'trend')
    
    if data_type == 'trend':
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
    
    elif data_type == 'distribution':
        data_type_detail = request.GET.get('data_type', 'overall')
        performances = AcademicPerformance.objects.all()
        
        if education_level:
            performances = performances.filter(beneficiary__current_level=education_level)
        if term:
            performances = performances.filter(term=term)
        if year:
            performances = performances.filter(academic_year=year)
        
        if data_type_detail == 'overall':
            data = [
                {'range': 'Excellent (85-100)', 'count': performances.filter(average_score__gte=85).count()},
                {'range': 'Good (70-84)', 'count': performances.filter(average_score__gte=70, average_score__lt=85).count()},
                {'range': 'Average (50-69)', 'count': performances.filter(average_score__gte=50, average_score__lt=70).count()},
                {'range': 'Poor (<50)', 'count': performances.filter(average_score__lt=50).count()}
            ]
            return JsonResponse({
                'labels': [item['range'] for item in data],
                'values': [item['count'] for item in data]
            })
        
        elif data_type_detail == 'by_level':
            data = performances.values('beneficiary__current_level').annotate(
                count=Count('id')
            ).order_by('beneficiary__current_level')
            return JsonResponse({
                'labels': [Beneficiary.LEVEL_CHOICES[int(item['beneficiary__current_level'])][1] for item in data],
                'values': [item['count'] for item in data]
            })
        
        elif data_type_detail == 'by_subject':
            performances = SubjectPerformance.objects.all()
            if education_level:
                performances = performances.filter(beneficiary__current_level=education_level)
            if term:
                performances = performances.filter(term=term)
            if year:
                performances = performances.filter(academic_year=year)
            if subject:
                performances = performances.filter(subject_id=subject)
            
            data = performances.values('subject__name').annotate(
                count=Count('id')
            ).order_by('subject__name')
            return JsonResponse({
                'labels': [item['subject__name'] for item in data],
                'values': [item['count'] for item in data]
            })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def export_performance_report(request):
    format_type = request.GET.get('format', 'csv')
    education_level = request.GET.get('education_level', '')
    term = request.GET.get('term', '')
    year = request.GET.get('year', '')
    
    performances = AcademicPerformance.objects.all()
    if education_level:
        performances = performances.filter(beneficiary__current_level=education_level)
    if term:
        performances = performances.filter(term=term)
    if year:
        performances = performances.filter(academic_year=year)
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="performance_report_{year}_{term}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Name', 'Education Level', 'Average Score', 'Rank', 'Term', 'Year'])
        
        for p in performances.select_related('beneficiary'):
            writer.writerow([
                p.beneficiary.full_name,
                p.beneficiary.get_current_level_display(),
                f"{p.average_score:.1f}%",
                p.rank,
                p.term,
                p.academic_year
            ])
        
        return response
    
    elif format_type == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="performance_report_{year}_{term}.pdf"'
        
        doc = SimpleDocTemplate(response, pagesize=letter)
        elements = []
        
        data = [['Name', 'Education Level', 'Average Score', 'Rank', 'Term', 'Year']]
        for p in performances.select_related('beneficiary'):
            data.append([
                p.beneficiary.full_name,
                p.beneficiary.get_current_level_display(),
                f"{p.average_score:.1f}%",
                p.rank,
                p.term,
                p.academic_year
            ])
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        return response
    
    return redirect('performance_dashboard')

# ... (other views remain unchanged)

@login_required
@transaction.atomic
def add_performance(request):
    if request.method == 'POST':
        try:
            beneficiary_id = request.POST.get('beneficiary')
            term = request.POST.get('term')
            academic_year = request.POST.get('academic_year')
            average_score = request.POST.get('average_score')
            rank = request.POST.get('rank')
            comments = request.POST.get('comments', '')
            report_file = request.FILES.get('report_file')

            if not all([beneficiary_id, term, academic_year, average_score, rank, report_file]):
                messages.error(request, "All required fields must be filled, including the PDF report.")
                return redirect('add_performance')

            if report_file and not report_file.name.lower().endswith('.pdf'):
                messages.error(request, "Uploaded file must be a PDF.")
                return redirect('add_performance')

            try:
                beneficiary = Beneficiary.objects.get(id=beneficiary_id)
            except Beneficiary.DoesNotExist:
                messages.error(request, "Selected beneficiary does not exist.")
                return redirect('add_performance')

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

            academic_performance = AcademicPerformance.objects.create(
                beneficiary=beneficiary,
                term=term,
                academic_year=academic_year,
                average_score=average_score,
                rank=rank,
                comments=comments,
                report_file=report_file
            )

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

            messages.success(request, f"Performance record for {beneficiary.full_name} added successfully.")
            return redirect('performance_dashboard')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('add_performance')

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

@login_required
@transaction.atomic
def edit_performance(request, pk):
    performance = get_object_or_404(AcademicPerformance, pk=pk)
    subject_performances = SubjectPerformance.objects.filter(
        beneficiary=performance.beneficiary,
        term=performance.term,
        academic_year=performance.academic_year
    )

    if request.method == 'POST':
        try:
            term = request.POST.get('term')
            academic_year = request.POST.get('academic_year')
            average_score = request.POST.get('average_score')
            rank = request.POST.get('rank')
            comments = request.POST.get('comments', '')
            report_file = request.FILES.get('report_file')

            if not all([term, academic_year, average_score, rank]):
                messages.error(request, "All required fields must be filled.")
                return redirect('edit_performance', pk=pk)

            if report_file and not report_file.name.lower().endswith('.pdf'):
                messages.error(request, "Uploaded file must be a PDF.")
                return redirect('edit_performance', pk=pk)

            try:
                average_score = float(average_score)
                if not 0 <= average_score <= 100:
                    raise ValueError("Average score must be between 0 and 100.")
                rank = int(rank)
                if rank < 1:
                    raise ValueError("Rank must be a positive integer.")
            except ValueError as e:
                messages.error(request, str(e))
                return redirect('edit_performance', pk=pk)

            performance.term = term
            performance.academic_year = academic_year
            performance.average_score = average_score
            performance.rank = rank
            performance.comments = comments
            if report_file:
                if performance.report_file:
                    if os.path.isfile(performance.report_file.path):
                        os.remove(performance.report_file.path)
                performance.report_file = report_file
            performance.save()

            subject_ids = request.POST.getlist('subject[]')
            scores = request.POST.getlist('score[]')
            grades = request.POST.getlist('grade[]')
            subject_comments = request.POST.getlist('subject_comments[]')
            subject_performance_ids = request.POST.getlist('subject_performance_id[]')

            if not subject_ids:
                messages.error(request, "At least one subject performance record is required.")
                return redirect('edit_performance', pk=pk)

            existing_ids = set(subject_performance_ids)
            current_ids = set(str(sp.id) for sp in subject_performances)

            for sp_id in current_ids - existing_ids:
                if sp_id:
                    SubjectPerformance.objects.filter(id=sp_id).delete()

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
                    sp_id = subject_performance_ids[i] if i < len(subject_performance_ids) else ''

                    if sp_id:
                        sp = SubjectPerformance.objects.get(id=sp_id)
                        sp.subject = subject
                        sp.score = score
                        sp.grade = grade
                        sp.comments = comment
                        sp.term = term
                        sp.academic_year = academic_year
                        sp.save()
                    else:
                        SubjectPerformance.objects.create(
                            beneficiary=performance.beneficiary,
                            subject=subject,
                            term=term,
                            academic_year=academic_year,
                            score=score,
                            grade=grade,
                            comments=comment
                        )
                except (Subject.DoesNotExist, SubjectPerformance.DoesNotExist, ValueError) as e:
                    messages.error(request, str(e))
                    return redirect('edit_performance', pk=pk)

            messages.success(request, f"Performance record for {performance.beneficiary.full_name} updated successfully.")
            return redirect('performance_detail', pk=performance.beneficiary.id)

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('edit_performance', pk=pk)

    context = {
        'performance': performance,
        'subject_performances': subject_performances,
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
    return render(request, 'edit_performance.html', context)

@login_required
def delete_performance(request, pk):
    performance = get_object_or_404(AcademicPerformance, pk=pk)
    beneficiary = performance.beneficiary
    term = performance.term
    academic_year = performance.academic_year

    if request.method == 'POST':
        try:
            SubjectPerformance.objects.filter(
                beneficiary=beneficiary,
                term=term,
                academic_year=academic_year
            ).delete()

            if performance.report_file:
                if os.path.isfile(performance.report_file.path):
                    os.remove(performance.report_file.path)

            performance.delete()

            messages.success(request, f"Performance record for {beneficiary.full_name} deleted successfully.")
            return redirect('performance_detail', pk=beneficiary.id)

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('performance_detail', pk=beneficiary.id)

    return redirect('performance_detail', pk=beneficiary.id)

@login_required
def add_performance_note(request, pk):
    performance = get_object_or_404(AcademicPerformance, pk=pk)
    if request.method == 'POST':
        note = request.POST.get('note')
        if note:
            performance.comments = (performance.comments or '') + '\n' + note
            performance.save()
            
            messages.success(request, "Note added successfully.")
            return redirect('performance_detail', pk=performance.beneficiary.id)
        else:
            messages.error(request, "Note cannot be empty.")
    
    context = {
        'performance': performance,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    return render(request, 'add_performance_note.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
import calendar
from .models import AcademicEvent, EventType, EventParticipant, EventAttachment

@login_required
def academic_calendar(request):
    """
    Main academic calendar view
    """
    # Get filter parameters
    event_type = request.GET.get('event_type')
    month = request.GET.get('month', timezone.now().month)
    year = request.GET.get('year', timezone.now().year)
    view_type = request.GET.get('view', 'month')  # month, week, list
    
    try:
        month = int(month)
        year = int(year)
    except (ValueError, TypeError):
        month = timezone.now().month
        year = timezone.now().year
    
    # Calculate previous and next month/year for navigation
    prev_month = month - 1
    prev_year = year
    if prev_month < 1:
        prev_month = 12
        prev_year = year - 1
        
    next_month = month + 1
    next_year = year
    if next_month > 12:
        next_month = 1
        next_year = year + 1
    
    # Get events for the selected month/year
    start_date = datetime(year, month, 1)
    end_date = datetime(year, month, calendar.monthrange(year, month)[1])
    
    events = AcademicEvent.objects.filter(
        is_active=True,
        start_date__gte=start_date,
        start_date__lte=end_date
    )
    
    # Fix: Check if event_type is valid before filtering
    if event_type and event_type != 'all' and event_type != 'None':
        try:
            events = events.filter(event_type__id=int(event_type))
        except (ValueError, TypeError):
            # If event_type is not a valid integer, ignore the filter
            pass
    
    # Get upcoming events for sidebar
    upcoming_events = AcademicEvent.objects.filter(
        is_active=True,
        start_date__gte=timezone.now()
    ).order_by('start_date')[:10]
    
    # Get event types for filter
    event_types = EventType.objects.filter(is_active=True)
    
    # Generate calendar data for template
    cal = calendar.monthcalendar(year, month)
    
    # Prepare events for each day
    calendar_data = []
    today = timezone.now().date()
    
    for week in cal:
        week_data = []
        for day in week:
            day_events = []
            if day != 0:  # 0 means day is not in current month
                day_date = datetime(year, month, day).date()
                day_events = events.filter(
                    Q(start_date__date=day_date) | 
                    Q(end_date__date=day_date) |
                    Q(start_date__lte=day_date, end_date__gte=day_date)
                )
            week_data.append({
                'day': day,
                'events': day_events
            })
        calendar_data.append(week_data)
    
    context = {
        'calendar_data': calendar_data,
        'current_month': month,
        'current_year': year,
        'month_name': calendar.month_name[month],
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'upcoming_events': upcoming_events,
        'event_types': event_types,
        'selected_event_type': event_type,
        'view_type': view_type,
        'today': today,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'academic_calendar.html', context)

@login_required
def calendar_events_api(request):
    """
    API endpoint for calendar events (for AJAX requests)
    """
    start = request.GET.get('start')
    end = request.GET.get('end')
    event_type = request.GET.get('event_type')
    
    try:
        start_date = datetime.strptime(start, '%Y-%m-%d')
        end_date = datetime.strptime(end, '%Y-%m-%d')
    except (ValueError, TypeError):
        start_date = timezone.now() - timedelta(days=30)
        end_date = timezone.now() + timedelta(days=30)
    
    events = AcademicEvent.objects.filter(
        is_active=True,
        start_date__gte=start_date,
        end_date__lte=end_date
    )
    
    if event_type and event_type != 'all':
        events = events.filter(event_type__id=event_type)
    
    events_data = []
    for event in events:
        events_data.append({
            'id': event.id,
            'title': event.title,
            'start': event.start_date.isoformat(),
            'end': event.end_date.isoformat(),
            'allDay': event.all_day,
            'color': event.event_type.color,
            'type': event.event_type.name,
            'location': event.location or '',
            'url': f'/calendar/event/{event.id}/'
        })
    
    return JsonResponse(events_data, safe=False)


@login_required
def add_event(request):
    """
    View to add a new academic event
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        event_type_id = request.POST.get('event_type')
        start_date_str = request.POST.get('start_date')
        end_date_str = request.POST.get('end_date')
        all_day = request.POST.get('all_day') == 'on'
        location = request.POST.get('location')
        priority = request.POST.get('priority')
        
        # Validate required fields
        errors = {}
        if not title:
            errors['title'] = 'Title is required'
        if not event_type_id:
            errors['event_type'] = 'Event type is required'
        if not start_date_str:
            errors['start_date'] = 'Start date is required'
        if not end_date_str:
            errors['end_date'] = 'End date is required'
        
        if errors:
            event_types = EventType.objects.filter(is_active=True)
            context = {
                'event_types': event_types,
                'priorities': AcademicEvent.PRIORITY_CHOICES,
                'errors': errors,
                'form_data': request.POST,
                'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
            }
            return render(request, 'add_event.html', context)
        
        try:
            event_type = EventType.objects.get(id=event_type_id)
            
            # Convert string dates to datetime objects
            if 'T' in start_date_str:
                start_datetime = datetime.strptime(start_date_str, '%Y-%m-%dT%H:%M')
            else:
                start_datetime = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
                
            if 'T' in end_date_str:
                end_datetime = datetime.strptime(end_date_str, '%Y-%m-%dT%H:%M')
            else:
                end_datetime = datetime.strptime(end_date_str, '%Y-%m-%d %H:%M:%S')
            
            # Create the event
            event = AcademicEvent(
                title=title,
                description=description,
                event_type=event_type,
                start_date=start_datetime,
                end_date=end_datetime,
                all_day=all_day,
                location=location,
                priority=priority,
                created_by=request.user
            )
            event.save()
            
            # Add creator as participant
            EventParticipant.objects.create(
                event=event,
                user=request.user,
                role='organizer',
                confirmed=True,
                confirmed_at=timezone.now()
            )
            
            messages.success(request, 'Event created successfully!')
            return redirect('academic_calendar')
            
        except Exception as e:
            messages.error(request, f'Error creating event: {str(e)}')
            return redirect('add_event')
    
    else:
        # GET request - show empty form
        event_types = EventType.objects.filter(is_active=True)
        
        # Set default dates for the form
        default_start = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        default_end = default_start + timedelta(hours=2)
        
        context = {
            'event_types': event_types,
            'priorities': AcademicEvent.PRIORITY_CHOICES,
            'default_start': default_start.strftime('%Y-%m-%dT%H:%M'),
            'default_end': default_end.strftime('%Y-%m-%dT%H:%M'),
            'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        }
        return render(request, 'add_event.html', context)


@login_required
def event_detail(request, event_id):
    """
    View to show event details
    """
    event = get_object_or_404(AcademicEvent, id=event_id, is_active=True)
    participants = EventParticipant.objects.filter(event=event).select_related('user')
    attachments = EventAttachment.objects.filter(event=event)
    
    # Check if current user is participating
    user_participation = None
    if request.user.is_authenticated:
        try:
            user_participation = EventParticipant.objects.get(event=event, user=request.user)
        except EventParticipant.DoesNotExist:
            pass
    
    context = {
        'event': event,
        'participants': participants,
        'attachments': attachments,
        'user_participation': user_participation,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'event_detail.html', context)


@login_required
def edit_event(request, event_id):
    """
    View to edit an existing event
    """
    event = get_object_or_404(AcademicEvent, id=event_id, is_active=True)
    
    # Check if user has permission to edit (creator or admin)
    if event.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this event.')
        return redirect('event_detail', event_id=event.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        event_type_id = request.POST.get('event_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        all_day = request.POST.get('all_day') == 'on'
        location = request.POST.get('location')
        priority = request.POST.get('priority')
        
        # Validate required fields
        errors = {}
        if not title:
            errors['title'] = 'Title is required'
        if not event_type_id:
            errors['event_type'] = 'Event type is required'
        if not start_date:
            errors['start_date'] = 'Start date is required'
        if not end_date:
            errors['end_date'] = 'End date is required'
        
        if errors:
            event_types = EventType.objects.filter(is_active=True)
            context = {
                'event': event,
                'event_types': event_types,
                'priorities': AcademicEvent.PRIORITY_CHOICES,
                'errors': errors,
                'form_data': request.POST,
                'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
            }
            return render(request, 'edit_event.html', context)
        
        try:
            event_type = EventType.objects.get(id=event_type_id)
            
            # Convert string dates to datetime objects
            start_datetime = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
            end_datetime = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
            
            # Update the event
            event.title = title
            event.description = description
            event.event_type = event_type
            event.start_date = start_datetime
            event.end_date = end_datetime
            event.all_day = all_day
            event.location = location
            event.priority = priority
            event.save()
            
            messages.success(request, 'Event updated successfully!')
            return redirect('event_detail', event_id=event.id)
            
        except Exception as e:
            messages.error(request, f'Error updating event: {str(e)}')
            return redirect('edit_event', event_id=event.id)
    
    else:
        # GET request - show form with current data
        event_types = EventType.objects.filter(is_active=True)
        
        # Format dates for datetime-local input
        start_date_formatted = event.start_date.strftime('%Y-%m-%dT%H:%M')
        end_date_formatted = event.end_date.strftime('%Y-%m-%dT%H:%M')
        
        context = {
            'event': event,
            'event_types': event_types,
            'priorities': AcademicEvent.PRIORITY_CHOICES,
            'start_date_formatted': start_date_formatted,
            'end_date_formatted': end_date_formatted,
            'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        }
        return render(request, 'edit_event.html', context)


@login_required
def delete_event(request, event_id):
    """
    View to delete an event (soft delete)
    """
    event = get_object_or_404(AcademicEvent, id=event_id, is_active=True)
    
    # Check if user has permission to delete (creator or admin)
    if event.created_by != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete this event.')
        return redirect('event_detail', event_id=event.id)
    
    if request.method == 'POST':
        event.is_active = False
        event.save()
        
        messages.success(request, 'Event deleted successfully!')
        return redirect('academic_calendar')
    
    context = {
        'event': event,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    return render(request, 'delete_event_confirm.html', context)


@login_required
def join_event(request, event_id):
    """
    View for a user to join an event
    """
    event = get_object_or_404(AcademicEvent, id=event_id, is_active=True)
    
    # Check if user is already participating
    existing_participation = EventParticipant.objects.filter(event=event, user=request.user).first()
    
    if existing_participation:
        messages.info(request, 'You are already participating in this event.')
        return redirect('event_detail', event_id=event.id)
    
    # Create new participation
    EventParticipant.objects.create(
        event=event,
        user=request.user,
        role='participant',
        confirmed=True,
        confirmed_at=timezone.now()
    )
    
    messages.success(request, 'You have successfully joined the event!')
    return redirect('event_detail', event_id=event.id)


@login_required
def leave_event(request, event_id):
    """
    View for a user to leave an event
    """
    event = get_object_or_404(AcademicEvent, id=event_id, is_active=True)
    
    # Check if user is participating
    participation = EventParticipant.objects.filter(event=event, user=request.user).first()
    
    if not participation:
        messages.info(request, 'You are not participating in this event.')
        return redirect('event_detail', event_id=event.id)
    
    # Remove participation (can't leave if you're the organizer)
    if participation.role == 'organizer':
        messages.error(request, 'Organizers cannot leave their own events. Please delete the event instead.')
        return redirect('event_detail', event_id=event.id)
    
    participation.delete()
    
    messages.success(request, 'You have successfully left the event.')
    return redirect('event_detail', event_id=event.id)


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Announcement, Message, MessageAttachment, DiscussionThread, 
    DiscussionReply, CommunicationCategory, UserNotificationPreference
)


@login_required
def communication_dashboard(request):
    """
    Main communication dashboard view
    """
    # Get recent announcements
    recent_announcements = Announcement.objects.filter(
        is_published=True,
        publish_date__lte=timezone.now()
    ).exclude(
        Q(expiration_date__lt=timezone.now()) | 
        Q(read_by=request.user)
    ).order_by('-publish_date')[:5]
    
    # Get unread messages count
    unread_messages_count = Message.objects.filter(
        recipients=request.user,
        status__in=['sent', 'delivered']
    ).count()
    
    # Get recent discussions
    recent_discussions = DiscussionThread.objects.annotate(
        reply_count=Count('replies')
    ).order_by('-updated_at')[:5]
    
    # Get user notification preferences
    try:
        notification_preferences = UserNotificationPreference.objects.get(user=request.user)
    except UserNotificationPreference.DoesNotExist:
        # Create default preferences if they don't exist
        notification_preferences = UserNotificationPreference.objects.create(user=request.user)
    
    context = {
        'recent_announcements': recent_announcements,
        'unread_messages_count': unread_messages_count,
        'recent_discussions': recent_discussions,
        'notification_preferences': notification_preferences,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'communication.html', context)


@login_required
def announcement_list(request):
    """
    View to list all announcements
    """
    # Get filter parameters
    category = request.GET.get('category')
    priority = request.GET.get('priority')
    status = request.GET.get('status', 'active')  # active, all, unread
    
    announcements = Announcement.objects.filter(is_published=True)
    
    # Apply filters
    if category and category != 'all':
        announcements = announcements.filter(category__id=category)
    
    if priority and priority != 'all':
        announcements = announcements.filter(priority=priority)
    
    if status == 'unread':
        announcements = announcements.exclude(read_by=request.user)
    elif status == 'all':
        # Show all published announcements regardless of read status
        pass
    else:  # active (default)
        announcements = announcements.filter(
            publish_date__lte=timezone.now()
        ).exclude(expiration_date__lt=timezone.now())
    
    # Get categories for filter
    categories = CommunicationCategory.objects.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(announcements.order_by('-publish_date'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'announcements': page_obj,
        'categories': categories,
        'priorities': Announcement.PRIORITY_CHOICES,
        'selected_category': category,
        'selected_priority': priority,
        'selected_status': status,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'announcement_list.html', context)


@login_required
def announcement_detail(request, announcement_id):
    """
    View to show announcement details and mark as read
    """
    announcement = get_object_or_404(Announcement, id=announcement_id, is_published=True)
    
    # Mark as read if user hasn't read it yet
    if request.user not in announcement.read_by.all():
        announcement.read_by.add(request.user)
    
    context = {
        'announcement': announcement,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'announcement_detail.html', context)


@login_required
def message_inbox(request):
    """
    View to show message inbox
    """
    # Get filter parameters
    folder = request.GET.get('folder', 'inbox')  # inbox, sent, archived, important
    search = request.GET.get('search', '')
    
    if folder == 'sent':
        messages = Message.objects.filter(sender=request.user)
    elif folder == 'archived':
        messages = Message.objects.filter(recipients=request.user, status='archived')
    elif folder == 'important':
        messages = Message.objects.filter(recipients=request.user, is_important=True)
    else:  # inbox
        messages = Message.objects.filter(recipients=request.user).exclude(status='archived')
    
    # Apply search filter
    if search:
        messages = messages.filter(
            Q(subject__icontains=search) |
            Q(body__icontains=search) |
            Q(sender__username__icontains=search) |
            Q(sender__first_name__icontains=search) |
            Q(sender__last_name__icontains=search)
        )
    
    # Get unread messages count for folder tabs
    inbox_count = Message.objects.filter(recipients=request.user).exclude(status__in=['read', 'archived']).count()
    important_count = Message.objects.filter(recipients=request.user, is_important=True).exclude(status='archived').count()
    archived_count = Message.objects.filter(recipients=request.user, status='archived').count()
    
    # Pagination
    paginator = Paginator(messages.order_by('-sent_at'), 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'messages': page_obj,
        'folder': folder,
        'search_query': search,
        'inbox_count': inbox_count,
        'important_count': important_count,
        'archived_count': archived_count,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'message_inbox.html', context)


@login_required
def message_detail(request, message_id):
    """
    View to show message details and mark as read
    """
    message = get_object_or_404(Message, id=message_id)
    
    # Check if user has permission to view this message
    if request.user != message.sender and request.user not in message.recipients.all():
        messages.error(request, 'You do not have permission to view this message.')
        return redirect('message_inbox')
    
    # Mark as read if user is a recipient
    if request.user in message.recipients.all():
        message.mark_as_read(request.user)
    
    context = {
        'message': message,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'message_detail.html', context)


@login_required
def send_message(request):
    """
    View to send a new message
    """
    if request.method == 'POST':
        recipient_ids = request.POST.getlist('recipients')
        subject = request.POST.get('subject')
        body = request.POST.get('body')
        is_important = request.POST.get('is_important') == 'on'
        
        # Validate required fields
        errors = {}
        if not recipient_ids:
            errors['recipients'] = 'At least one recipient is required'
        if not subject:
            errors['subject'] = 'Subject is required'
        if not body:
            errors['body'] = 'Message body is required'
        
        if errors:
            # Get all active users for recipient selection
            users = User.objects.filter(is_active=True).exclude(id=request.user.id)
            context = {
                'users': users,
                'errors': errors,
                'form_data': request.POST,
                'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
            }
            return render(request, 'send_message.html', context)
        
        try:
            # Create the message
            message = Message.objects.create(
                sender=request.user,
                subject=subject,
                body=body,
                is_important=is_important
            )
            
            # Add recipients
            recipients = User.objects.filter(id__in=recipient_ids)
            message.recipients.set(recipients)
            
            # Handle file attachments
            files = request.FILES.getlist('attachments')
            for file in files:
                attachment = MessageAttachment.objects.create(
                    file=file,
                    original_filename=file.name,
                    uploaded_by=request.user,
                    file_size=file.size
                )
                message.attachments.add(attachment)
            
            messages.success(request, 'Message sent successfully!')
            return redirect('message_inbox')
            
        except Exception as e:
            messages.error(request, f'Error sending message: {str(e)}')
            return redirect('send_message')
    
    else:
        # GET request - show empty form
        users = User.objects.filter(is_active=True).exclude(id=request.user.id)
        
        context = {
            'users': users,
            'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        }
        return render(request, 'send_message.html', context)


@login_required
def discussion_list(request):
    """
    View to list all discussion threads
    """
    # Get filter parameters
    category = request.GET.get('category')
    sort = request.GET.get('sort', 'recent')  # recent, popular, unanswered
    
    threads = DiscussionThread.objects.all()
    
    # Apply filters
    if category and category != 'all':
        threads = threads.filter(category__id=category)
    
    # Apply sorting
    if sort == 'popular':
        threads = threads.annotate(reply_count=Count('replies')).order_by('-reply_count', '-updated_at')
    elif sort == 'unanswered':
        threads = threads.annotate(reply_count=Count('replies')).filter(reply_count=0).order_by('-created_at')
    else:  # recent
        threads = threads.order_by('-is_pinned', '-updated_at')
    
    # Get categories for filter
    categories = CommunicationCategory.objects.filter(is_active=True)
    
    # Pagination
    paginator = Paginator(threads, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'threads': page_obj,
        'categories': categories,
        'selected_category': category,
        'selected_sort': sort,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'discussion_list.html', context)


@login_required
def discussion_detail(request, thread_id):
    """
    View to show discussion thread details
    """
    thread = get_object_or_404(DiscussionThread, id=thread_id)
    
    # Increment view count
    thread.views += 1
    thread.save()
    
    # Handle reply submission
    if request.method == 'POST':
        content = request.POST.get('content')
        parent_reply_id = request.POST.get('parent_reply')
        
        if not content:
            messages.error(request, 'Reply content cannot be empty.')
        else:
            try:
                parent_reply = None
                if parent_reply_id:
                    parent_reply = DiscussionReply.objects.get(id=parent_reply_id)
                
                DiscussionReply.objects.create(
                    thread=thread,
                    author=request.user,
                    content=content,
                    parent_reply=parent_reply
                )
                
                # Update thread's updated_at timestamp
                thread.updated_at = timezone.now()
                thread.save()
                
                messages.success(request, 'Reply posted successfully!')
                return redirect('discussion_detail', thread_id=thread.id)
                
            except Exception as e:
                messages.error(request, f'Error posting reply: {str(e)}')
    
    # Get all replies for this thread
    replies = DiscussionReply.objects.filter(thread=thread, is_approved=True).order_by('created_at')
    
    context = {
        'thread': thread,
        'replies': replies,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'discussion_detail.html', context)


@login_required
def create_discussion(request):
    """
    View to create a new discussion thread
    """
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        category_id = request.POST.get('category')
        
        # Validate required fields
        errors = {}
        if not title:
            errors['title'] = 'Title is required'
        if not content:
            errors['content'] = 'Content is required'
        if not category_id:
            errors['category'] = 'Category is required'
        
        if errors:
            categories = CommunicationCategory.objects.filter(is_active=True)
            context = {
                'categories': categories,
                'errors': errors,
                'form_data': request.POST,
                'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
            }
            return render(request, 'create_discussion.html', context)
        
        try:
            category = CommunicationCategory.objects.get(id=category_id)
            
            DiscussionThread.objects.create(
                title=title,
                content=content,
                author=request.user,
                category=category
            )
            
            messages.success(request, 'Discussion thread created successfully!')
            return redirect('discussion_list')
            
        except Exception as e:
            messages.error(request, f'Error creating discussion: {str(e)}')
            return redirect('create_discussion')
    
    else:
        # GET request - show empty form
        categories = CommunicationCategory.objects.filter(is_active=True)
        
        context = {
            'categories': categories,
            'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
        }
        return render(request, 'create_discussion.html', context)


@login_required
def notification_preferences(request):
    """
    View to manage notification preferences
    """
    try:
        preferences = UserNotificationPreference.objects.get(user=request.user)
    except UserNotificationPreference.DoesNotExist:
        preferences = UserNotificationPreference.objects.create(user=request.user)
    
    if request.method == 'POST':
        # Update email preferences
        preferences.email_announcements = request.POST.get('email_announcements') == 'on'
        preferences.email_messages = request.POST.get('email_messages') == 'on'
        preferences.email_thread_replies = request.POST.get('email_thread_replies') == 'on'
        preferences.email_mentions = request.POST.get('email_mentions') == 'on'
        
        # Update push preferences
        preferences.push_announcements = request.POST.get('push_announcements') == 'on'
        preferences.push_messages = request.POST.get('push_messages') == 'on'
        preferences.push_thread_replies = request.POST.get('push_thread_replies') == 'on'
        
        # Update in-app preferences
        preferences.in_app_announcements = request.POST.get('in_app_announcements') == 'on'
        preferences.in_app_messages = request.POST.get('in_app_messages') == 'on'
        preferences.in_app_thread_replies = request.POST.get('in_app_thread_replies') == 'on'
        
        # Update frequency
        preferences.email_digest_frequency = request.POST.get('email_digest_frequency', 'immediate')
        
        preferences.save()
        
        messages.success(request, 'Notification preferences updated successfully!')
        return redirect('notification_preferences')
    
    context = {
        'preferences': preferences,
        'unread_notifications': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'notification_preferences.html', context)