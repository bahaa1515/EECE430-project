from django.db import models
from django.utils import timezone

class Match(models.Model):
    TYPE_MATCH = 'Match'
    TYPE_PRACTICE = 'Practice'
    TYPE_CHOICES = [(TYPE_MATCH,'Match'),(TYPE_PRACTICE,'Practice')]

    STATUS_UPCOMING = 'Upcoming'
    STATUS_COMPLETED = 'Completed'
    STATUS_CANCELLED = 'Cancelled'
    STATUS_POSTPONED = 'Postponed'
    STATUS_CHOICES = [
        (STATUS_UPCOMING, 'Upcoming'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_POSTPONED, 'Postponed'),
    ]

    title = models.CharField(max_length=200)
    match_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_MATCH)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UPCOMING)
    date = models.DateTimeField()
    duration_hours = models.PositiveSmallIntegerField(default=2)
    location = models.CharField(max_length=200, default='Charles Hostler')
    coach = models.ForeignKey('accounts.CustomUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='coached_matches')
    confirmation_closes = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['date']

    def __str__(self):
        return self.title

class AttendanceRecord(models.Model):
    RESPONSE_AVAILABLE = 'Available'
    RESPONSE_UNAVAILABLE = 'Unavailable'
    RESPONSE_NO_RESPONSE = 'No Response'
    RESPONSE_CHOICES = [
        (RESPONSE_AVAILABLE, 'Available'),
        (RESPONSE_UNAVAILABLE, 'Unavailable'),
        (RESPONSE_NO_RESPONSE, 'No Response'),
    ]

    OFFICIAL_PRESENT = 'Present'
    OFFICIAL_ABSENT = 'Absent'
    OFFICIAL_EXCUSED = 'Excused'
    OFFICIAL_LATE = 'Late'
    OFFICIAL_PENDING = 'Pending Review'
    OFFICIAL_STATUS_CHOICES = [
        (OFFICIAL_PRESENT, 'Present'),
        (OFFICIAL_ABSENT, 'Absent'),
        (OFFICIAL_EXCUSED, 'Excused'),
        (OFFICIAL_LATE, 'Late'),
        (OFFICIAL_PENDING, 'Pending Review'),
    ]

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='records')
    player = models.ForeignKey('accounts.CustomUser', on_delete=models.CASCADE, related_name='attendance_records')
    response = models.CharField(max_length=20, choices=RESPONSE_CHOICES, default=RESPONSE_NO_RESPONSE)
    official_status = models.CharField(max_length=20, choices=OFFICIAL_STATUS_CHOICES, default=OFFICIAL_PENDING)

    class Meta:
        unique_together = ['match', 'player']

    def __str__(self):
        return f"{self.player.get_full_name()} - {self.match.title}: {self.official_status}"

    @property
    def counts_as_present(self):
        return self.official_status in {self.OFFICIAL_PRESENT, self.OFFICIAL_LATE}

    @property
    def counts_as_absent(self):
        return self.official_status == self.OFFICIAL_ABSENT

    @property
    def is_excused(self):
        return self.official_status == self.OFFICIAL_EXCUSED
