from django.http import HttpResponse


def hello_notes(request):
    return HttpResponse("Hello from Notes app.")
