def add_user_to_context(request):
    """
    Додає користувача в контекст всіх шаблонів
    """
    return {
        'user': request.user
    }