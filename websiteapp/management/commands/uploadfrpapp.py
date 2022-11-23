# *_*coding:utf-8 *_*
# @Author : Reggie
# @Time : 2022/11/7 9:43
import argparse

import requests
from django.core.management import BaseCommand
from requests.auth import HTTPBasicAuth

from websiteapp.models import WebSite, WebSiteGroup


def bytes2x(n: int, position: int = 2, base=1024, u=0, show_symbol=True) -> str:
    symbols = ('', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    while n >= base:
        n = n / base
        u = u + 1
    result = f"{n:.{position}f}"
    if show_symbol:
        result += f"{symbols[u]}"
    return result


class Logger:
    def __init__(self, level=5, verbose_level=4):
        self.level = level
        self.verbose_level = verbose_level

    def _print(self, msg, level):
        if level <= self.verbose_level:
            print(msg)

    def info(self, msg):
        self._print(msg, level=4)

    def debug(self, msg):
        self._print(msg, level=5)

    def warning(self, msg):
        self._print(msg, level=3)


logger = Logger()


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
        parser.add_argument("-H", "--host", dest="host", required=True)
        parser.add_argument("-p", "--port", dest="port", required=False, default=7500, type=int)
        parser.add_argument("-s", "--secure", dest="secure", required=False, default=False, type=bool)
        parser.add_argument("-V", "--verbose", dest="verbose", required=False, default=False, type=bool)

    @classmethod
    def is_ignore_name(cls, name):
        for n in cls.ignore_name:
            if n in name:
                return True
        return False

    @classmethod
    def handle_groups(cls, groups):
        result = []
        groups.sort(key=lambda x: x)
        for group in groups:
            group_name = group
            website_group = WebSiteGroup.objects.filter(name=group_name).first()
            if not website_group:
                website_group = WebSiteGroup.objects.create(name=group_name)
                logger.debug(f"add group {group_name}")
            result.append(website_group)
        return result

    @classmethod
    def handle_sites(cls, sites, groups):
        group_map = {group.name: group.pk for group in groups}
        sites.sort(key=lambda x: x["site_name"])
        for site in sites:
            name = site["name"]
            site_name = site["site_name"]
            remote_port = site["remote_port"]
            group_name = site["group_name"]
            host = site["host"]
            web_site = WebSite.objects.filter(title=site_name).first()
            path = f"http://{host}:{remote_port}"
            if not web_site:
                WebSite.objects.create(
                    path=path,
                    title=site_name,
                    description=site_name,
                    website_group_id=group_map[group_name]
                )
                logger.debug(f"add proxy: {name}")
            else:
                web_site.path = path
                web_site.website_group_id = group_map[group_name]
                web_site.save()
                logger.debug(f"update proxy: {name}")

    @classmethod
    def show_server(cls, server_info):
        ignore_key = [
            'vhost_http_port',
            'vhost_https_port',
            'kcp_bind_port',
            'subdomain_host',
            'bind_udp_port',
        ]
        lines = []
        max_line = 0
        for k, v in server_info.items():
            if k in ignore_key:
                continue
            if k in ["total_traffic_in", "total_traffic_out"]:
                v = bytes2x(v)
            line = f"{f'|  {k} :'.ljust(25, ' ')} {str(v).ljust(12, ' ')} |"
            max_line = len(line)
            lines.append(line)
        logger.info(" fro info ".center(max_line, "-"))
        [logger.info(line) for line in lines]
        logger.info("".center(max_line, "-"))

    def handle(self, *args, **options):

        session = requests.session()
        session.auth = HTTPBasicAuth("admin", "wangtong")
        secure = options.get("secure")
        host = options.get("host")
        port = options.get("port")
        verbose = options.get("verbose")
        if verbose:
            logger.verbose_level = 5
        base_host = f"http{'s' if secure else ''}://{host}:{port}"

        url = f"{base_host}/{self.SERVER_INFO}"
        resp = session.get(url)
        self.show_server(resp.json())

        url = f"{base_host}/{self.TCP_API}"
        resp = session.get(url)
        WebSite.objects.filter()
        WebSiteGroup.objects.filter()
        # print(json.dumps(resp.json(), indent=4))
        proxies = resp.json().get('proxies', {})
        groups = []
        sites = []
        for proxy in proxies:
            name = proxy.get('name')
            if not name:
                continue
            if self.is_ignore_name(name):
                logger.debug(f"Ignoring name: {name}")
                continue

            name_split = name.split('-')
            if len(name_split) != 2:
                continue
            group_name, site_name = name_split
            groups.append(group_name)
            if not proxy:
                continue
            conf = proxy.get('conf')
            if not conf:
                logger.warning(f"{name} has no conf")
            remote_port = conf.get('remote_port')
            sites.append(
                {
                    "name": name,
                    "site_name": site_name,
                    "host": host,
                    "group_name": group_name,
                    "remote_port": remote_port,
                }
            )
        self.handle_sites(sites, self.handle_groups(groups))
