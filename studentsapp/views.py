import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .models import Registration

def cors_response(response):
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS, DELETE, PUT"
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

@csrf_exempt
def api_register(request):
    """
    API endpoint to register student details from ConsultationModal / registration form.
    Supports POST with JSON or Form-Data.
    """
    if request.method == "OPTIONS":
        response = HttpResponse()
        return cors_response(response)

    if request.method == "POST":
        try:
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            else:
                data = request.POST

            full_name = data.get('full_name') or data.get('name') or ''
            email = data.get('email') or ''
            phone = data.get('phone') or ''
            experience_level = data.get('experience') or data.get('experience_level') or 'College Student / Fresh Graduate'

            if not full_name or not email or not phone:
                res = JsonResponse({'success': False, 'error': 'Name, email, and phone are required.'}, status=400)
                return cors_response(res)

            registration = Registration.objects.create(
                full_name=full_name.strip(),
                email=email.strip(),
                phone=phone.strip(),
                experience_level=experience_level.strip()
            )

            res = JsonResponse({
                'success': True,
                'message': 'Registration completed successfully!',
                'data': {
                    'id': registration.id,
                    'full_name': registration.full_name,
                    'email': registration.email,
                    'phone': registration.phone,
                    'experience_level': registration.experience_level,
                    'created_at': registration.created_at.strftime('%Y-%m-%d %H:%M:%S')
                }
            }, status=201)
            return cors_response(res)

        except Exception as e:
            res = JsonResponse({'success': False, 'error': str(e)}, status=500)
            return cors_response(res)

    res = JsonResponse({'error': 'Method not allowed'}, status=405)
    return cors_response(res)


@csrf_exempt
def api_get_registrations(request):
    """
    API endpoint to fetch all registered student details.
    """
    if request.method == "OPTIONS":
        response = HttpResponse()
        return cors_response(response)

    registrations = Registration.objects.all()
    data = [{
        'id': r.id,
        'full_name': r.full_name,
        'email': r.email,
        'phone': r.phone,
        'experience_level': r.experience_level,
        'status': r.status,
        'created_at': r.created_at.strftime('%b %d, %Y %I:%M %p')
    } for r in registrations]

    res = JsonResponse({'success': True, 'count': len(data), 'registrations': data})
    return cors_response(res)


@csrf_exempt
def admin_login_view(request):
    """
    Superuser Admin Login View
    """
    if request.user.is_authenticated:
        return redirect('registrations_dashboard')

    error = None
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('registrations_dashboard')
        else:
            error = "Invalid username or password. Please try again."

    return render(request, 'admin_login.html', {'error': error})


def admin_logout_view(request):
    """
    Logout view
    """
    logout(request)
    return redirect('admin_login')


@login_required(login_url='admin_login')
def registrations_dashboard(request):
    """
    Backend HTML Template view showing all student registration details with Start Date & End Date filtering.
    Protected by superuser login.
    """
    from django.utils import timezone
    from datetime import timedelta, datetime

    registrations = Registration.objects.all().order_by('-created_at')

    start_date_str = request.GET.get('start_date', '').strip()
    end_date_str = request.GET.get('end_date', '').strip()

    filtered_registrations = registrations

    if start_date_str:
        try:
            start_d = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            filtered_registrations = filtered_registrations.filter(created_at__date__gte=start_d)
        except ValueError:
            pass

    if end_date_str:
        try:
            end_d = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            filtered_registrations = filtered_registrations.filter(created_at__date__lte=end_d)
        except ValueError:
            pass

    now = timezone.now()
    today_start = now.date()
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    # Summary Statistics
    total_count = registrations.count()
    today_count = registrations.filter(created_at__date=today_start).count()
    week_count = registrations.filter(created_at__gte=seven_days_ago).count()
    month_count = registrations.filter(created_at__gte=thirty_days_ago).count()

    context = {
        'registrations': filtered_registrations,
        'total_count': total_count,
        'today_count': today_count,
        'week_count': week_count,
        'month_count': month_count,
        'start_date': start_date_str,
        'end_date': end_date_str,
        'user': request.user,
    }
    return render(request, 'dashboard.html', context)


@csrf_exempt
def update_registration_status(request, pk):
    if request.method == "POST":
        reg = get_object_or_404(Registration, pk=pk)
        try:
            data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
            new_status = data.get('status')
            if new_status:
                reg.status = new_status
                reg.save()
                return cors_response(JsonResponse({'success': True, 'status': reg.status}))
        except Exception as e:
            return cors_response(JsonResponse({'success': False, 'error': str(e)}, status=400))
    return cors_response(JsonResponse({'error': 'Invalid request'}, status=400))


@csrf_exempt
def delete_registration(request, pk):
    if request.method in ["POST", "DELETE"]:
        reg = get_object_or_404(Registration, pk=pk)
        reg.delete()
        return cors_response(JsonResponse({'success': True}))
    return cors_response(JsonResponse({'error': 'Invalid request'}, status=400))


@login_required(login_url='admin_login')
def export_excel_view(request):
    """
    Exports all registered student details into an Excel Spreadsheet (.xls).
    """
    registrations = Registration.objects.all().order_by('-created_at')

    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Student_Registrations_All.xls"'

    html = """<html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
    <head>
        <meta charset="UTF-8">
        <!--[if gte mso 9]>
        <xml>
            <x:ExcelWorkbook>
                <x:ExcelWorksheets>
                    <x:ExcelWorksheet>
                        <x:Name>Registered Students</x:Name>
                        <x:WorksheetOptions>
                            <x:DisplayGridlines/>
                        </x:WorksheetOptions>
                    </x:ExcelWorksheet>
                </x:ExcelWorksheets>
            </x:ExcelWorkbook>
        </xml>
        <![endif]-->
        <style>
            th { background-color: #10b981; color: #ffffff; font-weight: bold; padding: 10px; font-size: 14px; }
            td { padding: 8px; font-size: 13px; }
        </style>
    </head>
    <body>
    <table border="1">
        <thead>
            <tr>
                <th>ID</th>
                <th>Full Name</th>
                <th>Email Address</th>
                <th>Phone Number</th>
                <th>Experience Level</th>
                <th>Submitted Date & Time</th>
            </tr>
        </thead>
        <tbody>
    """

    for r in registrations:
        phone_fmt = f"'{r.phone}" if not r.phone.startswith("'") else r.phone
        html += f"""
            <tr>
                <td>#{r.id}</td>
                <td>{r.full_name}</td>
                <td>{r.email}</td>
                <td>{phone_fmt}</td>
                <td>{r.experience_level}</td>
                <td>{r.created_at.strftime('%Y-%m-%d %H:%M:%S')}</td>
            </tr>
        """

    html += """
        </tbody>
    </table>
    </body>
    </html>
    """

    response.write(html)
    return response


