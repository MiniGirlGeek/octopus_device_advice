from django.shortcuts import render
from django.http import HttpResponse
import requests
from datetime import datetime, timedelta
from .models import Task
from google.oauth2 import service_account
from googleapiclient.discovery import build
from django.views.decorators.csrf import csrf_exempt
import json




SCOPES = ["https://www.googleapis.com/auth/calendar"]

service_account_email = "device-advice-service-account@device-advice.iam.gserviceaccount.com"
credentials = service_account.Credentials.from_service_account_file('secrets.json')
scoped_credentials = credentials.with_scopes(SCOPES)
calendarId = "6ced8357cdad2c13accfa2bf97cb140589d592dd076c8e570a3f972e26fbcc24@group.calendar.google.com"


def build_service(request):
    service = build("calendar", "v3", credentials=scoped_credentials)
    return service

from .models import Device
def half_hour_group_by(no_half_hours, results):
    no_half_hours_results = []
    i = 0
    min_average = float('inf')
    best_time = 0
    for result in results:
        time = datetime.strptime(result['valid_from'],"%Y-%m-%dT%H:%M:%SZ")
        time = time + timedelta(hours=1)
        if time > datetime.now():
            if i <= len(results) - no_half_hours:
                sum = 0
                for j in range(no_half_hours):
                    sum += results[i+j]['value_inc_vat']
                average = round(sum/no_half_hours, 1)
                if average < min_average:
                    min_average = average
                    best_time = time
                no_half_hours_results.append({'x': result['valid_from'], 'y': average})
        i+=1
    return no_half_hours_results, min_average, best_time

def build_calendar_booking_request(start_time, duration, title, service):
    print(start_time.isoformat() + "+00:00")
    event = (
        service.events().insert(
            calendarId=calendarId,
            body={
                "summary": title,
                "start": {"dateTime": start_time.isoformat() + "+00:00"},
                "end": {"dateTime": (start_time + timedelta(hours=float(duration))).isoformat() + "+00:00"},
            },
        ).execute()
    )


@csrf_exempt
def index(request):
    service = build_service(request)
    url = 'https://api.octopus.energy'
    product_code = "AGILE-18-02-21"
    tariff_code = f"E-1R-{product_code}-C"
    tariff_url = f"{url}/v1/products/{product_code}/electricity-tariffs/{tariff_code}/standard-unit-rates/"
    response = requests.get(url=tariff_url)
    data = response.json()
    results = data['results'][::-1]
    half_hour, hlfhmin, hlfhbt = half_hour_group_by(1, results)
    one_hour, ohmin, ohbt = half_hour_group_by(2, results)
    hour_half, hhlfmin, hhlfbt = half_hour_group_by(3, results)
    two_hour, thmin, thbt = half_hour_group_by(4, results)
    eight_hour, ehmin, ehbt = half_hour_group_by(8, results)
    now = str(datetime.now())

    best_times = {
        0.5: hlfhbt,
        1.0: ohbt,
        1.5: hhlfbt,
        2.0: thbt,
        8.0: ehbt
    }

    current_task_list = Task.objects.order_by('-duration')

    context = {
        'data': half_hour,
        'now': now,
        'data2': one_hour,
        'data3': hour_half,
        'data4': two_hour,
        'data5': eight_hour,
        'hlfhmin': hlfhmin,'hlfhbt': hlfhbt,
        'hhlfmin': hhlfmin, 'hhlfbt': hhlfbt,
        'ohmin': ohmin, 'ohbt': ohbt,
        'thmin': thmin, 'thbt': thbt,
        'ehmin': ehmin, 'ehbt': ehbt,
        'current_task_list': current_task_list
    }
    if request.method == "POST":
        data = request.POST
        duration = (data["duration"])
        title = (data["task"])
        start_time = best_times[float(duration)]
        build_calendar_booking_request(start_time, duration, title, service)
    return render(request, 'device_advice/index.html', context)
