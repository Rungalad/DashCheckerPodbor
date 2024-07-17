import re
import os
import copy
import pandas as pd
import numpy as np
import pymorphy3
import pandas as pd

from src.dates_reg import InitialRegsDates

class RegExpsLena(InitialRegsDates):
    def __init__(self, morph, sent=""):
        print("v 0.2")
        self.key_words = {}
        self.names = {'Surn': "Фамилия"}
        self.morph = morph
        super().__init__(sent)
        
    def func_lemm(self, x):
        return self.morph.normal_forms(x)[0]
    
    def func_fio(self, sent, brackets):
        output_di = {"рекрутер": [], "руководитель": [], "кандидат": []}
        for type_human, left, right in brackets:
            output = [word for word in sent[left: right] if 'Surn' in str(self.morph.tag(word)[0])]
            output_di.update({self.func_lemm(type_human): output})
        return output_di

    def sent2normal_form(self, sent, reg=r"[a-zа-я-/]+", drop_wrods=['кандидат'], dontMorph=['оффер']):
        sent = sent.lower()
        sent = sent.replace("ё", "е")
        prefix_reg = r"(?:рекрутер[а-я]{0,2}|руководител[а-я]{0,2}|кандидат[а-я]{0,2})"
        found_key_words = re.compile(prefix_reg).findall(sent)
        sent = re.compile(reg).findall(sent)
        found_key_words_index = sorted([[i, sent.index(i), len(sent)]  for i in found_key_words], key=lambda x: x[1])
        found_key_words_index_brackets = []
        if len(found_key_words_index) > 1:
            for i in range(len(found_key_words_index) - 1):
                val = copy.copy(found_key_words_index[i])
                val[-1] = found_key_words_index[i + 1][1]
                found_key_words_index_brackets.append(val)
            found_key_words_index_brackets.append(found_key_words_index[-1])
        print("found_key_words_index_brackets: ", found_key_words_index_brackets)
        fios = self.func_fio(sent, found_key_words_index_brackets)
        print("fios: ", fios)
        sent = [self.func_lemm(i) if i not in dontMorph else i for i in sent]
        sent = list(filter(lambda word: word not in drop_wrods, sent))
        sent = " ".join(sent)
        return sent, fios

    def get_regexps(self, filePath=r"LenaZenkoDash/n_grams.xls"):
        
        xl = pd.ExcelFile(filePath)
        self.sheet_names = xl.sheet_names
        key_words = {}
        for sheet in self.sheet_names[3:]:
            print(sheet)
            q = pd.read_excel(filePath, sheet_name=sheet, header=1)
            if sheet == 'причины отклонения':
                q.rename(columns={"причины отклонений_фразы для фильтрации": 'фразы для фильтрации',
                                  "причины отклонений": "параметр"}, inplace=True)
            elif sheet == 'источники':
                q1 = q[['источники', 'источники_фразы для фильтрации']]
                q2 = q[['группы источников', 'группа источников_фразы для фильтрации']]
                q1.rename(columns={"источники": "параметр",
                                  "источники_фразы для фильтрации": 'фразы для фильтрации'}, inplace=True)
                q2.rename(columns={"группы источников": "параметр",
                                  "группа источников_фразы для фильтрации": 'фразы для фильтрации'}, inplace=True)
                q = pd.concat([q1, q2], axis=0)
            q['фразы для фильтрации'] = q['фразы для фильтрации'].apply(lambda x: str(x).split("\n"))
            value = dict(zip(q['параметр'].values, q['фразы для фильтрации'].values))
            # приведение к нормальной форме
            value = {i: [self.sent2normal_form(j)[0] for j in value[i]] for i in value}
            # отработка коротких фраз
            value = {i: [j if len(j) > 2 else r"(?:^|[^а-яa-z0-9])" + j + r"(?:[^а-яa-z0-9]|$)" 
                         for j in value[i]] for i in value}
            key_words.update({sheet: value})
        return key_words

    def extract_dates(self, sent):
        halfyear = self.get_half_yaer()
        quarter = self.get_quarter()
        season = self.get_season()
        mnth = self.get_last_mnth()

        if halfyear:
            return halfyear
        if quarter:
            return quarter
        elif season:
            return season
        elif mnth:
            return mnth
        else:
            val = self.preregs_dates()
            if not val:
                return []
            if len(val) == 1:
                val = [val[0], val[0] + pd.offsets.MonthEnd(0)]
            elif len(val) > 2:
                val = val[:2]
            else:
                pass
            return val

    def extractNERS(self, sent, key_words):
        self.sent = sent
        dates = self.extract_dates(sent)
        sent, fio = self.sent2normal_form(sent)
        extracted = {}
        for subner in key_words:
            extracted.update({subner: {}})
            for subkey in key_words[subner]:
                val = [re.compile(phrase).findall(sent) for phrase in key_words[subner][subkey]]
                val = [found for found in val if len(found) > 0]
                if len(val) > 0:
                    extracted[subner][subkey] = val 
        return extracted, sent, fio, dates

# key_words = get_regexps(filePath=filePath)
