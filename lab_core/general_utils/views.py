# encode: utf-8

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from user_agents import parse

from .models import LetsencryptModel, MobileSettings, MOBILE_CHOICES

@csrf_exempt
def lets_encrypt_acme(request, acme_challenge):
    """
    acme challenge response from key for lets_encrypt
    :param request:
    :param acme_challenge:
    :return:
    """
    content = get_object_or_404(LetsencryptModel, pk=acme_challenge)
    return HttpResponse(content.content)

@csrf_exempt
def mobile_settings(request, version):
    """
    json formatted mobile settings
    :param request:
    :return: json
    """
    agent = parse(request.META.get('HTTP_USER_AGENT'))
    content = MobileSettings.objects.all().values('key', 'key_value')
    return JsonResponse(dict((i.get('key'), i.get('key_value')) for i in content), safe=False)

