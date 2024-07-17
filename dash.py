import pymorphy3
import streamlit as st
import pickle
import pandas as pd
import copy 
import random
import os

from typing import Dict, List, Set
from reg_extractor_Lena import RegExpsLena
print("Libs loaded!")

# https://stackoverflow.com/questions/75410059/how-to-log-user-activity-in-a-streamlit-app

global history
history = dict()

# old version from xls file
# file_path = "LenaZenkoDash/n_grams.xls"
file_path = "LenaZenkoDash/key_words.pkl"
log_file = r"Log/log.pkl"

def format_df_from_key_words(key_words):
    table = {i: list(key_words[i].items()) for i in key_words}
    output = dict()
    keys = list(table.keys())
    for key in keys:
        df = pd.DataFrame(table[key], columns=["Выбранный фильтр", "Фраза"])
        output.update({key: df})
    return output
    
def save_log(update_, filename="log.pkl"):
    if "Log" not in os.listdir():
        os.mkdir("Log")
    if filename not in os.listdir("Log"):
        pickle.dump(update_, open(log_file, 'wb'))
    else:
        exist = pickle.load(open(log_file, 'rb'))
        exist.update(update_)
        pickle.dump(exist, open(log_file, 'wb'))

@st.cache_data
def load_key_words():
    morph = pymorphy3.MorphAnalyzer()
    class_ecz = RegExpsLena(morph)
    return class_ecz #, key_words

def get_ui(class_ecz): # key_words
    key_words = pickle.load(open(file_path, 'rb'))
    letters = [chr(i) for i in range(ord('a'), ord('z') + 1)]
    hash_ = ''.join(random.choices(letters, k = 32))
    
    st.header("Извлекаем сущности")
    st.subheader("Введите запрос")
    probaText = "кандидаты Иванов и Жирков из кадровых агентств и инсты с запланированными интервью за зиму 2023 для рекрутеров Бурлакова и Захаровой отклоненные из-за некомпетентности"
    title = st.text_input("Ваш запрос:", probaText)
    values, morphed, fio_get, dates_gets = class_ecz.extractNERS(title, key_words)
    st.markdown(":green[Нормализованный запрос -]" + " " + morphed)
    short_values = {i: list(values[i].keys()) for i in values}
    short_phrases = {i: list(values[i].values()) for i in values}
    
    st.subheader("Выделенные фильтры:")
    cols = st.columns(3, gap='medium')
    key_words_keys = list(key_words.keys())
    cnt = 0
    output1 = dict()
    for key in key_words_keys[:3]:
        with cols[cnt]:
            to_choose = list(key_words[key].keys())
            phrases = short_phrases[key]
            options = st.multiselect(f"Выбранные '{key}'", to_choose, short_values[key])
            output1.update({key: options, key + "_phrases": phrases})
        cnt = cnt + 1
    cols = st.columns(3, gap='medium')
    cnt = 0
    output2 = dict()
    for key in key_words_keys[3:]:
        with cols[cnt]:
            to_choose = list(key_words[key].keys())
            phrases = short_phrases[key]
            options = st.multiselect(f"Выбранные '{key}'", to_choose, short_values[key])
            output2.update({key: options, key + "_phrases": phrases})
        cnt = cnt + 1
     
    output1.update(output2)
    cols = st.columns(2, gap='medium')
    with cols[0]:
        date = st.date_input(
            "Выделенные даты",
            tuple(dates_gets),
            format="DD.MM.YYYY",
        )
        output1.update({"date": date})
    with cols[1]:
        funnc_join = lambda x: ", ".join([i.capitalize() for i in x])
        name_rec = st.text_input("Выделенные фамилии - рекрутер:", funnc_join(fio_get["рекрутер"]))
        output1.update({"Выделенные фамилии - рекрутер": name_rec})
        name_ruc = st.text_input("Выделенные фамилии - руководитель:", funnc_join(fio_get["руководитель"]))
        output1.update({"Выделенные фамилии - руководитель": name_ruc})
        name_can = st.text_input("Выделенные фамилии - кандидат:", funnc_join(fio_get["кандидат"]))
        output1.update({"Выделенные фамилии - кандидат": name_can})
        
    cols = st.columns(2, gap='large')
    with cols[0]:
        if st.button("Зафиксировать сущности"):
            history.update({title + "_origin": output1})
            save_log(history)
    with cols[1]:
        if st.button("Исправил(-а) сущности"):
            history.update({title + "_fixed": output1})
            save_log(history)
            
    # log saving
    try:
        to_save_history = pickle.load(open(log_file, 'rb'))
        shp = len(to_save_history)
        to_save_history = pd.DataFrame(to_save_history).transpose().to_csv().encode("utf-8")
        st.download_button('Скачать лог', data=to_save_history, file_name="Log.csv", mime="text/csv")
        st.write(f"Размер лога: {shp}")
    except FileNotFoundError:
        st.write("Размер лога: 0")
        
    # dataframes widget
    st.subheader("Ключевые фразы (Им.п., м.р., ед.число)")
    keys = list(key_words.keys())
    dfs = format_df_from_key_words(key_words)
    tabs_ = st.tabs(keys)
    deditors = []
    for i in range(len(keys)):
        with tabs_[i]:
            df = dfs[keys[i]]
            df["Фраза"] = df["Фраза"].apply(lambda x: ", ".join(x))
            deditor = st.data_editor(df, hide_index=True, use_container_width=True, num_rows="dynamic")
            deditors.append(deditor)
    if st.button("Сохранить таблицу"):
        di_save = dict()
        cnt = 0
        for deditor in deditors:
            di = dict(zip(deditor["Выбранный фильтр"].values, deditor["Фраза"].values))
            di = {i: di[i].split(", ") for i in di}
            di_save.update({keys[cnt]: di})
            cnt = cnt + 1
        pickle.dump(di_save, open(file_path, 'wb'))
    
    # to download 
    to_download = pd.DataFrame()
    cnt = 0
    for deditor in deditors:
        deditor_cp = copy.copy(deditor)
        deditor_cp["type"] = keys[cnt]
        cnt = cnt + 1
        to_download = pd.concat([to_download, deditor_cp], axis=0)
    to_download = pd.DataFrame(to_download).reset_index(drop=True).to_csv().encode("utf-8")
    st.download_button('Скачать таблицу ключевых фраз', data=to_download, file_name="KeyPhrases.csv", mime="text/csv")
        
    
def main():
    class_ecz = load_key_words() #, key_words
    get_ui(class_ecz) # key_words

st.set_page_config(layout="wide")
main()
