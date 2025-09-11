# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

class CustomUserAdmin(UserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

class BeneficiaryAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'current_level', 'institution', 'sponsor', 'status', 'current_school')
    list_filter = ('current_level', 'institution', 'sponsor', 'is_active', 'guardian_type')
    search_fields = ('first_name', 'last_name', 'national_id', 'current_school', 'previous_school', 'guardian_full_name')
    raw_id_fields = ('user',)
    date_hierarchy = 'enrollment_date'
    ordering = ('last_name', 'first_name')

class SponsorAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'contact_email', 'is_active')
    search_fields = ('name', 'contact_person', 'contact_email')
    list_filter = ('is_active',)

class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution_type', 'location', 'is_active')
    list_filter = ('institution_type', 'is_active')
    search_fields = ('name', 'location')

class PaymentAdmin(admin.ModelAdmin):
    list_display = ('beneficiary', 'amount', 'payment_date', 'academic_year', 'term')
    list_filter = ('academic_year', 'term')
    search_fields = ('beneficiary__first_name', 'beneficiary__last_name', 'receipt_number')
    date_hierarchy = 'payment_date'

# Unregister the default User admin and register our custom one

admin.site.register(User, CustomUserAdmin)

# Register other models
admin.site.register(UserProfile)
admin.site.register(Institution, InstitutionAdmin)
admin.site.register(Beneficiary, BeneficiaryAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(AcademicPerformance)
admin.site.register(ActivityLog)
admin.site.register(Event)
admin.site.register(Subject)
admin.site.register(Notification)
admin.site.register(Sponsor, SponsorAdmin)
from django.contrib import admin
from .models import EventType, AcademicEvent, EventParticipant, EventAttachment

@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(AcademicEvent)
class AcademicEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_date', 'end_date', 'is_active')
    list_filter = ('event_type', 'priority', 'is_active', 'start_date')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_date'
    filter_horizontal = ()
    readonly_fields = ('created_by', 'created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(EventParticipant)
class EventParticipantAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'role', 'confirmed')
    list_filter = ('role', 'confirmed')
    search_fields = ('event__title', 'user__username')

@admin.register(EventAttachment)
class EventAttachmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('name', 'event__title')


from django.contrib import admin
from .models import (
    CommunicationCategory, Announcement, Message, MessageAttachment,
    DiscussionThread, DiscussionReply, UserNotificationPreference
)

@admin.register(CommunicationCategory)
class CommunicationCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'icon', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'priority', 'is_published', 'publish_date', 'author')
    list_filter = ('category', 'priority', 'is_published', 'publish_date')
    search_fields = ('title', 'content')
    filter_horizontal = ('specific_recipients', 'read_by')
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not obj.author_id:
            obj.author = request.user
        super().save_model(request, obj, form, change)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'sender', 'status', 'is_important', 'sent_at')
    list_filter = ('status', 'is_important', 'sent_at')
    search_fields = ('subject', 'body', 'sender__username')
    filter_horizontal = ('recipients', 'attachments')
    readonly_fields = ('sent_at', 'read_at')

@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ('original_filename', 'uploaded_by', 'uploaded_at', 'file_size_display')
    list_filter = ('uploaded_at',)
    search_fields = ('original_filename', 'uploaded_by__username')
    readonly_fields = ('uploaded_at', 'file_size')

@admin.register(DiscussionThread)
class DiscussionThreadAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'is_pinned', 'is_locked', 'created_at', 'reply_count')
    list_filter = ('category', 'is_pinned', 'is_locked', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('created_at', 'updated_at', 'views')

@admin.register(DiscussionReply)
class DiscussionReplyAdmin(admin.ModelAdmin):
    list_display = ('thread', 'author', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('content', 'thread__title', 'author__username')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(UserNotificationPreference)
class UserNotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_digest_frequency', 'updated_at')
    list_filter = ('email_digest_frequency',)
    search_fields = ('user__username',)
    readonly_fields = ('updated_at',)