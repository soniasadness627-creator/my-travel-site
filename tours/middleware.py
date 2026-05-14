from django.utils.deprecation import MiddlewareMixin
from .models import TourVisit


class TourTrackingMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        # Перевіряємо, чи це сторінка деталей туру
        if request.resolver_match and request.resolver_match.url_name in ['tour_detail_otpusk',
                                                                          'agent_tour_detail_otpusk']:
            hid = request.GET.get('hid')
            oid = request.GET.get('oid')

            if hid and oid:
                try:
                    TourVisit.objects.create(
                        tour_hid=hid,
                        tour_oid=oid,
                        user_ip=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                        session_key=request.session.session_key
                    )
                except Exception as e:
                    print(f"Помилка збереження відвідування: {e}")
        return None

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip