from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("attendance", "0003_attendancerecord_official_status_and_response"),
        ("highlights", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="matchhighlight",
            name="session",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="featured_highlights",
                to="attendance.match",
            ),
        ),
        migrations.AddField(
            model_name="mvp",
            name="session",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="featured_mvps",
                to="attendance.match",
            ),
        ),
    ]
