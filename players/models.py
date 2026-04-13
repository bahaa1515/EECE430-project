from django.db import models
from django.db.models import Count, Q

class Player(models.Model):
    MAX_STARTERS = 6
    POSITION_CHOICES = [
        ('OH', 'Outside Hitter'),
        ('OPP', 'Opposite Hitter'),
        ('S', 'Setter'),
        ('MB', 'Middle Blocker'),
        ('L', 'Libero'),
        ('DS', 'Defensive Specialist'),
    ]
    TYPE_STARTING = 'Starting'
    TYPE_SUBSTITUTE = 'Substitute'
    TYPE_CHOICES = [(TYPE_STARTING,'Starting'),(TYPE_SUBSTITUTE,'Substitute')]

    user = models.OneToOneField('accounts.CustomUser', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100)
    jersey_number = models.PositiveSmallIntegerField()
    position = models.CharField(max_length=5, choices=POSITION_CHOICES)
    player_type = models.CharField(max_length=15, choices=TYPE_CHOICES, default=TYPE_STARTING)
    photo = models.ImageField(upload_to='players/', blank=True, null=True)
    points = models.PositiveIntegerField(default=0)
    kills = models.PositiveIntegerField(default=0)
    blocks = models.PositiveIntegerField(default=0)
    aces = models.PositiveIntegerField(default=0)
    digs = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    attack_pct = models.PositiveSmallIntegerField(default=0)
    perfect_recv_pct = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['player_type', 'jersey_number', 'name']

    def __str__(self):
        return f"#{self.jersey_number} {self.name} ({self.get_position_display()})"

    def get_position_short(self):
        return self.position

    @classmethod
    def active_starters(cls):
        return cls.objects.filter(
            player_type=cls.TYPE_STARTING,
            is_active=True,
        )

    @property
    def attendance_summary(self):
        if not self.user_id:
            return None

        from attendance.models import AttendanceRecord

        return AttendanceRecord.objects.filter(player=self.user).aggregate(
            total=Count(
                "id",
                filter=Q(
                    official_status__in=[
                        AttendanceRecord.OFFICIAL_PRESENT,
                        AttendanceRecord.OFFICIAL_ABSENT,
                        AttendanceRecord.OFFICIAL_LATE,
                    ]
                ),
            ),
            attending=Count(
                "id",
                filter=Q(
                    official_status__in=[
                        AttendanceRecord.OFFICIAL_PRESENT,
                        AttendanceRecord.OFFICIAL_LATE,
                    ]
                ),
            ),
            missed=Count("id", filter=Q(official_status=AttendanceRecord.OFFICIAL_ABSENT)),
            pending=Count("id", filter=Q(official_status=AttendanceRecord.OFFICIAL_PENDING)),
            excused=Count("id", filter=Q(official_status=AttendanceRecord.OFFICIAL_EXCUSED)),
        )

    @property
    def attendance_percentage(self):
        summary = self.attendance_summary
        if not summary or not summary["total"]:
            return None
        return round((summary["attending"] / summary["total"]) * 100)
