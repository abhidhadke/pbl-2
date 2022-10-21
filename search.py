import requests
from bs4 import BeautifulSoup

class Gamespot:
  def __init__(self):
        self.url = 'https://www.gameinformer.com/search?keyword='
        

  def key_words_search_words(self, user_message):
    words = user_message.split()
    keywords = '+'.join(words)
    return keywords

  def search(self, keywords):
    response = requests.get(self.url+keywords)
    content = response.content
    soup = BeautifulSoup(content, 'html.parser')
    result_links = soup.findAll('a')
    return result_links
      
  def send_link(self, result_links, keywords): 
    send_link = set()
    for link in result_links:
        text = link.text.lower()
        if keywords in text:
          game_link = 'https://www.gameinformer.com' + link.get('href')
          send_link.add(game_link)
          
    return send_link