from django.shortcuts import render, redirect
from django.contrib import messages
from django.db.models import Sum
from datetime import datetime
from decimal import Decimal
from pytz import timezone
import pytz
import bcrypt
from .models import User
from .models import Shift
from .models import Quote
from .models import Email

def admin_home(request):
    now = datetime.now(timezone('America/Chicago'))

    # Calculate & save company total points
    calc_points = User.objects.all().aggregate(all_points = Sum('total_points'))
    company_points = round(calc_points['all_points'], 2)

    context = {
        'company_points': company_points,
        'date_time': now.strftime('%I:%M %p | %d %B %Y'),
        'quote': Quote.objects.last(),
        'user': User.objects.get(id=request.session['id'])
    }
    return render(request, 'admin_home.html', context)


def clock_in(request):
    shift = Shift.objects.create(
        clock_in = datetime.now(timezone('America/Chicago')),
        time_in = datetime.now(timezone('America/Chicago')),
        date = datetime.now(timezone('America/Chicago')),
        employee = User.objects.get(id = request.session['id'])
    )

    request.session['shift_id'] = shift.id
    return redirect('/clocked_in')


def clocked_in(request):
    now = datetime.now(timezone('America/Chicago'))

    user = User.objects.get(id=request.session['id'])
    user_shifts = Shift.objects.filter(employee = user)
    print(user_shifts)

    # Calculate & save user total points
    if user_shifts[0].clock_out != None:
        calc_points = User.objects.annotate(sum_points = Sum('shifts__points')).get(id=request.session['id'])
        total_points = calc_points.sum_points
        user.total_points = round(total_points, 2)
        user.save()

    # Calculate & save company total points
    calc_points = User.objects.all().aggregate(all_points = Sum('total_points'))
    company_points = round(calc_points['all_points'], 2)

    context = {
        'company_points': company_points,
        'date_time': now.strftime('%I:%M %p | %d %B %Y'),
        'shifts': Shift.objects.all(),
        'user': user,
        'users': User.objects.all()
    }

    return render(request, 'clocked_in.html', context)


def clock_out(request):
    errors = Shift.objects.validate(request.POST)

    if len(errors):
        for key, value in errors.items():
            messages.error(request, value)
        return redirect('/clocked_in')

    else:
        user = User.objects.get(id = request.session['id'])
        shift = Shift.objects.get(id = request.session['shift_id'])

        # Calculate work hours & points (use rate!!!)
        timeDiff = datetime.now(timezone('America/Chicago')) - shift.clock_in
        total_seconds = int(timeDiff.total_seconds())
        hours = Decimal(total_seconds/3600)
        points = hours * user.points_rate

        print("total_seconds" + str(total_seconds), 'hours' + str(hours), "points" + str(points))
        shift.clock_out = datetime.now(timezone('America/Chicago'))
        shift.time_out = datetime.now(timezone('America/Chicago'))
        shift.hours = hours
        shift.points = points
        shift.description = request.POST['description']
        shift.save()
        # Add shift points to total points
        user.total_points += points
        user.save()

    return redirect('/home')

def edit_quote(request):
    errors = Quote.objects.validate(request.POST)
    print(errors)

    if len(errors):
        for key, value in errors.items():
            messages.error(request, value)
        return redirect('/admin_home')

    else:
        Quote.objects.create(
            author = request.POST['author'],
            quote = request.POST['quote']
        )
        return redirect('/admin_home')

def email(request):
    errors = Email.objects.validate(request.POST)

    if len(errors):
        for key, value in errors.items():
            messages.error(request, value)
        return redirect('/report')

    else:
        Email.objects.create(
            description = request.POST['description'],
            challenges = request.POST['challenges'],
            help = request.POST['help'],
            recipients = request.POST['recipients'],
            sender = User.objects.get(id=request.session['id'])
        )
        messages.success(request, "Daily reports created")
        return redirect('/report')

def forgot(request):
    now = datetime.now(timezone('America/Chicago'))

    user = User.objects.get(id=request.session['id'])
    shift = Shift.objects.get(id=request.POST['shift_id'])

    naive = datetime.strptime(request.POST['clock_out']+':00', "%Y-%m-%dT%H:%M:%S")
    aware = pytz.utc.localize(naive)

    print(naive)
    print(aware)
    print(request.POST['clock_out'])
    print(clock_out)
    print(shift.clock_in)
    # Calculate work hours & points (use rate!!!)
    timeDiff = aware - shift.clock_in
    total_seconds = int(timeDiff.total_seconds())
    hours = round(Decimal(total_seconds/3600) + 5, 1)
    points = hours * user.points_rate

    print("total_seconds" + str(total_seconds), 'hours' + str(hours), "points" + str(points))
    shift.clock_out = aware
    shift.time_out = aware
    shift.hours = hours
    shift.points = points
    shift.description = request.POST['description']
    shift.save()
    # Add shift points to total points
    user.total_points += points
    user.save()


    print(request.POST)
    return redirect('/home')


def home(request):
    now = datetime.now(timezone('America/Chicago'))
    print(now)

    user = User.objects.get(id=request.session['id'])
    user_shifts = Shift.objects.filter(employee = user)

    # Calculate & save user total points
    if len(user_shifts):
        if user_shifts[0].clock_out != None:
            calc_points = User.objects.annotate(sum_points = Sum('shifts__points')).get(id=request.session['id'])
            total_points = calc_points.sum_points
            user.total_points = round(total_points, 2)
            user.save()

    # Calculate & save company total points
    calc_points = User.objects.all().aggregate(all_points = Sum('total_points'))
    company_points = round(calc_points['all_points'], 2)

    context = {
        'company_points': company_points,
        'date_time': now.strftime('%I:%M %p | %d %B %Y'),
        'quote': Quote.objects.last(),
        'shifts': Shift.objects.all(),
        'user': user,
        'user_shifts': Shift.objects.filter(employee=user),
        'users': User.objects.all()
    }

    return render(request, 'home.html', context)


def index(request):
    return render(request, 'index.html')


def login(request):
    errors = User.objects.validate_login(request.POST)

    if len(errors):
        for key, value in errors.items():
            messages.error(request, value)
        return redirect('/')

    else:
        user = User.objects.get(email = request.POST['email'])
        request.session['id'] = user.id
        return redirect('/home')


def logout(request):
    request.session.clear()
    return redirect('/')


def points(request):
    now = datetime.now(timezone('America/Chicago'))

    user = User.objects.get(id=request.session['id'])
    user_shifts = Shift.objects.filter(employee = user)

    # Calculate & save user total points
    if user_shifts[0].clock_out != None:
        calc_points = User.objects.annotate(sum_points = Sum('shifts__points')).get(id=request.session['id'])
        total_points = calc_points.sum_points
        user.total_points = round(total_points, 2)
        user.save()

    # Calculate & save company total points
    calc_points = User.objects.all().aggregate(all_points = Sum('total_points'))
    company_points = round(calc_points['all_points'], 2)

    context = {
        'company_points': company_points,
        'date_time': now.strftime('%I:%M %p | %d %B %Y'),
        'shifts': Shift.objects.all(),
        'user': User.objects.get(id=request.session['id']),
        'user_shifts': Shift.objects.filter(employee=user),
        'users': User.objects.all()
    }
    return render(request, 'points.html', context)


def register(request):
    errors = User.objects.validate_reg(request.POST)

    if len(errors):
        for key, value in errors.items():
            messages.error(request, value)
        return redirect('/')

    else:
        user = User.objects.create(
            first_name = request.POST['first_name'],
            last_name = request.POST['last_name'],
            email = request.POST['email'],
            user_level = 1,
            total_points = 0,
            password = bcrypt.hashpw(request.POST['password'].encode(), bcrypt.gensalt())
        )

        if len(User.objects.all()) == 1:
            user.user_level = 9
            user.save()
            messages.success(request, "New Admin Added")
            request.session['id'] = user.id
            return redirect('/home')

        else:
            messages.success(request, "New User Added")
            request.session['id'] = user.id
            return redirect('/home')


def report(request):
    now = datetime.now(timezone('America/Chicago'))

    # Calculate & save company total points
    calc_points = User.objects.all().aggregate(all_points = Sum('total_points'))
    company_points = round(calc_points['all_points'], 2)

    context = {
        'company_points': company_points,
        'date_time': now.strftime('%I:%M %p | %d %B %Y'),
        'quote': Quote.objects.last(),
        'user': User.objects.get(id=request.session['id'])
    }

    return render(request, 'report.html', context)

def reset_password(request):
    pass

def settings(request):
    now = datetime.now(timezone('America/Chicago'))

    # Calculate & save company total points
    calc_points = User.objects.all().aggregate(all_points = Sum('total_points'))
    company_points = round(calc_points['all_points'], 2)

    context = {
        'company_points': company_points,
        'date_time': now.strftime('%I:%M %p | %d %B %Y'),
        'quote': Quote.objects.last(),
        'user': User.objects.get(id=request.session['id'])
    }

    return render(request, 'settings.html', context)

def updates(request):
    context = {
        'user': User.objects.get(id=request.session['id'])
    }
    return render(request, 'updates.html', context)
