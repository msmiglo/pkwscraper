
from lxml import html
import re

import requests


WEB_ADRESS = "https://parlament2015.pkw.gov.pl"
PATH = "/index.html"
URL = WEB_ADRESS + PATH


class Voivodship:
    def __init__(self, code, name, geo):
        self.code = code
        self.name = name
        self.geo = geo

    @classmethod
    def from_html_element(cls, html_elem):
        '''print(dir(html_elem))
        print()
        print(html_elem.attrib)
        print()
        print(html_elem.getchildren())
        print()
        print(html_elem.getchildren()[0])
        print()
        print(html_elem.getchildren()[0].attrib)
        print()
        print(html_elem.getchildren()[0].attrib["rel"])
        print()
        print(html_elem.getchildren()[0].attrib["d"])
        print()'''
        #print(dir(html_elem.getchildren()))
        #print()

        #code = html_elem.code
        href_path = html_elem.attrib['xlink:href']
        code = re.findall('\d+', href_path)[0]
        '''print(code)
        print(type(code))'''

        #name = html_elem.name
        name = html_elem.getchildren()[0].attrib["rel"]

        #geo = html_elem.geo
        geo = html_elem.getchildren()[0].attrib["d"]

        return cls(code, name, geo)

    def __repr__(self):
        return (f"Voivodship, code: {self.code}, name: '{self.name}', "
                f"geo: '{self.geo[:10]}...{self.geo[-10:]}'")

    def to_record(self):
        return {
            "code": self.code,
            "name": self.name,
            "geo": self.geo
        }


def main():
    print(Voivodship(5, 2, "shtgrsnbgdrnygtdsnygtnyhdtnyhtnhjydthydt"))
    print()
    response = requests.get(URL)
    print(response)
    print(response.content[0:200])

    html_tree = html.fromstring(response.content)

    xpath_voivodships = '/html/body//div[@id="home"]//' \
                        'div[@class="home_content home_mapa"]//svg//a'
    voivodships_hrefs = html_tree.xpath(xpath_voivodships)
    print()
    print(len(voivodships_hrefs))
    print(voivodships_hrefs)

    voivodships = list(map(Voivodship.from_html_element, voivodships_hrefs))
    print()
    print(voivodships)

    '''
    aaa = '/html/body//div[@id="home"]//div[@class="home_content home_mapa"]' \
          '//svg//a/@*'
    bbb = '//a/path/@rel'
    ccc = '//a/path/@d'

    voivodships_ids = html_tree.xpath(aaa)
    print()
    print(voivodships_ids)
    '''





    "/html/body/div/div[4]/div/div[2]/div[2]/div[1]/svg/g/a[1]"

if __name__ == "__main__":
    main()
