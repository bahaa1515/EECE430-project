from django.db import migrations, models


def rename_student_to_player(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')
    CustomUser.objects.filter(role='student').update(role='player')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='role',
            field=models.CharField(
                choices=[('player', 'Player'), ('coach', 'Coach'), ('manager', 'Manager')],
                default='player',
                max_length=10,
            ),
        ),
        migrations.RunPython(rename_student_to_player, migrations.RunPython.noop),
    ]