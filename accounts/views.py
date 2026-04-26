from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import CustomUser

PLAYER_EMAIL_DOMAIN = '@mail.aub.edu'
STAFF_EMAIL_DOMAIN = '@aub.edu.lb'   # shared by coaches and managers


def _role_label(role):
    labels = {
        CustomUser.ROLE_PLAYER: 'player',
        CustomUser.ROLE_COACH: 'coach',
        CustomUser.ROLE_MANAGER: 'manager',
    }
    return labels.get(role, role)


def _expected_domain(role):
    return PLAYER_EMAIL_DOMAIN if role == CustomUser.ROLE_PLAYER else STAFF_EMAIL_DOMAIN


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    role = request.GET.get('role', CustomUser.ROLE_PLAYER)
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '').strip()
        role = request.POST.get('role', CustomUser.ROLE_PLAYER)
        remember = request.POST.get('remember_me')
        expected_domain = _expected_domain(role)

        if not email:
            messages.error(request, 'Please enter your AUB email address.')
            return render(request, 'accounts/login.html', {'role': role})
        if '@' not in email:
            messages.error(request, 'Login requires your AUB email address, not just the username.')
            return render(request, 'accounts/login.html', {'role': role})
        if not email.endswith(expected_domain):
            messages.error(
                request,
                f'Please use your {_role_label(role)} AUB email address ending in {expected_domain}.',
            )
            return render(request, 'accounts/login.html', {'role': role})

        account = CustomUser.objects.filter(email__iexact=email).first()
        if account is None:
            messages.error(request, 'Invalid email or password. Please try again.')
            return render(request, 'accounts/login.html', {'role': role})

        user = authenticate(request, username=account.username, password=password)
        if user is not None:
            if user.role != role:
                messages.error(
                    request,
                    f"This account is registered as {user.get_role_display().lower()}. "
                    f"Please use the {user.get_role_display().lower()} login tab.",
                )
                return render(request, 'accounts/login.html', {'role': role})
            login(request, user)
            if not remember:
                request.session.set_expiry(0)
            return redirect('dashboard')
        messages.error(request, 'Invalid email or password. Please try again.')
    return render(request, 'accounts/login.html', {'role': role})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    role = request.GET.get('role', CustomUser.ROLE_PLAYER)
    if request.method == 'POST':
        password1  = request.POST.get('password1', '')
        password2  = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        email      = request.POST.get('email', '').strip().lower()
        role       = request.POST.get('role', CustomUser.ROLE_PLAYER)
        base_username = email.split('@')[0] if '@' in email else ''
        expected = _expected_domain(role)

        if not first_name or not last_name or not email:
            messages.error(request, 'First name, last name, and AUB email are required.')
        elif not email.endswith(expected):
            messages.error(
                request,
                f'Please use your {_role_label(role)} AUB email address ending in {expected}.',
            )
        elif CustomUser.objects.filter(email__iexact=email).exists():
            messages.error(request, 'An account with this email already exists.')
        elif len(password1) < 6:
            messages.error(request, 'Password must be at least 6 characters.')
        elif password1 != password2:
            messages.error(request, 'Passwords do not match.')
        else:
            # Build a unique username: try base_username, then base_username2, base_username3 …
            username = base_username
            counter = 2
            while CustomUser.objects.filter(username=username).exists():
                username = f'{base_username}{counter}'
                counter += 1
            user = CustomUser.objects.create_user(
                username=username, password=password1,
                first_name=first_name, last_name=last_name,
                email=email, role=role,
            )
            login(request, user)
            return redirect('dashboard')

    return render(request, 'accounts/signup.html', {
        'role': role,
        'post': request.POST,
    })


def logout_view(request):
    logout(request)
    return redirect('login')
