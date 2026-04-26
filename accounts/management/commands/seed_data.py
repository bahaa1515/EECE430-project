"""
Management command to seed the database with demo data.
Run: python manage.py seed_data
"""
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Seeds the database with demo data matching the current UI"

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding database...")

        from accounts.models import CustomUser
        from attendance.models import AttendanceRecord, Match
        from highlights.models import MVP, MatchHighlight
        from notifications.models import Notification, NotificationRecipient
        from notifications.services import create_notification
        from players.models import Player
        from statistics_app.models import PlayerStat, TeamStat

        coach, _ = CustomUser.objects.get_or_create(username="coach")
        coach.set_password("coach123")
        coach.first_name = "Bahaa"
        coach.last_name = "Hamdan"
        coach.email = "bh00@aub.edu.lb"
        coach.role = "coach"
        coach.is_staff = True
        coach.is_superuser = True
        coach.save()

        student, _ = CustomUser.objects.get_or_create(username="student")
        student.set_password("student123")
        student.first_name = "Bahaa"
        student.last_name = "Hamdan"
        student.email = "bh01@mail.aub.edu"
        student.role = "player"
        student.save()

        extra_users = []
        for first_name, last_name in [
            ("Fadi", "Nassar"),
            ("Hadi", "Sleiman"),
            ("Rami", "Khoury"),
            ("Samer", "Akkawi"),
            ("Samir", "Haddad"),
            ("Jad", "Moussa"),
        ]:
            user, _ = CustomUser.objects.get_or_create(username=first_name.lower())
            user.set_password("pass123")
            user.first_name = first_name
            user.last_name = last_name
            user.email = f"{first_name.lower()}@mail.aub.edu"
            user.role = "player"
            user.save()
            extra_users.append(user)

        NotificationRecipient.objects.all().delete()
        Notification.objects.all().delete()
        notification_specs = [
            ("Training time changed to 6:30 PM (Main Gym)", "", "View", False),
            ('Coach posted: "Match prep meeting tomorrow at 12:00."', "", "View", False),
            ("Please confirm availability for Match vs LAU (Sat 4:00 PM)", "", "Confirm", True),
            ("Match result uploaded: AUB 3-1 NDU", "", "View", False),
            ("New highlights added for AUB vs NDU", "", "View", True),
            ("Player of the Match: Jean M. (12 kills, 4 blocks)", "", "View", True),
            ("Practice cancelled tomorrow due to facility maintenance", "", "View", False),
            ("New season schedule posted", "", "View", True),
            ("Team photo session Saturday 2:00 PM", "", "Confirm", False),
        ]
        all_users = CustomUser.objects.filter(is_active=True)
        now = timezone.now()
        for index, (title, description, action, is_read) in enumerate(notification_specs):
            notification = create_notification(
                title=title,
                description=description,
                action=action,
                created_by=coach,
                target_url="/notifications/",
                recipients=all_users,
            )
            notification.created_at = now - timedelta(hours=index * 3)
            notification.save(update_fields=["created_at"])
            NotificationRecipient.objects.filter(notification=notification).update(
                is_read=is_read,
                read_at=(notification.created_at if is_read else None),
            )

        AttendanceRecord.objects.all().delete()
        Match.objects.all().delete()
        matches_data = [
            ("AUB vs LAU", "Match", 0, 2, "NDU"),
            ("Practice", "Practice", 2, 1, "Charles Hostler"),
            ("AUB vs NDU", "Match", 4, 2, "NDU"),
            ("Practice", "Practice", 6, 2, "Charles Hostler"),
            ("Practice", "Practice", 8, 1, "Charles Hostler"),
            ("Practice", "Practice", 10, 2, "NDU"),
        ]
        created_matches = []
        for title, match_type, day_offset, duration, location in matches_data:
            match = Match.objects.create(
                title=title,
                match_type=match_type,
                status=Match.STATUS_UPCOMING,
                date=timezone.now() + timedelta(days=day_offset),
                duration_hours=duration,
                location=location,
                coach=coach,
                confirmation_closes=timezone.now() + timedelta(hours=10 + day_offset),
            )
            created_matches.append(match)

        student_responses = [
            AttendanceRecord.RESPONSE_NO_RESPONSE,
            AttendanceRecord.RESPONSE_AVAILABLE,
            AttendanceRecord.RESPONSE_UNAVAILABLE,
            AttendanceRecord.RESPONSE_AVAILABLE,
            AttendanceRecord.RESPONSE_AVAILABLE,
            AttendanceRecord.RESPONSE_NO_RESPONSE,
        ]
        for match, response in zip(created_matches, student_responses):
            AttendanceRecord.objects.get_or_create(
                match=match,
                player=student,
                defaults={
                    "response": response,
                    "official_status": AttendanceRecord.OFFICIAL_PENDING,
                },
            )

        for index in range(20):
            historical_match = Match.objects.create(
                title=f"Practice #{index + 1}",
                match_type=Match.TYPE_PRACTICE,
                status=Match.STATUS_COMPLETED,
                date=timezone.now() - timedelta(days=index * 3 + 5),
                duration_hours=2,
                location="Charles Hostler",
                coach=coach,
            )
            official_status = (
                AttendanceRecord.OFFICIAL_PRESENT
                if index % 3 != 0
                else AttendanceRecord.OFFICIAL_ABSENT
            )
            AttendanceRecord.objects.get_or_create(
                match=historical_match,
                player=student,
                defaults={
                    "response": (
                        AttendanceRecord.RESPONSE_AVAILABLE
                        if official_status == AttendanceRecord.OFFICIAL_PRESENT
                        else AttendanceRecord.RESPONSE_UNAVAILABLE
                    ),
                    "official_status": official_status,
                },
            )

        for match in created_matches[:4]:
            for player_user in extra_users[:4]:
                AttendanceRecord.objects.get_or_create(
                    match=match,
                    player=player_user,
                    defaults={
                        "response": (
                            AttendanceRecord.RESPONSE_AVAILABLE
                            if player_user.id % 2 == 0
                            else AttendanceRecord.RESPONSE_NO_RESPONSE
                        ),
                        "official_status": AttendanceRecord.OFFICIAL_PENDING,
                    },
                )
            for player_user in extra_users[4:]:
                AttendanceRecord.objects.get_or_create(
                    match=match,
                    player=player_user,
                    defaults={
                        "response": AttendanceRecord.RESPONSE_UNAVAILABLE,
                        "official_status": AttendanceRecord.OFFICIAL_PENDING,
                    },
                )

        Player.objects.all().delete()
        starting_players = [
            ("Oussama Kharma", 8, "OPP", 88, 234, 58, 21, 39, 0, 0, 0),
            ("Karim Hallab", 14, "L", 81, 0, 0, 15, 0, 389, 48, 0),
            ("Giuseppe Abboud", 12, "S", 86, 0, 0, 20, 0, 0, 0, 705),
            ("Omar Khoury", 7, "OH", 75, 275, 30, 28, 46, 0, 0, 0),
            ("Karim Sinno", 11, "OH", 78, 202, 28, 14, 39, 0, 0, 0),
            ("Bassel Haidar", 13, "OPP", 71, 214, 33, 18, 44, 0, 0, 0),
        ]
        for name, jersey, position, points, kills, blocks, aces, attack_pct, digs, recv_pct, assists in starting_players:
            Player.objects.create(
                name=name,
                jersey_number=jersey,
                position=position,
                player_type=Player.TYPE_STARTING,
                points=points,
                kills=kills,
                blocks=blocks,
                aces=aces,
                attack_pct=attack_pct,
                digs=digs,
                perfect_recv_pct=recv_pct,
                assists=assists,
            )

        substitute_players = [
            ("Michael Ghosn", 5, "OH", 64, 120, 20, 10, 35, 0, 0, 0),
            ("Jad Houry", 9, "MB", 57, 98, 45, 8, 28, 0, 0, 0),
            ("Nour Kassoha", 15, "DS", 75, 80, 12, 18, 30, 0, 0, 0),
        ]
        for name, jersey, position, points, kills, blocks, aces, attack_pct, digs, recv_pct, assists in substitute_players:
            Player.objects.create(
                name=name,
                jersey_number=jersey,
                position=position,
                player_type=Player.TYPE_SUBSTITUTE,
                points=points,
                kills=kills,
                blocks=blocks,
                aces=aces,
                attack_pct=attack_pct,
                digs=digs,
                perfect_recv_pct=recv_pct,
                assists=assists,
            )

        PlayerStat.objects.all().delete()
        karim_sinno = Player.objects.get(name="Karim Sinno")
        recent_matches = [
            (date(2024, 4, 5), "LAU", 26, 2, 2),
            (date(2024, 3, 28), "USJ", 22, 3, 4),
            (date(2024, 3, 25), "UQB", 20, 4, 0),
            (date(2024, 3, 19), "ESA", 17, 1, 2),
        ]
        for match_date, opponent, kills, blocks, aces in recent_matches:
            PlayerStat.objects.create(
                player=karim_sinno,
                date=match_date,
                opponent=opponent,
                kills=kills,
                blocks=blocks,
                aces=aces,
            )

        TeamStat.objects.all().delete()
        TeamStat.objects.create(
            season="2024-2025",
            home_played=30,
            home_wins=22,
            home_losses=8,
            away_played=10,
            away_wins=8,
            away_losses=2,
            attack_efficiency_made=30,
            attack_efficiency_total=36,
            block_success_rate=38,
            serve_efficiency_made=15,
            serve_efficiency_total=22,
            reception_accuracy_made=23,
            reception_accuracy_total=30,
            side_out_made=23,
            side_out_total=38,
            comeback_rate=27,
        )

        MatchHighlight.objects.all().delete()
        MVP.objects.all().delete()
        highlight = MatchHighlight.objects.create(
            session=created_matches[0] if created_matches else None,
            title="AUB Varsity vs LAU Falcons",
            score="3 - 2",
            summary=(
                "AUB secured a decisive victory with strong offensive execution and disciplined "
                "defense. The team closed the match 3-2 after a high-intensity final set."
            ),
        )
        karim_player = Player.objects.filter(name__icontains="Karim").first()
        if karim_player:
            MVP.objects.create(
                player=karim_player,
                session=created_matches[0] if created_matches else None,
                match=highlight,
                points=198,
                points_per_match=16.5,
                attack_success_rate=54,
                blocks=38,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "\nDatabase seeded successfully!\n"
                "Coach login: email=bh00@aub.edu.lb password=coach123\n"
                "Player login: email=bh01@mail.aub.edu password=student123\n"
                "Admin panel: http://127.0.0.1:8000/admin/\n"
            )
        )
