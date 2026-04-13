from django.db import models

class MatchHighlight(models.Model):
    session = models.ForeignKey(
        'attendance.Match',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='featured_highlights',
    )
    title = models.CharField(max_length=200)
    score = models.CharField(max_length=20, blank=True, help_text="e.g. 3-2")
    summary = models.TextField()
    image = models.ImageField(upload_to='highlights/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self): return self.title

class MVP(models.Model):
    player = models.ForeignKey('players.Player', on_delete=models.CASCADE)
    session = models.ForeignKey(
        'attendance.Match',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='featured_mvps',
    )
    match = models.ForeignKey(MatchHighlight, on_delete=models.CASCADE, null=True, blank=True)
    points = models.IntegerField(default=0)
    points_per_match = models.FloatField(default=0)
    attack_success_rate = models.IntegerField(default=0)
    blocks = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self): return f"MVP: {self.player.name}"
