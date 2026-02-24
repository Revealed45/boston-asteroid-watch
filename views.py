from django.shortcuts import render
from django.http import JsonResponse
from .nasa_api import get_top5_asteroids


def index(request):
    error = None
    data = None
    try:
        data = get_top5_asteroids(force_refresh=False)
    except Exception as e:
        error = str(e)
    return render(request, 'tracker/index.html', {'data': data, 'error': error})


def refresh(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = get_top5_asteroids(force_refresh=True)
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
