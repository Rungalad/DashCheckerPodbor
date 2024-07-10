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

global history
history = dict()

# old version from xls file
# file_path = "LenaZenkoDash/n_grams.xls"
file_path = "LenaZenkoDash/key_words.pkl"

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
        pickle.dump(update_, open(r"Log/log.pkl", 'wb'))
    else:
        exist = pickle.load(open(r"Log/log.pkl", 'rb'))
        exist.update(update_)
        pickle.dump(exist, open(r"Log/log.pkl", 'wb'))

@st.cache_data
def load_key_words():
    morph = pymorphy3.MorphAnalyzer()
    class_ecz = RegExpsLena(morph)
    # old version from xls file
    # key_words = class_ecz.get_regexps(file_path)
    # key_words = pickle.load(open(file_path, 'rb'))
    return class_ecz #, key_words

def get_ui(class_ecz): # key_words
    key_words = pickle.load(open(file_path, 'rb'))
    letters = [chr(i) for i in range(ord('a'), ord('z') + 1)]
    hash_ = ''.join(random.choices(letters, k = 32))
    
    st.header("Извлекаем сущности")
    st.subheader("Введите запрос")
    probaText = "кандидаты из кадровых агентств и инсты  с запланированными интервью за зиму 2023 для Иванова и Захаровой отклоненные из-за некомпетентности"
    title = st.text_input("Ваш запрос:", probaText)
    values, morphed, fio_get, dates_gets = class_ecz.extractNERS(title, key_words)
    st.markdown(":green[Нормализованный запрос -]" + " " + morphed)
    if len(fio_get) > 0:
        fio_get = [i[0][1].capitalize() for i in fio_get]
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
        name = st.text_input("Выделенные ФИО:", ", ".join(fio_get))
        output1.update({"name": name})
        
    cols = st.columns(2, gap='large')
    with cols[0]:
        if st.button("Зафиксировать сущности"):
            history.update({title + "_origin": output1})
            # print(history)
            save_log(history)
    with cols[1]:
        if st.button("Исправил(-а) сущности"):
            history.update({title + "_fixed": output1})
            # print(history)
            save_log(history)
     
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
        
    
def main():
    class_ecz = load_key_words() #, key_words
    get_ui(class_ecz) # key_words

st.set_page_config(layout="wide")
main()