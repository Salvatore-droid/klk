from django.urls import path
from . import views



urlpatterns = [
    
    path('', views.dashboard, name='dashboard'),
    path('api/beneficiary-distribution/', views.get_beneficiary_distribution, name='beneficiary_distribution'),
    path('api/performance-trends/', views.get_performance_trends, name='performance_trends'),
    path('beneficiaries/', views.beneficiaries_list, name='beneficiaries_list'),
    path('beneficiaries/add/', views.add_beneficiary, name='add_beneficiary'),
    path('beneficiaries/<int:pk>/', views.beneficiary_detail, name='beneficiary_detail'),
    path('beneficiaries/<int:pk>/edit/', views.edit_beneficiary, name='edit_beneficiary'),
    path('beneficiaries/<int:pk>/delete/', views.delete_beneficiary, name='delete_beneficiary'),
    path('accounts/login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    
    path('financial/', views.financial_dashboard, name='financial_dashboard'),
    path('financial/aid/', views.financial_aid_list, name='financial_aid_list'),
    path('financial/aid/add/', views.add_financial_aid, name='add_financial_aid'),
    path('financial/aid/<int:pk>/', views.financial_aid_detail, name='financial_aid_detail'),
    path('financial/aid/<int:pk>/update-status/', views.update_financial_aid_status, name='update_financial_aid_status'),
    path('financial/reports/', views.financial_reports, name='financial_reports'),


    path('performance/', views.performance_dashboard, name='performance_dashboard'),
    path('performance/api/', views.performance_data_api, name='performance_data_api'),
    path('performance/export/', views.export_performance_report, name='export_performance_report'),
    path('performance/add/', views.add_performance, name='add_performance'),
    path('performance/detail/<int:pk>/', views.performance_detail, name='performance_detail'),
    path('performance/edit/<int:pk>/', views.edit_performance, name='edit_performance'),
    path('performance/delete/<int:pk>/', views.delete_performance, name='delete_performance'),
    path('performance/note/<int:pk>/', views.add_performance_note, name='add_performance_note'),


    path('calendar/', views.academic_calendar, name='academic_calendar'),
    path('calendar/events/', views.calendar_events_api, name='calendar_events_api'),
    path('calendar/event/add/', views.add_event, name='add_event'),
    path('calendar/event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('calendar/event/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('calendar/event/<int:event_id>/delete/', views.delete_event, name='delete_event'),
    path('calendar/event/<int:event_id>/join/', views.join_event, name='join_event'),
    path('calendar/event/<int:event_id>/leave/', views.leave_event, name='leave_event'),

    path('communication/', views.communication_dashboard, name='communication'),
    path('communication/announcements/', views.announcement_list, name='announcement_list'),
    path('communication/announcements/<int:announcement_id>/', views.announcement_detail, name='announcement_detail'),
    path('communication/messages/', views.message_inbox, name='message_inbox'),
    path('communication/messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('communication/messages/send/', views.send_message, name='send_message'),
    path('communication/discussions/', views.discussion_list, name='discussion_list'),
    path('communication/discussions/<int:thread_id>/', views.discussion_detail, name='discussion_detail'),
    path('communication/discussions/create/', views.create_discussion, name='create_discussion'),
    path('communication/notifications/preferences/', views.notification_preferences, name='notification_preferences'),
]