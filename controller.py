from selenium import webdriver
from selenium.webdriver.chrome.options import Options

import time

from selenium.webdriver.remote.webelement import WebElement

# test
class Controller:

    def __init__(self, mafia):
        options = Options()
        options.add_argument("--log-level=3")
        options.headless = True
        self.driver = webdriver.Chrome(executable_path='./browserdrivers/chromedriver', options=options)

        self.choose_mafia = mafia
        self.sanctiuni = dict()

    def read_invoiri(self):
        self.driver.get('https://forum.b-zone.ro/topic/98445-green-street-bloods-%C3%AEnvoiri-pass-request/')

        nav_row = self.driver.find_element_by_class_name('ipsPagination')
        last_page_number = nav_row.get_attribute('data-pages')

        self.driver.get(f'https://forum.b-zone.ro/topic/98445-green-street-bloods-%C3%AEnvoiri-pass-request/?page={last_page_number}')

        posts = list()
        for raw_post in self.driver.find_elements_by_tag_name('article'):
            temp_post = ForumPost(raw_post)
            posts.append(temp_post)
            print('')


    def read_war_score(self, war_count):
        all_war_link = 'https://www.rpg2.b-zone.ro/wars/viewall/gang/greenstreet'
        self.driver.get(all_war_link)

        # load war table
        table = self.driver.find_element_by_css_selector('#contentPage > div.tableFull > table')
        
        rows = table.find_elements_by_tag_name('tr')
        rows.remove(table.find_element_by_class_name('headerRow'))

        wars = list()

        # load individual rows
        for row in rows[:4]:
            war_obj = War(row)
            wars.append(war_obj)

        today_date = time.strftime('%d.%m.%Y', time.gmtime())
        hours = {   1 : '20:30',
                    2 : '21:00',
                    3 : '21:30',
                    4 : '22:00'     }
        war_date = f'{today_date} {hours.get(war_count)}'

        war_found = None

        for war in wars:
            if (war.get_war_date() == war_date): 
                # print('war found')
                # print(f'link {war.war_link}')
                war_found = war

        mafia_table = self.find_mafia_members(war_found)

        for member in mafia_table:
            if member.get_player_kills() == 0 and member.get_player_deaths() == 0 and member.get_player_seconds() == 0:
                # print(f'Player {member.get_player_name()} - Nu a fost la war')
                continue
            self.sanctiuni.update(self.calculate_member_stats(member))

    def find_mafia_members(self, war):
        self.driver.get(war.get_war_link())

        table_id = ''
        if war.get_turf_attacker() == 'Green Street Bloods':
            table_id = 'viewWarAttackerPlayers' 
        elif war.get_turf_defender() == 'Green Street Bloods':
            table_id = 'viewWarDefenderPlayers'

        members_table = self.driver.find_element_by_id(table_id).find_element_by_tag_name('table').find_elements_by_tag_name('tr')
        # members_table.remove(members_table.find_element_by_class_name('headerRow'))
        members_table.pop(0)

        members = list()
        for member in members_table:
            temp_member = WarPlayer(member) 
            members.append(temp_member)
        return members

    def calculate_member_stats(self, member):
        sactiune = list()
        player_kda = member.get_player_kills() - member.get_player_deaths()

        if player_kda <= -5:
            # print(f'Player {member.get_player_name()} - Amenda - Scor mai mic de -5')
            sactiune.append('Amenda (-5)')
        if player_kda <= -10:
            # print(f'Player {member.get_player_name()} - FW - Scor mai mic de -10')
            sactiune.append('FW (-10)')
        if member.get_player_seconds() < 800:
            # print(f'Player {member.get_player_name()} - Amenda - Secunde mai putine de 800') 
            sactiune.append('Amenda (secunde < 800)')

        return { member.get_player_name() : sactiune }

    def print_evidenta(self):
        evidenta_date = time.strftime('%d %b %Y', time.gmtime())
        # print title
        print(f'Evidenta war {evidenta_date}')

        # print invoiri
        self.read_invoiri()

        # print inactivitati

        # print sactiuni
        # print('Sanctiuni: ')
        # for member in self.sanctiuni.keys():
        #     if not self.sanctiuni[member]:
        #         continue
        #     print(f'{member} : {" ".join(self.sanctiuni[member])}') 

    def quit(self):
        self.driver.quit()

class ForumPost:
    def __init__(self, web_element : WebElement):
        # author name
        author_pane = web_element.find_element_by_tag_name('aside')
        self.author = author_pane.find_element_by_tag_name('a').text

        self.post_time = web_element.find_element_by_tag_name('time')

        self.raw_content = list(element.text for element in web_element.find_elements_by_tag_name('p'))
        # TODO: add support for multiple invoiri
        print(self.raw_content)
        self.content = Invoire(self.raw_content)

    def __str__(self):
        return (f'Post Author: {self.author}\n'
                f'Time: {self.post_time.get_attribute("datetime")}\n'
                f'Content: {self.content}')

class Invoire:
    def __init__(self, content_dump):
        self.one_line = False
        self.invoire_retrasa = False
        self.invoiri_acceptate = False

        if len(content_dump) == 1:
            print('oneliner')
            self.one_line = True
            self.one_line_text = content_dump[0]
            if self.one_line_text.lower().contains('retrag'):
                self.invoire_retrasa = True
            elif self.one_line_text.lower().contains('Invoiri acceptate'):
                self.invoiri_acceptate = True
        else:
            print('invoire')
            self.nickname = content_dump[0]
            self.rank = content_dump[1]
            self.tip = content_dump[2]
            self.data = content_dump[3]
            self.motiv = content_dump[4]
            self.total_invoiri = content_dump[5]
            self.altele = content_dump[6]

    def __str__(self):
        if self.one_line:
            return self.one_line_text
        else:
            return (f'{self.nickname}\n'
            f'{self.rank}\n'
            f'{self.tip}\n' 
            f'{self.data}\n'
            f'{self.motiv}\n'
            f'{self.total_invoiri}\n'
            f'{self.altele}\n')

class WarPlayer:
    def __init__(self, web_element: WebElement):
        self.row_elements = web_element.find_elements_by_tag_name('td')
        
        self.player_name = self.row_elements[0].text
        self.player_kills = int(self.row_elements[1].text)
        self.player_deaths = int(self.row_elements[2].text)
        self.player_seconds = int(self.row_elements[3].text)
        
    def __str__(self):
        return (f'Player: {self.player_name}\n'
                f'Kills: {self.player_kills} - Deaths: {self.player_deaths}\n'
                f'Seconds on turf: {self.player_seconds}')

    def get_player_kills(self):
        return self.player_kills

    def get_player_deaths(self):
        return self.player_deaths

    def get_player_seconds(self):
        return self.player_seconds

    def get_player_name(self):
        return self.player_name

class War:

    def __init__(self, web_element: WebElement):
        self.row_elements = web_element.find_elements_by_tag_name('td')
        
        self.turf_location = self.row_elements[0].text
        self.turf_attacker = self.row_elements[1].text
        self.turf_attacker_score = self.row_elements[2].text
        self.turf_defender_score = self.row_elements[3].text
        self.turf_defender = self.row_elements[4].text
        self.war_time_interval = self.row_elements[5].text
        self.war_date = self.row_elements[6].text
        self.war_link = self.row_elements[7].find_element_by_tag_name('a').get_attribute('href')
        
    def __str__(self):
        return (f'War on turf {self.turf_location}\n'
        f'Attacker: {self.turf_attacker} - Score {self.turf_attacker_score}\n'
        f'Defender: {self.turf_defender} - Score {self.turf_defender_score}\n'
        f'Time Interval: {self.war_time_interval} - Date: {self.war_date}\n'
        f'War link: {self.war_link}')

    def get_turf_attacker(self):
        return self.turf_attacker

    def get_turf_defender(self):
        return self.turf_defender

    def get_war_link(self):
        return self.war_link

    def get_war_date(self):
        return self.war_date
