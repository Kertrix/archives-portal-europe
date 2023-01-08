import requests
from bs4 import BeautifulSoup
from queue import Queue

import csv


class ArchiveTree():
    def __init__(self, *args, **kwargs):
        self.folders = Queue()
        self.details = []

        directory = requests.get("https://deprecated.archivesportaleurope.net/web/guest/directory?p_p_id=directory_WAR_Portal&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=directoryTree&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_pos=2&p_p_col_count=3&_=1673100574492")
        countries = directory.json()[0]["children"]
        for country in countries[:2]:
            country_code, key = country["countryCode"], country["key"]
            entries = requests.get(f"https://deprecated.archivesportaleurope.net/web/guest/directory?p_p_id=directory_WAR_Portal&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=directoryTreeAi&nodeId={key}&countryCode={country_code}").json()
            for entry in entries:
                self.dispatch(entry)

    def dispatch(self, entry):
        print(entry)
        if "isFolder" in entry:
            self.folders.put(entry)
        else:
            self.details.append(entry)

    def iterate(self):
        while not self.folders.empty():
            folder = self.folders.get()
            items = requests.get(f"https://deprecated.archivesportaleurope.net/web/guest/directory?p_p_id=directory_WAR_Portal&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=directoryTreeAi&nodeId={folder['key']}&countryCode={folder['countryCode']}").json()
            for item in items:
                self.dispatch(item)
    
    def size(self):
        print("Folder size:", self.folders.qsize())
        print("Detail size:", len(self.details))

    def dump_csv(self):
        with open('emails.csv', 'w') as f:
            writer = csv.DictWriter(f, fieldnames=["country_code", "institution", "email", "address"], delimiter=";")
            writer.writeheader()

            for detail in self.details:
                page = requests.get(f"https://deprecated.archivesportaleurope.net/web/guest/directory?p_p_id=directory_WAR_Portal&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=aiDetails&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_pos=2&p_p_col_count=3&id={detail['aiId']}")
        
                soup = BeautifulSoup(page.content, "html.parser")
                emails = soup.select('a[href^=mailto]')
                address = soup.find("td", class_="address")

                for email in emails:
                    href=email['href']
                    try:
                        str1, str2 = href.split(':')
                    except ValueError:
                        break

                    writer.writerow({"country_code": detail["countryCode"], "institution": detail["title"], "email": str2, "address": address.text.replace("\n", "")})


    def extract_emails(self):
        self.iterate()
        self.dump_csv()

tree = ArchiveTree()

tree.extract_emails()

# code = "AT"
# country = "country_30" 
# entries = requests.get(f"https://deprecated.archivesportaleurope.net/web/guest/directory?p_p_id=directory_WAR_Portal&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=directoryTreeAi&nodeId={country}&countryCode={code}").json()

# def get_folder(key, code):
#     folder = requests.get(f"https://deprecated.archivesportaleurope.net/web/guest/directory?p_p_id=directory_WAR_Portal&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=directoryTreeAi&nodeId={key}&countryCode={code}").json()
#     return folder

# for entry in entries:
#     if "isFolder" in entry:
#         folders1 = get_folder(entry['key'], entry['countryCode'])
#         for folder1 in folders1:
#             if "isFolder" in folder1:
#                 folder2 = get_folder(folder1["key"], folder1["countryCode"])
#                 for a in folder2:
#                     print(a)

