import requests
from bs4 import BeautifulSoup
from queue import Queue
from datetime import datetime

# fun!
from rich.console import Console
from simple_term_menu import TerminalMenu
from art import tprint

import csv


class ArchiveTree():
    def __init__(self, amount, *args, **kwargs):
        self.folders = Queue()
        self.details = []
        self.console = Console()
        self.amount = amount

        directory = requests.get("https://deprecated.archivesportaleurope.net/web/guest/directory?p_p_id=directory_WAR_Portal&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=directoryTree&p_p_cacheability=cacheLevelPage&p_p_col_id=column-1&p_p_col_pos=2&p_p_col_count=3&_=1673100574492")
        countries = directory.json()[0]["children"]
        if amount != "":
            countries = countries[:int(amount)]
        for country in countries:
            country_code, key = country["countryCode"], country["key"]
            entries = requests.get(f"https://deprecated.archivesportaleurope.net/web/guest/directory?p_p_id=directory_WAR_Portal&p_p_lifecycle=2&p_p_state=normal&p_p_mode=view&p_p_resource_id=directoryTreeAi&nodeId={key}&countryCode={country_code}").json()
            for entry in entries:
                self.dispatch(entry)

    def dispatch(self, entry):
        self.console.log(f"Extracting info for {entry['title']}, {entry['countryCode']}")
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

                    self.console.log("Found email! -> " + str2)  
                    writer.writerow({"country_code": detail["countryCode"], "institution": detail["title"], "email": str2, "address": address.text.replace("\n", "")})
            

    def extract_emails(self):
        with self.console.status("[bold green]Exracting info...", spinner="runner") as status:
            self.iterate()
            self.dump_csv()

if __name__ == '__main__':
    tprint("APE  Email  Extractor", font="small")
    options = ["run the extractor", "exit"]
    terminal_menu = TerminalMenu(options, title="What do you want to do?")
    menu_entry_index = terminal_menu.show()
    if options[menu_entry_index] == options[0]:
        amount = input("How much countries do you want parse? (Leave blank for all): ")
        print(amount)
        starttime = datetime.now()
        tree = ArchiveTree(amount=amount)
        tree.extract_emails()
        with open("emails.csv", "r") as f:
            amount = sum(1 for line in f)
            time = datetime.now() - starttime
            print(f"\N{High Voltage Sign} Done with {amount} emails found in {time.total_seconds()}s!")
        
    elif options[menu_entry_index] == options[1]:
        print("Bye!")
        exit

# print("Done!")