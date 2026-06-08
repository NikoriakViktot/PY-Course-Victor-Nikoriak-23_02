from django.http import HttpResponse
def hello_notes(request):
    """Простий view, який виводить вітальне повідомлення."""
    return HttpResponse("Hello from Notes app.")