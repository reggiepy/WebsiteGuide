# *_*coding:utf-8 *_*
# @Author : Reggie
# @Time : 2022/11/7 9:43
import argparse

import requests
from django.core.management import BaseCommand
from requests.auth import HTTPBasicAuth

from websiteapp.models import WebSite, WebSiteGroup


class Command(BaseCommand):
    SERVER_INFO = "api/serverinfo"
    TCP_API = "api/proxy/tcp"
    UDP_API = "api/proxy/udp"
    HTTP_API = "api/proxy/http"
    HTTPS_API = "api/proxy/https"
    STCP_API = "api/proxy/stcp"
    ignore_name = [
        "ssh",
        "mysql",
        "redis",
        "rdp",
        "windows",
    ]

    def add_arguments(self, parser: argparse.ArgumentParser):
        parser.add_argument("-host", "--host", dest="host", required=True)
        parser.add_argument("-p", "--port", dest="port", required=False, default=7500, type=int)
        parser.add_argument("-s", "--secure", dest="secure", required=False, default=False, type=bool)

    @classmethod
    def is_ignore_name(cls, name):
        for n in cls.ignore_name:
            if n in name:
                return True
        return False

    def handle(self, *args, **options):

        session = requests.session()
        session.auth = HTTPBasicAuth("admin", "wangtong")
        secure = options.get("secure")
        host = options.get("host")
        port = options.get("port")
        base_host = f"http{'s' if secure else ''}://{host}:{port}"

        url = f"{base_host}/{self.SERVER_INFO}"
        resp = session.get(url)
        # print(resp.json())

        url = f"{base_host}/{self.TCP_API}"
        resp = session.get(url)
        WebSite.objects.filter()
        WebSiteGroup.objects.filter()
        # print(json.dumps(resp.json(), indent=4))
        proxies = resp.json().get('proxies', {})
        for proxy in proxies:
            name = proxy.get('name')
            if not name:
                continue
            if self.is_ignore_name(name):
                print("Ignoring name: {}".format(name))
                continue

            name_split = name.split('-')
            if len(name_split) != 2:
                continue
            group_name, site_name = name_split
            website_group = WebSiteGroup.objects.filter(name=group_name).first()
            if not website_group:
                website_group = WebSiteGroup.objects.create(name=group_name)
            remote_port = proxy.get('conf', {}).get('remote_port')
            web_site = WebSite.objects.filter(title=site_name).first()
            path = f"http://{host}:{remote_port}"
            if not web_site:
                WebSite.objects.create(
                    path=path,
                    title=site_name,
                    description=site_name,
                    website_group_id=website_group.pk
                )
            else:
                web_site.path = path
                web_site.website_group_id = website_group.pk
                web_site.save()
            print("add proxy: {}".format(name))
            # print(proxy)
