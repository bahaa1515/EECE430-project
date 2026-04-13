from django.db import models

class TeamStat(models.Model):
    season = models.CharField(max_length=20, default='2024-2025')
    home_played = models.IntegerField(default=0)
    home_wins   = models.IntegerField(default=0)
    home_losses = models.IntegerField(default=0)
    away_played = models.IntegerField(default=0)
    away_wins   = models.IntegerField(default=0)
    away_losses = models.IntegerField(default=0)
    attack_efficiency_made    = models.IntegerField(default=0)
    attack_efficiency_total   = models.IntegerField(default=0)
    block_success_rate        = models.IntegerField(default=0)
    serve_efficiency_made     = models.IntegerField(default=0)
    serve_efficiency_total    = models.IntegerField(default=0)
    reception_accuracy_made   = models.IntegerField(default=0)
    reception_accuracy_total  = models.IntegerField(default=0)
    side_out_made             = models.IntegerField(default=0)
    side_out_total            = models.IntegerField(default=0)
    comeback_rate             = models.IntegerField(default=0)

    @property
    def total_played(self):  return self.home_played + self.away_played
    @property
    def total_wins(self):    return self.home_wins + self.away_wins
    @property
    def total_losses(self):  return self.home_losses + self.away_losses

    # Win %
    @property
    def home_win_pct(self):
        return round(self.home_wins / self.home_played * 100, 2) if self.home_played else 0
    @property
    def away_win_pct(self):
        return round(self.away_wins / self.away_played * 100, 2) if self.away_played else 0
    @property
    def total_win_pct(self):
        return round(self.total_wins / self.total_played * 100, 2) if self.total_played else 0

    # Loss % — losses divided by games played, NOT wins+losses
    @property
    def home_loss_pct(self):
        return round(self.home_losses / self.home_played * 100, 2) if self.home_played else 0
    @property
    def away_loss_pct(self):
        return round(self.away_losses / self.away_played * 100, 2) if self.away_played else 0
    @property
    def total_loss_pct(self):
        return round(self.total_losses / self.total_played * 100, 2) if self.total_played else 0

    def __str__(self): return f"Team Stats {self.season}"

class PlayerStat(models.Model):
    player   = models.ForeignKey('players.Player', on_delete=models.CASCADE, related_name='match_stats')
    date     = models.DateField()
    opponent = models.CharField(max_length=100)
    kills    = models.IntegerField(default=0)
    blocks   = models.IntegerField(default=0)
    aces     = models.IntegerField(default=0)
    mvp      = models.BooleanField(default=False)

    class Meta:
        ordering = ['-date']

    def __str__(self): return f"{self.player.name} vs {self.opponent} ({self.date})"
