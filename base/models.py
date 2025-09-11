from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.validators import RegexValidator

class User(AbstractUser):
    """
    Custom User model with extended fields and proper authentication handling.
    """
    
    # User type choices
    USER_TYPE_CHOICES = (
        ('admin', 'Administrator'),
        ('staff', 'Staff Member'),
        ('sponsor', 'Sponsor'),
        ('beneficiary', 'Beneficiary'),
    )
    
    # Make email unique and required
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )
    
    # User type field with default
    user_type = models.CharField(
        max_length=12,
        choices=USER_TYPE_CHOICES,
        default='staff',
        verbose_name=_('user type')
    )
    
    # Phone number with validation
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=20,
        blank=True,
        null=True,
        verbose_name=_('phone number')
    )
    
    # Profile picture handling
    profile_picture = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        verbose_name=_('profile picture')
    )
    
    # Email verification fields
    email_verified = models.BooleanField(
        default=False,
        verbose_name=_('email verified')
    )
    verification_token = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('verification token')
    )
    
    # Security-related fields
    last_password_reset = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('last password reset')
    )
    
    # Override groups and permissions to avoid clashes
    groups = models.ManyToManyField(
        Group,
        verbose_name=_('groups'),
        blank=True,
        help_text=_('The groups this user belongs to.'),
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name=_('user permissions'),
        blank=True,
        help_text=_('Specific permissions for this user.'),
        related_name='custom_user_set',
        related_query_name='custom_user',
    )
    
    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.email})"
    
    def save(self, *args, **kwargs):
        # Ensure username is set if not provided
        if not self.username:
            self.username = self.email
        super().save(*args, **kwargs)
    
    @property
    def is_admin(self):
        return self.user_type == 'admin' or self.is_superuser
    
    @property
    def is_staff_member(self):
        return self.user_type == 'staff' or self.is_staff
    
    @property
    def is_sponsor(self):
        return self.user_type == 'sponsor'
    
    @property
    def is_beneficiary(self):
        return self.user_type == 'beneficiary'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    id_number = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f"Profile for {self.user.username}"



class Institution(models.Model):
    INSTITUTION_TYPES = (
        ('primary', 'Primary School'),
        ('secondary', 'Secondary School'),
        ('college', 'College'),
        ('university', 'University'),
        ('vocational', 'Vocational Training'),
    )
    
    name = models.CharField(max_length=200)
    institution_type = models.CharField(max_length=20, choices=INSTITUTION_TYPES)
    location = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    partnership_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class Beneficiary(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )
    
    LEVEL_CHOICES = (
        ('primary', 'Primary'),
        ('secondary', 'Secondary'),
        ('college', 'College'),
        ('university', 'University'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    sponsor = models.ForeignKey('Sponsor', on_delete=models.SET_NULL, null=True, blank=True)
    date_of_birth = models.DateField()
    national_id = models.CharField(max_length=20, blank=True, null=True)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    current_level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True)
    enrollment_date = models.DateField()
    is_active = models.BooleanField(default=True)
    photo = models.ImageField(upload_to='beneficiaries/', blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    expected_graduation = models.DateField(blank=True, null=True)
    sponsorship_start_date = models.DateField(blank=True, null=True)
    sponsorship_end_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    previous_school = models.CharField(max_length=200, blank=True, null=True)
    current_school = models.CharField(max_length=200, blank=True, null=True)
    admission_letter = models.FileField(upload_to='beneficiary_docs/admission_letters/', blank=True, null=True)
    fee_structure = models.FileField(upload_to='beneficiary_docs/fee_structures/', blank=True, null=True)
    fee_statement = models.FileField(upload_to='beneficiary_docs/fee_statements/', blank=True, null=True)
    receipts = models.FileField(upload_to='beneficiary_docs/receipts/', blank=True, null=True)
    letters = models.FileField(upload_to='beneficiary_docs/letters/', blank=True, null=True)
    
    # Parent/Guardian details
    GUARDIAN_TYPE_CHOICES = (
        ('single_parent', 'Single Parent'),
        ('both_parents', 'Both Parents'),
        ('guardian', 'Guardian'),
    )
    guardian_type = models.CharField(max_length=20, choices=GUARDIAN_TYPE_CHOICES, blank=True, null=True)
    guardian_full_name = models.CharField(max_length=200, blank=True, null=True)
    guardian_phone = models.CharField(max_length=20, blank=True, null=True)
    guardian_id_copy = models.FileField(upload_to='beneficiary_docs/guardian_ids/', blank=True, null=True)
    guardian_email = models.EmailField(blank=True, null=True)
    
    # Residence information
    residence_address = models.TextField(blank=True, null=True)
    residence_directions = models.TextField(blank=True, null=True)
    
    # Referrals
    referral_source = models.CharField(max_length=200, blank=True, null=True)
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('graduated', 'Graduated'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def status(self):
        if not self.is_active:
            return "Inactive"
        if self.current_level == 'graduated':
            return "Graduated"
        return "Active"
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('beneficiary_detail', kwargs={'pk': self.pk})
    
    class Meta:
        verbose_name_plural = "Beneficiaries"
        ordering = ['last_name', 'first_name']

class Payment(models.Model):
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    term = models.CharField(max_length=20)
    academic_year = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    receipt_number = models.CharField(max_length=50)
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    def __str__(self):
        return f"Payment of {self.amount} for {self.beneficiary}"

class AcademicPerformance(models.Model):
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE)
    term = models.CharField(max_length=20)
    academic_year = models.CharField(max_length=10)
    average_score = models.DecimalField(max_digits=5, decimal_places=2)
    rank = models.IntegerField()
    comments = models.TextField(blank=True)
    date_recorded = models.DateField(auto_now_add=True)
    
    def __str__(self):
        return f"Performance for {self.beneficiary} - Term {self.term} {self.academic_year}"

class ActivityLog(models.Model):
    ACTIVITY_TYPES = (
        ('enrollment', 'New Enrollment'),
        ('payment', 'Payment Processed'),
        ('performance', 'Performance Update'),
        ('meeting', 'Meeting'),
        ('training', 'Training Conducted'),
        ('other', 'Other Activity'),
    )
    
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    description = models.TextField()
    date_recorded = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    related_beneficiary = models.ForeignKey(Beneficiary, on_delete=models.SET_NULL, null=True, blank=True)
    related_institution = models.ForeignKey(Institution, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.description[:50]}"

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    location = models.CharField(max_length=200)
    organizer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return f"Notification for {self.user.username}"

class Sponsor(models.Model):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    address = models.TextField()
    sponsorship_start_date = models.DateField()
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class FinancialAid(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('disbursed', 'Disbursed'),
    )
    
    TERM_CHOICES = (
        ('1', 'Term 1'),
        ('2', 'Term 2'),
        ('3', 'Term 3'),
    )
    
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name='financial_aids')
    academic_year = models.CharField(max_length=9)  # Format: 2023-2024
    term = models.CharField(max_length=1, choices=TERM_CHOICES)
    amount_requested = models.DecimalField(max_digits=10, decimal_places=2)
    amount_approved = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    request_date = models.DateField(auto_now_add=True)
    approval_date = models.DateField(null=True, blank=True)
    disbursement_date = models.DateField(null=True, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_aids')
    notes = models.TextField(blank=True)
    receipt_number = models.CharField(max_length=50, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    
    class Meta:
        ordering = ['-request_date']
        verbose_name_plural = 'Financial Aids'
    
    def __str__(self):
        return f"{self.beneficiary} - {self.get_term_display()} {self.academic_year}"
    
    def save(self, *args, **kwargs):
        # If status is being updated to approved/disbursed, set the appropriate dates
        if self.pk:
            original = FinancialAid.objects.get(pk=self.pk)
            if self.status == 'approved' and original.status != 'approved':
                self.approval_date = timezone.now().date()
            elif self.status == 'disbursed' and original.status != 'disbursed':
                self.disbursement_date = timezone.now().date()
        super().save(*args, **kwargs)

# Add to models.py

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    level = models.CharField(max_length=20, choices=Beneficiary.LEVEL_CHOICES)
    is_core = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} ({self.code})"

class SubjectPerformance(models.Model):
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE, related_name='subject_performances')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.CharField(max_length=20)
    academic_year = models.CharField(max_length=10)
    score = models.DecimalField(max_digits=5, decimal_places=2)
    grade = models.CharField(max_length=2)
    comments = models.TextField(blank=True)
    date_recorded = models.DateField(auto_now_add=True)
    
    class Meta:
        unique_together = ('beneficiary', 'subject', 'term', 'academic_year')
        ordering = ['academic_year', 'term', 'subject__name']
    
    def __str__(self):
        return f"{self.beneficiary} - {self.subject} ({self.term} {self.academic_year})"

class PerformanceReport(models.Model):
    REPORT_TYPE_CHOICES = (
        ('term', 'Term Report'),
        ('annual', 'Annual Report'),
        ('subject', 'Subject Analysis'),
        ('comparative', 'Comparative Analysis'),
    )
    
    title = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    academic_year = models.CharField(max_length=10)
    term = models.CharField(max_length=20, blank=True, null=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    report_file = models.FileField(upload_to='performance_reports/', blank=True, null=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return self.title

class AcademicPerformance(models.Model):
    beneficiary = models.ForeignKey(Beneficiary, on_delete=models.CASCADE)
    term = models.CharField(max_length=20)
    academic_year = models.CharField(max_length=10)
    average_score = models.DecimalField(max_digits=5, decimal_places=2)
    rank = models.IntegerField()
    comments = models.TextField(blank=True)
    date_recorded = models.DateField(auto_now_add=True)
    report_file = models.FileField(upload_to='performance_reports/', blank=True, null=True)

    def __str__(self):
        return f"Performance for {self.beneficiary} - Term {self.term} {self.academic_year}"


class EventType(models.Model):
    """
    Model to categorize events (Academic, Holiday, Exam, Other, etc.)
    """
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#4361ee')  # Hex color code
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Event Type'
        verbose_name_plural = 'Event Types'
    
    def __str__(self):
        return self.name


class AcademicEvent(models.Model):
    """
    Model for academic calendar events
    """
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    event_type = models.ForeignKey(EventType, on_delete=models.PROTECT, related_name='events')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    all_day = models.BooleanField(default=False)
    location = models.CharField(max_length=200, blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # For recurring events
    is_recurring = models.BooleanField(default=False)
    recurrence_pattern = models.CharField(max_length=50, blank=True, null=True)  # e.g., "FREQ=WEEKLY;INTERVAL=1"
    recurrence_end_date = models.DateTimeField(blank=True, null=True)
    
    # For event reminders
    reminder_sent = models.BooleanField(default=False)
    reminder_date = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['start_date']
        verbose_name = 'Academic Event'
        verbose_name_plural = 'Academic Events'
    
    def __str__(self):
        return f"{self.title} - {self.start_date.strftime('%Y-%m-%d')}"
    
    @property
    def is_past(self):
        return timezone.now() > self.end_date
    
    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    @property
    def duration(self):
        return self.end_date - self.start_date


class EventParticipant(models.Model):
    """
    Model to track participants for events
    """
    ROLE_CHOICES = (
        ('organizer', 'Organizer'),
        ('participant', 'Participant'),
        ('speaker', 'Speaker'),
        ('guest', 'Guest'),
    )
    
    event = models.ForeignKey(AcademicEvent, on_delete=models.CASCADE, related_name='participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_participations')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='participant')
    confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        unique_together = ('event', 'user')
        verbose_name = 'Event Participant'
        verbose_name_plural = 'Event Participants'
    
    def __str__(self):
        return f"{self.user.username} - {self.event.title}"


class EventAttachment(models.Model):
    """
    Model for event attachments (documents, images, etc.)
    """
    event = models.ForeignKey(AcademicEvent, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='event_attachments/%Y/%m/%d/')
    name = models.CharField(max_length=200)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Event Attachment'
        verbose_name_plural = 'Event Attachments'
    
    def __str__(self):
        return f"{self.name} - {self.event.title}"


class CommunicationCategory(models.Model):
    """
    Model to categorize communications (Announcements, Notifications, Alerts, etc.)
    """
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7, default='#4361ee')  # Hex color code
    icon = models.CharField(max_length=50, default='fas fa-bullhorn')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Communication Category'
        verbose_name_plural = 'Communication Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Announcement(models.Model):
    """
    Model for system announcements
    """
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )
    
    title = models.CharField(max_length=200)
    content = models.TextField()
    category = models.ForeignKey(CommunicationCategory, on_delete=models.PROTECT, related_name='announcements')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    is_published = models.BooleanField(default=False)
    publish_date = models.DateTimeField(null=True, blank=True)
    expiration_date = models.DateTimeField(null=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='authored_announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Target audience
    target_audience = models.CharField(max_length=20, choices=User.USER_TYPE_CHOICES, blank=True, null=True)
    specific_recipients = models.ManyToManyField(User, blank=True, related_name='targeted_announcements')
    
    # Read receipts
    read_by = models.ManyToManyField(User, blank=True, related_name='read_announcements')
    
    class Meta:
        ordering = ['-publish_date', '-created_at']
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'
    
    def __str__(self):
        return self.title
    
    @property
    def is_active(self):
        now = timezone.now()
        if self.publish_date and self.publish_date > now:
            return False
        if self.expiration_date and self.expiration_date < now:
            return False
        return self.is_published
    
    @property
    def read_count(self):
        return self.read_by.count()
    
    @property
    def unread_count(self):
        # This would need to be calculated based on the target audience
        return 0  # Placeholder


class Message(models.Model):
    """
    Model for user-to-user messages
    """
    STATUS_CHOICES = (
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('read', 'Read'),
        ('archived', 'Archived'),
    )
    
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    recipients = models.ManyToManyField(User, related_name='received_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    is_important = models.BooleanField(default=False)
    sent_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Attachments
    attachments = models.ManyToManyField('MessageAttachment', blank=True)
    
    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
    
    def __str__(self):
        return f"{self.subject} - {self.sender.username}"
    
    @property
    def is_read(self):
        return self.status == 'read' and self.read_at is not None
    
    def mark_as_read(self, user):
        if user in self.recipients.all() and not self.is_read:
            self.status = 'read'
            self.read_at = timezone.now()
            self.save()
            return True
        return False


class MessageAttachment(models.Model):
    """
    Model for message attachments
    """
    file = models.FileField(upload_to='message_attachments/%Y/%m/%d/')
    original_filename = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.BigIntegerField()  # Size in bytes
    
    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Message Attachment'
        verbose_name_plural = 'Message Attachments'
    
    def __str__(self):
        return self.original_filename
    
    def save(self, *args, **kwargs):
        if not self.original_filename and self.file:
            self.original_filename = self.file.name
        if not self.file_size and self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    @property
    def file_size_display(self):
        """Return human-readable file size"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        elif self.file_size < 1024 * 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        else:
            return f"{self.file_size / (1024 * 1024 * 1024):.1f} GB"


class DiscussionThread(models.Model):
    """
    Model for discussion threads (forum-like functionality)
    """
    title = models.CharField(max_length=200)
    content = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authored_threads')
    category = models.ForeignKey(CommunicationCategory, on_delete=models.PROTECT, related_name='discussion_threads')
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-is_pinned', '-updated_at']
        verbose_name = 'Discussion Thread'
        verbose_name_plural = 'Discussion Threads'
    
    def __str__(self):
        return self.title
    
    @property
    def reply_count(self):
        return self.replies.count()
    
    @property
    def last_reply(self):
        return self.replies.order_by('-created_at').first()


class DiscussionReply(models.Model):
    """
    Model for replies to discussion threads
    """
    thread = models.ForeignKey(DiscussionThread, on_delete=models.CASCADE, related_name='replies')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='forum_replies')
    content = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # For reply-to-reply functionality
    parent_reply = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='child_replies')
    
    class Meta:
        ordering = ['created_at']
        verbose_name = 'Discussion Reply'
        verbose_name_plural = 'Discussion Replies'
    
    def __str__(self):
        return f"Reply to: {self.thread.title}"


class UserNotificationPreference(models.Model):
    """
    Model for user notification preferences
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Email notifications
    email_announcements = models.BooleanField(default=True)
    email_messages = models.BooleanField(default=True)
    email_thread_replies = models.BooleanField(default=True)
    email_mentions = models.BooleanField(default=True)
    
    # Push notifications
    push_announcements = models.BooleanField(default=True)
    push_messages = models.BooleanField(default=True)
    push_thread_replies = models.BooleanField(default=True)
    
    # In-app notifications
    in_app_announcements = models.BooleanField(default=True)
    in_app_messages = models.BooleanField(default=True)
    in_app_thread_replies = models.BooleanField(default=True)
    
    # Frequency
    email_digest_frequency = models.CharField(max_length=20, choices=(
        ('immediate', 'Immediate'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
    ), default='immediate')
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Notification Preference'
        verbose_name_plural = 'User Notification Preferences'
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"