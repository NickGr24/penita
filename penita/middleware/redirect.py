from django.http import HttpResponsePermanentRedirect


class RemoveWWWMiddleware:
    """
    Middleware для редиректа с www на версию без www.

    Это решает проблему с duplicate content в SEO, когда Google индексирует
    обе версии сайта (с www и без www), но canonical теги указывают только на одну.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().lower()

        # Если запрос идет на www версию, делаем 301 редирект на версию без www
        if host.startswith('www.'):
            # Получаем схему (http или https) из заголовков прокси
            scheme = request.META.get('HTTP_X_FORWARDED_PROTO', 'http')

            # Убираем www из хоста
            new_host = host[4:]  # Удаляем 'www.'

            # Строим новый URL
            new_url = f"{scheme}://{new_host}{request.get_full_path()}"

            # Возвращаем 301 редирект (постоянный)
            return HttpResponsePermanentRedirect(new_url)

        # Если запрос не на www версию, обрабатываем как обычно
        return self.get_response(request)
