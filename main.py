import streamlit as st
import requests
# import urllib.request
from bs4 import BeautifulSoup
import json


def get_keywords(stock, url, joins):
    HEADERS = {
        'User-Agent':"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36","Accept-Language": "en-US, en;q=0.5"
        }
    try:
        page = requests.get(url, headers = HEADERS)
        soup = BeautifulSoup(page.content, 'html.parser')
        if 'shutterstock' in url:
            script = soup.find('script', id="__NEXT_DATA__", type='application/json')
            for a in script:
                select = json.loads(a)
            keywords = [i for i in select['props']['pageProps']['asset']['keywords']]
        elif 'getty' in url:
            script = soup.find('script', type = 'application/json')
            results = json.loads(script.getText())
            kw_list = results['asset']['keywords']
            keywords = []
            for kw in kw_list:
                keywords.append(kw['text'])
        st.session_state['keywords'] = joins.join(keywords)
    except Exception as e:
        st.session_state['keywords'] = e
    return None

col1, col2 = st.columns([3,1])
selected_stock = col1.radio('Select PS',['Shutterstock','Getty'], horizontal= True,label_visibility='hidden')
if selected_stock == 'Shutterstock':
    col2.image('https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Shutterstock_logo.svg/351px-Shutterstock_logo.svg.png?20180715171416')
elif selected_stock == 'Getty':
    col2.image('https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Getty_Images_Logo.svg/207px-Getty_Images_Logo.svg.png?20180727163711')

st.markdown('Enter a search term to search:')
search_phrase = st.text_input('search string', key = 'SEARCH', label_visibility='hidden')
links = {
    'Getty':f"https://www.gettyimages.com/search/2/image?family=creative&phrase={search_phrase.replace(' ','%20')}&sort=mostpopular&mediatype=photography",
    'Shutterstock':f"https://www.shutterstock.com/search/{search_phrase.replace(' ','-')}?image_type=photo"
    }
st.write(f'[{links[selected_stock]}]({links[selected_stock]})')
st.markdown('Or enter the image URL:')
url = st.text_input('url', key = 'URL', label_visibility='hidden')
if selected_stock == 'Shutterstock' and url != '':
    url = url.replace('www.shutterstock.com/ru','www.shutterstock.com')

join_type = {'comma':', ','paragraph':'\n'}
joins = st.radio('label',join_type.keys(), horizontal= True)
if url != '':
    if st.button('Get Keywords'):
        get_keywords(selected_stock, url, join_type[joins])
if 'keywords' in st.session_state:
    if st.session_state['keywords']:
        st.text_area('Keywords:',st.session_state['keywords'], height=300)
