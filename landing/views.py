from django.shortcuts import render

def index(request):
    """Головна сторінка лендингу"""
    return render(request, 'landing/index.html')

def privacy_policy(request):
    """Сторінка політики конфіденційності для лендингу"""
    return render(request, 'landing/privacy_policy.html')

def terms_of_service(request):
    """Сторінка правил надання послуг для лендингу"""
    return render(request, 'landing/terms_of_service.html')