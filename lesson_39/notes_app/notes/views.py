from django.shortcuts import render


def notes_list(request):
    notes = [
        {
            "title": "First note",
            "text": "Learn Django views and templates.",
            "created_at": "2026-06-01",
        },
        {
            "title": "Second note",
            "text": "Move CSS to a separate static file.",
            "created_at": "2026-06-02",
        },
        {
            "title": "Third note",
            "text": "Render test data on the main HTML page.",
            "created_at": "2026-06-03",
        },
    ]

    return render(request, "notes/index.html", {"notes": notes})
