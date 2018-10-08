# Keypirinha launcher (keypirinha.com)

import keypirinha as kp
import keypirinha_util as kpu
import keypirinha_net as kpnet
import json
from datetime import datetime
from urllib.parse import urljoin 
import os

class Rocketchat(kp.Plugin):
 
    DAYS_KEEP_CACHE = 7
    ITEMCAT = kp.ItemCategory.USER_BASE + 1

    def __init__(self):
        super().__init__()
        try:
            if os.environ['DEBUG'] == 'rocketchat': 
                self._debug = True # enables self.dbg() output
        except Exception as exc:
            self._debug = False    
        self.users = []
        self.channels = []
       

    def on_start(self):
        self.dbg("On Start")
        self.read_config()
        self.generate_cache()
        self.get_users()
        self.get_channels()
        pass

    def on_catalog(self):
        self.dbg("On catalog")
        self.set_catalog([
            self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label="rocketchat",
                short_desc="Search users",
                target="rocketchat",
                args_hint=kp.ItemArgsHint.REQUIRED,
                hit_hint=kp.ItemHitHint.KEEPALL
            )
        ])

    def on_suggest(self, user_input, items_chain):
        if not items_chain or items_chain[0].category() != kp.ItemCategory.KEYWORD:
            return

        suggestionsU = self.filter_users(user_input)
        suggestionsC = self.filter_channels(user_input)

        self.set_suggestions(suggestionsU + suggestionsC, kp.Match.ANY, kp.Sort.LABEL_ASC)

    def filter_users(self, user_input):
        return list(filter(lambda item: self.has_name(item, user_input), self.users))
    
    def filter_channels(self, user_input):
        return list(filter(lambda item: self.has_name(item, user_input), self.channels))

    def has_name(self, item, user_input):
        if user_input.lower() in item.label().lower():
            self.dbg(user_input)
            return item
        return False

    def on_execute(self, item, action):
        if item.category() != self.ITEMCAT:
            return
        url=urljoin(self.DOMAIN, item.short_desc()+ "/" + item.target())
        self.dbg(url)
        kpu.web_browser_command(private_mode=None,url=url,execute=True)

    def generate_cache(self):
        cache_path_u = self.get_cache_path("u")
        cache_path_c = self.get_cache_path("c")
        should_generate = False
        try:
            last_modified = datetime.fromtimestamp(os.path.getmtime(cache_path)).date()
            if ((last_modified - datetime.today().date()).days > self.DAYS_KEEP_CACHE):
                should_generate = True
        except Exception as exc:
            should_generate = True

        if not should_generate:
            return False
        self.dbg(self.AUTH,self.USER_ID,self.DOMAIN)
        opener = kpnet.build_urllib_opener()
        opener.addheaders = [("X-Auth-Token", str(self.AUTH)),("X-User-Id",str(self.USER_ID))]
        urlUsers = urljoin(self.DOMAIN ,"/api/v1/users.list")
        urlChannels = urljoin(self.DOMAIN ,"/api/v1/channels.list")
        try:
            with opener.open(urlUsers) as request:
                response = request.read()
                data = json.loads(response)
                with open(cache_path_u, "w") as index_file:
                    json.dump(data, index_file, indent=2)
        except Exception as exc:
            self.err("Could not reach the users to generate the cache: ", exc)   
        try:          
            with opener.open(urlChannels) as request:
                response = request.read()
                data = json.loads(response)
                with open(cache_path_c, "w") as index_file:
                    json.dump(data, index_file, indent=2)   
        except Exception as exc:
            self.err("Could not reach the channles to generate the cache: ", exc)     

    def get_users(self):
        if not self.users:
            with open(self.get_cache_path("u"), "r") as users_file:
                data = json.loads(users_file.read())
            for item in data['users']:
                self.dbg(item['name']) 
                suggestion = self.create_item(
                    category=self.ITEMCAT,
                    label=item['name'],
                    short_desc="direct",
                    target=item['name'],
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE
                )

                self.users.append(suggestion)

        return self.users

    def get_channels(self):
        if not self.channels:
            with open(self.get_cache_path("c"), "r") as users_file:
                data = json.loads(users_file.read())
            for item in data['channels']:
                self.dbg(item['name']) 
                self.dbg("-------------------------") 
                suggestion = self.create_item(
                    category=self.ITEMCAT,
                    label=item['name'],
                    short_desc="channel",
                    target=item['name'],
                    args_hint=kp.ItemArgsHint.FORBIDDEN,
                    hit_hint=kp.ItemHitHint.IGNORE
                )

                self.channels.append(suggestion)

        return self.channels

    def get_cache_path(self,prefix):
        cache_path = self.get_package_cache_path(True)
        return os.path.join(cache_path, prefix + 'rocketchat.json')

    # read ini config
    def read_config(self):
        settings = self.load_settings()
        self.AUTH = settings.get("AUTH", "main")
        self.USER_ID = settings.get("USER_ID", "main")
        self.DOMAIN = settings.get("DOMAIN", "main")
