from django.shortcuts import render
import os
from django.conf import settings
from django.http import FileResponse, Http404

def home(request):
    return render(request, 'home/home.html')


def download_resume(request):
    filepath = os.path.join(settings.BASE_DIR, 'static', 'files', 'resume.pdf')
    if not os.path.exists(filepath):
        raise Http404("Resume not found")
    # as_attachment=True triggers the "Save as" dialog
    return FileResponse(open(filepath, 'rb'), as_attachment=True, filename='Muhammed_Irshad_Resume.pdf')