import requests
import os
import re
import sys
import json
import datetime
import time

"""
CTFD Challenge Scrapper & Downloader
by : https://github.com/bardiz12
python3 port + extra feature: https://github.com/nk521
Usage : python ctfds.py [CTFD-URL] [output_dir] [USERNAME] [PASSWORD] [SUPPRESS S]
"""


class CTFDScrapper():
    def __init__(self, base_url):
        self.user = {"username": None, "password": None}
        self.base_url = base_url[0:-1] if base_url[-1] == "/" else base_url
        self.request = requests.Session()
        self.suppress = False

    def login(self, username, password):
        self.user['username'] = username
        self.user['password'] = password
        # self.post("/login",sel)
        token = self.__accessLoginPage()
        try_login = self.post(
            "/login", {"name": username, "password": password, "nonce": token})
        if ("Your username or password is incorrect" in try_login.text):
            raise Exception('Wrong username/password')

    def __accessLoginPage(self):
        page = self.get("/login")
        token = re.findall(
            "<input id=\"nonce\" name=\"nonce\" type=\"hidden\" value=\"(.*?)\">", page.text)
        return token[0]

    def get(self, path):
        return self.request.get(self.base_url + path)

    def post(self, path, data):
        return self.request.post(self.base_url + path, data)

    def apiGet(self, path):
        return self.get("/api/v1"+path)

    def download(self, directory_name, suppress):
        directory_name = os.path.join(
            directory_name, directory_name + '-' + '-'.join(str(datetime.datetime.now()).split()))
        self.suppress = suppress

        json_challs = self.apiGet('/challenges').text
        challenges = json.loads(json_challs)
        exported = {}

        if challenges.get("data"):
            if os.path.isdir(directory_name):
                if os.path.isfile(directory_name):
                    raise Exception(directory_name +
                                    " is not a valid directory")
            else:
                os.mkdir(directory_name)
        else:
            return

        for chall in challenges['data']:
            if not self.suppress:
                print("Downloading " + chall['name'] + " - " +
                      chall['category']+" ["+str(chall['value'])+" pts]")

            if chall['category'] not in exported:
                exported[chall['category']] = {}

            if os.path.isdir(directory_name + "/" + chall['category']) == False:
                os.mkdir(directory_name + "/" + chall['category'])

            chall_info = json.loads(self.apiGet(
                "/challenges/"+str(chall['id'])).text)['data']
            chall_dir = directory_name + "/" + \
                chall['category'] + "/" + chall['name'] + \
                " ["+str(chall['value'])+" pts]"

            os.mkdir(chall_dir)

            output = open(chall_dir + "/" + "README.md", 'w')
            output.write("Description:\n")
            output.write(chall_info['description'] + "\nHints:\n")

            for hint in chall_info:
                if "content" in hint:
                    output.write(hint.content + "\n")

            output.close()
            file_dir = chall_dir + "/" + "files"

            if len(chall_info['files']) > 0:
                os.mkdir(file_dir)

            for file_url in chall_info['files']:
                file_name = file_url.split("?token")[0].split("/")[-1]

                if not self.suppress:
                    print("     Downloading " + file_name)

                file_data = self.get(file_url).content
                file = open(file_dir + "/" + file_name, 'wb')
                file.write(file_data)
                file.close()

            exported[chall['category']][chall['name']] = chall_info

        if not self.suppress:
            print("Writing challs.json")
        challs = open(directory_name + "/" + "challs.json", 'w')
        json.dump(exported, challs, indent=4, sort_keys=True)
        challs.close()


if(len(sys.argv) < 3):
    print(
        "Usage : python ctfds.py CTFD-URL output_dir [USERNAME] [PASSWORD] [SUPPRESS S]")
    exit()

ctf_url = sys.argv[1]
output_dir = sys.argv[2]

if len(sys.argv) > 3:
    username = sys.argv[3]
else:
    username = input("Username: ")

if len(sys.argv) > 4:
    password = sys.argv[4]
else:
    password = input("Password: ")

if len(sys.argv) > 5:
    suppress = sys.argv[5]
    if suppress in ["S", "s"]:
        suppress = True
else:
    suppress = False

ctfds = CTFDScrapper(ctf_url)

print("CTFD Challenges Scrapper")

while True:
    try:
        try:
            ctfds.login(username, password)

        except Exception as e:
            print(e)
            exit()

        ctfds.download(output_dir, suppress)
        time.sleep(5)

    except KeyboardInterrupt:
        break
