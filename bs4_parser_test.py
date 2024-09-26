import csv
import os
import time
import requests

from itertools import cycle

from bs4 import BeautifulSoup
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter

from fake_useragent import UserAgent


load_dotenv()


class MainParser:
    """
    Парсер нединамичного сайта с помощью bs4.
    """

    data = []

    def make_request(
            self,
            url: str,
            proxies: dict,
            headers: dict,
            adapter: HTTPAdapter) -> None:

        """
        Для осуществления запросов к сайту.
        Настраивается сессия, headers, прокси.
        """

        stop_switching_proxy = False

        with requests.Session() as session:
            session.encoding = 'utf-8'
            session.mount('http://', adapter)
            session.mount('https://', adapter)
            session.headers.update(headers)
            # session.proxies.update(proxies)

            proxy_pool = cycle(proxies)
            print('Настраиваем прокси...')

            for i in range(1, len(proxies) + 1):
                proxy = next(proxy_pool)
                session.proxies.update(proxy)

                try:
                    response = session.get(url, timeout=10)
                    print(f'Запрос № {i}: успешно выполнен!')
                    # print(
                    #     f'TYPE OF THE RESPONSE {type(response)} and {type(response.text)}')

                    self.operations_bs4(response)
                    stop_switching_proxy = True

                except requests.exceptions.RequestException:
                    print(f'Request {i}: Failed switching {proxy}')
                else:
                    if stop_switching_proxy:
                        break

    def operations_bs4(self, obj_response: requests.Response) -> None:
        """
        Метод для выполнения операций с помощью bs4.
        """

        soup = BeautifulSoup(obj_response.text, 'lxml')
        main_container = soup.find('div', {'class': 'content'})
        org_list = main_container.find(
            'div', {'class': 'card w-100 p-1 p-lg-3 mt-1'}).find(
                'div', {'class': 'org_list'})
        self.data.append(org_list)
        company_blocks = org_list.find_all('p')

        # ВОЗРАЩАЕТ NONE, если объект не найден
        target_companies = []
        for company_element in company_blocks:
            closed_company = company_element.find('span', {'class': 'status_0'})
            # print(f'{closed_company} and type: {type(closed_company)}')

            if not closed_company:
                target_companies.append(company_element)
            else:
                continue

        company_names, links = [], []
        base_url = 'https://www.list-org.com'
        for target_company in target_companies:
            name = ''.join(
                target_company.find('span').text.split('"ИНН')[0].split('"'))
            link = target_company.find('a').get('href')
            company_names.append(name)
            links.append(f'{base_url}{link}')

        # УКАЗАТЬ ПУТЬ ДЛЯ СОХРАНЕНИЯ ФАЙЛА 
        file_path_to_save = input(
            'Укажите путь для сохранения файла с учетом его названия(.csv)...')
        self.save_to_excel(file_path_to_save, company_names, links)

    def save_to_excel(
                self,
                file_path: str,
                company_names: list,
                links: list) -> None:
        """
        Метод для сохранения данных в файл excel.
        """

        headers = ['№', 'Название', 'Ссылка']
        indexs = range(1, len(company_names) + 1)
        data = zip(indexs, company_names, links)
        with open(file_path, 'w', encoding='utf-8-sig', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(headers)
            for d in data:
                writer.writerow(d)


if __name__ == '__main__':
    web_parser = MainParser()
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml',
        'Connection': 'keep-alive'
    }
    proxy_with_auth = [
        {'https': os.getenv('PROXY_1')},
        {'https': os.getenv('PROXY_2')},
        {'https': os.getenv('PROXY_3')},
        {'https': os.getenv('PROXY_4')}
    ]
    adapter = HTTPAdapter(
        pool_connections=10, pool_maxsize=20, pool_block=True)
    url = 'https://www.list-org.com/list?okved2=41.20'
    time_start = time.time()
    web_parser.make_request(url, proxy_with_auth, headers, adapter)
    time_end = time.time()
    print(f'Скорость выполнения запроса: {round(time_end - time_start, 2)}')
    # print(web_parser.data)
    # print(web_parser.companies_data)