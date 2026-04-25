"""
Create a platform user quickly.
Usage:
  python manage.py create_user --username bh01 --password secret --role student --first Bahaa --last Hamdan
  python manage.py create_user --username coach1 --password secret --role coach --first Ali --last Moukallid
"""
from django.core.management.base import BaseCommand, CommandError
from accounts.models import CustomUser

class Command(BaseCommand):
    help = 'Create a new platform user (player or coach)'

    def add_arguments(self, parser):
        parser.add_argument('--username',  required=True)
        parser.add_argument('--password',  required=True)
        parser.add_argument('--role',      default='student', choices=['student','coach'])
        parser.add_argument('--first',     default='')
        parser.add_argument('--last',      default='')
        parser.add_argument('--email',     default='')

    def handle(self, *args, **opts):
        username = opts['username']
        if CustomUser.objects.filter(username=username).exists():
            raise CommandError(f'User "{username}" already exists.')

        user = CustomUser.objects.create_user(
            username   = username,
            password   = opts['password'],
            role       = opts['role'],
            first_name = opts['first'],
            last_name  = opts['last'],
            email      = opts['email'],
        )
        if opts['role'] == 'coach':
            user.is_staff = True
            user.save()

        self.stdout.write(self.style.SUCCESS(
            f'\n✅ User created!\n'
            f'   Username : {username}\n'
            f'   Password : {opts["password"]}\n'
            f'   Role     : {opts["role"]}\n'
            f'   Name     : {opts["first"]} {opts["last"]}\n'
        ))
