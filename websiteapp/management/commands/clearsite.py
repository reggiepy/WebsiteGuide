# *_*coding:utf-8 *_*
# @Author : Reggie
# @Time : 2022/11/7 9:43

from django.core.management import BaseCommand

from websiteapp.models import WebSite, WebSiteGroup


class Command(BaseCommand):
    def handle(self, *args, **options):
        print("start clear website")
        for site in WebSite.objects.all():
            print("remove site: %s" % site.title)
            site.delete()
        print("clear website successfully")
        print("start clear site group")
        for group in WebSiteGroup.objects.all():
            print("remove site group: %s" % group.name)
            group.delete()
        print("clear site group successfully")
