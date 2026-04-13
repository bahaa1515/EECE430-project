from django.db import migrations, models


def split_old_status_into_response_and_official(apps, schema_editor):
    AttendanceRecord = apps.get_model('attendance', 'AttendanceRecord')
    for record in AttendanceRecord.objects.all():
        old_status = record.status
        if old_status == 'Attending':
            record.response = 'Available'
            record.official_status = 'Present'
        elif old_status == 'Not Attending':
            record.response = 'Unavailable'
            record.official_status = 'Absent'
        else:
            record.response = 'No Response'
            record.official_status = 'Pending Review'
        record.save(update_fields=['response', 'official_status'])


def merge_split_fields_back_to_status(apps, schema_editor):
    AttendanceRecord = apps.get_model('attendance', 'AttendanceRecord')
    for record in AttendanceRecord.objects.all():
        if record.official_status in {'Present', 'Late'}:
            record.status = 'Attending'
        elif record.official_status == 'Absent':
            record.status = 'Not Attending'
        else:
            if record.response == 'Available':
                record.status = 'Attending'
            elif record.response == 'Unavailable':
                record.status = 'Not Attending'
            else:
                record.status = 'Pending'
        record.save(update_fields=['status'])


class Migration(migrations.Migration):

    dependencies = [
        ('attendance', '0002_match_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='attendancerecord',
            name='official_status',
            field=models.CharField(
                choices=[
                    ('Present', 'Present'),
                    ('Absent', 'Absent'),
                    ('Excused', 'Excused'),
                    ('Late', 'Late'),
                    ('Pending Review', 'Pending Review'),
                ],
                default='Pending Review',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='attendancerecord',
            name='response',
            field=models.CharField(
                choices=[
                    ('Available', 'Available'),
                    ('Unavailable', 'Unavailable'),
                    ('No Response', 'No Response'),
                ],
                default='No Response',
                max_length=20,
            ),
        ),
        migrations.RunPython(split_old_status_into_response_and_official, merge_split_fields_back_to_status),
        migrations.RemoveField(
            model_name='attendancerecord',
            name='status',
        ),
    ]
