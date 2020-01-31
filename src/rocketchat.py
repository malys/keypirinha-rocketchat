# Keypirinha launcher (keypirinha.com)

import keypirinha as kp
import keypirinha_util as kpu
import keypirinha_net as kpnet
import json
from datetime import datetime
from urllib.parse import urljoin 
import os
import urllib

class Rocketchat(kp.Plugin):
 
    DAYS_KEEP_CACHE = 10
    LIMIT = 2000
    ITEMCAT = kp.ItemCategory.USER_BASE + 1
    ITEMMESSAGE = kp.ItemCategory.USER_BASE + 2

    def __init__(self):
        super().__init__()
        try:
            if os.environ['DEBUG'] == 'rocketchat': 
                self._debug = True # enables self.dbg() output
        except Exception as exc:
            self._debug = False    
        self.users = []

    def on_events(self, flags):
        """
        Reloads the package config when its changed
        """
        self.dbg(flags)
        if flags & kp.Events.PACKCONFIG:
            self.read_config()
    
    def forge_action(self, name, label, desc):
        return self.create_action(
            name = name,
            label = label,
            short_desc = desc
        )

    def on_start(self):
        self.dbg("On Start")
        self.set_actions(self.ITEMMESSAGE, [self.forge_action('open', 'Open', 'Open rocket chat')]) 
        #self.set_actions(self.ITEMMESSAGE, [self.forge_action('send', 'Send', 'Send to rocket chat')]) 
        if self.read_config():
            if self.generate_cache():
                self.get_users()
        pass

    def on_catalog(self):
        self.dbg("On catalog")
        self.set_catalog([
            self.create_item(
                category=kp.ItemCategory.KEYWORD,
                label="Rocketchat",
                short_desc="Search users/channels",
                target="rocketchat",
                args_hint=kp.ItemArgsHint.REQUIRED,
                hit_hint=kp.ItemHitHint.KEEPALL
            )
        ])

    def forge_suggest(self,short_desc,channel, message):
        return self.create_item(
            category = self.ITEMMESSAGE,
            label = message,
            short_desc = short_desc,
            target = channel,
            args_hint = kp.ItemArgsHint.ACCEPTED,
            hit_hint = kp.ItemHitHint.IGNORE)

    def on_suggest(self, user_input, items_chain):
        if not items_chain or items_chain[0].category() != kp.ItemCategory.KEYWORD:
            return 
        if len(items_chain) == 1:
            self.set_suggestions(self.filter(user_input), kp.Match.FUZZY, kp.Sort.LABEL_ASC) 
        elif len(items_chain) > 1 and len(user_input)>0:
            self.dbg("--->",user_input) 
            suggestions=[self.forge_suggest(items_chain[1].short_desc(), items_chain[1].target(),user_input)] 
            self.set_suggestions(suggestions)

    def filter(self, user_input):
        return list(filter(lambda item: self.has_name(item, user_input), self.users))
    
    def has_name(self, item, user_input):
        #self.dbg(user_input.upper(),item.label().upper())
        if user_input.upper() in item.label().upper():
            return item
        return False

    def forgeRequest(self, url,typ,dataRaw):
        opener = kpnet.build_urllib_opener()
        opener.addheaders = [("X-Auth-Token", str(self.AUTH)),("X-User-Id",str(self.USER_ID))]
        if typ == 'POST':
            data = urllib.parse.urlencode(dataRaw).encode()
            req = urllib.request.Request(url, data=data)
            return opener.open(req)
        else:
            return opener.open(url) 

    def openBrowser(self, item):
        url=urljoin(self.DOMAIN, item.short_desc()+ "/" + item.target())
        self.dbg("open",url)
        kpu.web_browser_command(private_mode=None,url=url,execute=True)       

    def on_execute(self, item, action):
        self.dbg("Execute",item, action)
        if action:
            if action.name() == "open":
                self.openBrowser(item)
        elif item.category() == self.ITEMMESSAGE:
            url=urljoin(self.DOMAIN, "/api/v1/chat.postMessage")
            self.dbg("Send", item.short_desc(), item.target())
            prefix = ""
            if item.short_desc() == "direct":
                prefix="@"
            with self.forgeRequest(url,"POST",{ "channel": prefix + item.target(), "text": item.label() }) as request:
                response = request.read()
                self.openBrowser(item)




    def generate_cache(self):
        self.dbg("generate_cache user",self.AUTH,self.USER_ID,self.DOMAIN) 
        cache_path_c = self.get_cache_path("c")
        should_generate = False
        cache_path = self.get_package_cache_path(True)
        self.dbg(cache_path) 

        for i in os.listdir(cache_path):
            self.dbg('Find',i) 
            if os.path.isfile(os.path.join(cache_path,i)) and "urocket"  in i:
                file = os.path.join(cache_path,i)
                self.dbg('file',file)
                break
        
        try:
            last_modified = datetime.fromtimestamp(os.path.getmtime(file)).date()
            if ((last_modified - datetime.today().date()).days > self.DAYS_KEEP_CACHE):
                should_generate = True
        except Exception as exc:
            should_generate = True

        if not should_generate:
            return True
        urlUsers = urljoin(self.DOMAIN ,'/api/v1/users.list?fields={"name":1,"username":2}&query={"active":true,"type":{"$in":["user"]}}&count=' + str(self.LIMIT))
        urlChannels = urljoin(self.DOMAIN ,'/api/v1/channels.list?fields={"name":1}&count=0')
        offset=0
        total= self.LIMIT
        while offset < total:
            try:
                with self.forgeRequest(urlUsers + '&offset=' + str(offset),"GET","") as request:
                    response = request.read()
                    data = json.loads(response)
                    self.dbg(offset,total)  
                    if total > self.LIMIT:
                        total=self.LIMIT
                    with open(self.get_cache_path(str(offset) +"u"  ), "w") as index_file:
                        json.dump(data, index_file, indent=2)
                        total= int(data["total"])
                        offset= offset + int(data["count"]) 
            except Exception as exc:
                self.err("Could not reach the users to generate the cache: ", exc)  
                return (offset>0) 
        self.dbg("generate_cache channel",self.AUTH,self.USER_ID,self.DOMAIN)         
        try:          
            with self.forgeRequest(urlChannels,"GET","") as request:
                response = request.read()
                data = json.loads(response)
                with open(cache_path_c, "w") as index_file:
                    json.dump(data, index_file, indent=2)   
        except Exception as exc:
            self.err("Could not reach the channels to generate the cache: ", exc)  
            return False 
        return True      

    def get_users(self):
        self.dbg('Get users')
        if not self.users:
            cache_path = self.get_package_cache_path(True)
            for i in os.listdir(cache_path):
                self.dbg(i)
                if os.path.isfile(os.path.join(cache_path,i)) and "urocket" in i:
                    with open(os.path.join(cache_path,i), "r") as users_file:
                        data = json.loads(users_file.read())
                        for item in data['users']:
                            self.dbg('cusers:' ,item['name']) 
                            suggestion = self.create_item(
                                category=self.ITEMCAT,
                                label=self.get_unique_name(item),
                                short_desc="direct",
                                target=self.get_unique_name(item),
                                args_hint=kp.ItemArgsHint.REQUIRED,
                                hit_hint=kp.ItemHitHint.KEEPALL
                            )

                            self.users.append(suggestion)
            with open(self.get_cache_path("c"), "r") as users_file:
                data = json.loads(users_file.read())

                for item in data['channels']:
                    self.dbg('cchannel:' ,item['name']) 
                    #self.dbg("-------------------------") 
                    suggestion = self.create_item(
                        category=self.ITEMCAT,
                        label=item['name'],
                        short_desc="channel",
                        target=item['name'],
                        args_hint=kp.ItemArgsHint.REQUIRED,
                        hit_hint=kp.ItemHitHint.KEEPALL
                    )

                    self.users.append(suggestion)        
        self.dbg('Length:' , len(self.users) )
        return self.users

    def get_cache_path(self,prefix):
        cache_path = self.get_package_cache_path(True)
        return os.path.join(cache_path, prefix + 'rocketchat.json')

    # read ini config
    def read_config(self):
        self.dbg("Reading config")
        settings = self.load_settings()

        self.AUTH = str(settings.get("AUTH", "main"))
        self.USER_ID = str(settings.get("USER_ID", "main"))
        self.DOMAIN = str(settings.get("DOMAIN", "main"))

        if not self.DOMAIN or not self.USER_ID or not self.AUTH:
            self.dbg("Not configured",self.AUTH,self.USER_ID,self.DOMAIN)
            return False   
        return True

    def get_unique_name(self,item):
        name = item.get('name')
        username = item.get('username')
        label = name  # username is always set, for name that is not the case
        if name is not None :
            label = name + " (" + username + ")"  # the name itself is not unique        
        return label          