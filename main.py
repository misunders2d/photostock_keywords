import streamlit as st
from st_keyup import st_keyup
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import InvalidSessionIdException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import json
import re
import time
from openai import OpenAI
import os

AI_KEY = os.environ['AI_KEY']

st.set_page_config(page_title='Photostock Keywords', page_icon='media/favicon.png')

@st.cache_resource(show_spinner=False)
def get_driver():
    options = Options()
    options.add_argument('--disable-gpu')
    options.add_argument('--headless')
    options.add_argument('--disable-blink-features=AutomationControlled')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def get_keywords(stock, url):
    HEADERS = {
        "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OSX 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko)Chrome/71.0.3578.98 Safari/537.36",
        "Accept":"text/javascript,text/html,application/xhtml+xml,application/xml; q=0.9,image/webp,image/apng,*/*;q=0.8"
        }
    
    try:
        if 'shutterstock' in url:
            page = requests.get(url, headers = HEADERS)
            soup = BeautifulSoup(page.content, 'html.parser')
            script = soup.find('script', id="__NEXT_DATA__", type='application/json')
            for a in script:
                select = json.loads(a)
            keywords = [i for i in select['props']['pageProps']['asset']['keywords']]
        elif 'getty' in url:
            page = get_driver()
            page.get(url)
            time.sleep(5)
            soup = BeautifulSoup(page.page_source, 'html.parser')
            page.close()
            page.quit()
            scripts = soup.find('script', type = 'application/json')
            results = json.loads(scripts.getText())
            kw_list = results['asset']['keywords']
            keywords = []
            for kw in kw_list:
                keywords.append(kw['text'].lower())
        st.session_state['keywords'] = keywords
    except Exception as e:
        st.session_state['keywords'] = [str(e)]
    return st.session_state['keywords']

def ai_keywords(kws):
    client = OpenAI(api_key = AI_KEY)
    response = client.chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[
            {"role": "system", "content": "You are an assistant helping me work with photostock keywords"},
            {"role": "user", "content": f"Please disregard all previous context. Here is the list of keywords which are all merged together. Please separate each keyword with a comma:\n{kws}"},
            ]
            )
    return response.choices[0].message.content

col1, col2 = st.columns([3,1])
# selected_stock = col1.radio('Select PS',['Getty','Shutterstock','Adobe'], horizontal= True,label_visibility='hidden', index = 0)
selected_stock = col1.radio('Select PS',['Getty','Shutterstock'], horizontal= True,label_visibility='hidden', index = 0)
if selected_stock == 'Shutterstock':
    col2.image('https://upload.wikimedia.org/wikipedia/commons/thumb/c/cd/Shutterstock_logo.svg/351px-Shutterstock_logo.svg.png?20180715171416')
elif selected_stock == 'Getty':
    col2.image('https://upload.wikimedia.org/wikipedia/commons/thumb/a/ac/Getty_Images_Logo.svg/207px-Getty_Images_Logo.svg.png?20180727163711')
elif selected_stock == 'Adobe':
    col2.image('https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Adobe_Systems_logo_and_wordmark.svg/800px-Adobe_Systems_logo_and_wordmark.svg.png')

search_col1, search_col2 = st.columns([4,1])
search_col1.markdown('Enter a search term to search:')
search_phrase = st_keyup('search string', key = 'SEARCH', label_visibility='hidden')
# if search_col2.button('Clear'):
#     st.session_state['SEARCH'] = ''

links = {
    'Getty':f"https://www.gettyimages.com/search/2/image?family=creative&phrase={search_phrase.replace(' ','%20')}&sort=mostpopular&mediatype=photography",
    'Shutterstock':f"https://www.shutterstock.com/search/{search_phrase.replace(' ','-')}?image_type=photo",
    'Adobe':f"https://stock.adobe.com/search?k={search_phrase.replace(' ','+')}&search_type=usertyped"
    }
st.write(f'[{links[selected_stock]}]({links[selected_stock]})')
st.markdown('Or enter the image URL:')
url = st.text_input('url', key = 'URL', label_visibility='hidden')
if selected_stock == 'Shutterstock' and url != '':
    url = url.replace('www.shutterstock.com/ru','www.shutterstock.com')
elif selected_stock == 'Adobe' and url != '':
    url = url.replace('stock.adobe.com/ua','stock.adobe.com/')

join_type = {'comma':', ','paragraph':'\n'}
joins = st.radio('label',join_type.keys(), horizontal= True, label_visibility= 'hidden')
if url != '' and 'keywords' not in st.session_state:
    st.session_state['keywords'] = get_keywords(selected_stock, url)
if st.button('Reset') and 'keywords' in st.session_state:
    del st.session_state['keywords']
if joins and 'keywords' in st.session_state:
    st.text_area('results',join_type[joins].join(st.session_state['keywords']), height=300, label_visibility='hidden')
with st.expander('Process keywords'):
    kw_area = st.empty()
    kws = re.split('\n|,',kw_area.text_area('kws', '', height = 300, label_visibility='hidden'))
    if st.button('Format'):
        new_kws = ', '.join([x.lower() for x in kws if x != ''])
        kw_area.text_area('updated kws',new_kws, height = 300)
with st.expander('Convert from paragraphs to comma list', expanded = False):
    input_area = st.empty()
    convert_button_area = st.empty()
    button_col1, button_col2 = convert_button_area.columns([1,4])
    convert_button, clear_button = button_col1.button('Convert'), button_col2.button('Clear')
    st.session_state.initial_kws = input_area.text_area('Input list of keywords',height = 300)
    if clear_button:
        del st.session_state.initial_kws
    if convert_button:
        kw_list = st.session_state.initial_kws.split('\n')
        kw_list = [x.lower().replace(',','').strip() for x in kw_list if x != '']
        st.session_state.converted_kws = ', '.join(kw_list)
        input_area.text_area('Results:',st.session_state.converted_kws, height = 300)

with st.expander('Separate keywords with commas', expanded = True):
    input_area2 = st.empty()
    convert_button_area2 = st.empty()
    aibutton_col1, aibutton_col2 = convert_button_area2.columns([1,3])
    aiconvert_button, aiclear_button = aibutton_col1.button('Process keywords'), aibutton_col2.button('Clear', key = 'ai')
    st.session_state.ai_kws = input_area2.text_area('Input joined keywords',height = 300)
    if aiclear_button:
        del st.session_state.ai_kws
    if aiconvert_button:
        input_area2.text_area('Results:',ai_keywords(st.session_state.ai_kws), height = 300)