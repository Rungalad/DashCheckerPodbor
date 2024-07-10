import time 
import re
from itertools import chain, permutations
import pandas as pd

class InitialRegsDates:
    def __init__(self, sent):
        # print("v 1.1")
        self.sent = sent
        ye = time.asctime().split(' ')[-1][-1]
        self.currenttime = ["настоящ[ие]е время", 
                            "на?с?т?[.,]? ?[/\\-]? ?вр[.]?", 
                            "сейчас",
                            "текущ[а-я]{2,3} момента?"]
        # (?:[1-4]-?(?:[ыои]й)?|первый|второй|третий|четвертый|последний)?, ?(?:202[0-{ye}])?
        self.quarter_var = f"квартал."
        self.mnths_lit = {"декабр[ьяе]": "12", 
                 "ноябр[ьяе]": "11",
                 "октябр[ьяе]": "10",
                 "сентябр[ьяе]": "09",
                 "август[ае]": "08",
                 "июл[ьяе]": "07",
                 "июн[ьяе]": "06",
                 "ма[йяе]": "05",
                 "апрел[ьяе]": "04",
                 "март[ае]?": "03",
                 "феврал[ьяе]": "02",
                 "январ[ьея]": "01"}
        sp = " *?[-\\/_.] *?"
        
        self.dates_fotmat = [f"(?:[0123]?[0-9]{sp})?[01][0-9]{sp}202[0-{ye}]", 
                             f"202[0-{ye}]{sp}[01]?[0-9](?:{sp}[0123]?[0-9])?"
                            ]
    
    @staticmethod
    def dates_clean(date):
        date = re.compile(r'[-\/_. ]+').sub("-", date)
        date_splited = date.split("-")
        if len(date_splited) == 2 and len(date_splited[0]) == 4:
            date = date + "-01"
        elif len(date_splited) == 2 and len(date_splited[1]) == 4:
            date = f"{date_splited[1]}-{date_splited[0]}-01"
        else:
            pass
        if len(date_splited) == 3 and len(date_splited[-1]) == 4:
            date = f"{date_splited[2]}-{date_splited[1]}-{date_splited[0]}"
        else:
            pass 
        return date
    
    def get_yaer_final_hope(self, mode='only_year'):
        # определение года - в том случае если нет никаких дат
        current = pd.to_datetime(time.asctime())
        year_reg0 = re.compile(r"(201[6-9]|202[0-4])").findall(self.sent)
        year_reg1 = re.compile(r"(?:это[а-я]{0,2}|текущ[а-я]{2,3}|настоящ[а-я]{2,3}) год").findall(self.sent)
        year_reg2 = re.compile(r"(?:прошл[а-я]{2,3}|предыдущ[а-я]{2,3}) год").findall(self.sent)
        year = None
        if year_reg0:
            year = int(year_reg0[0])
        if year_reg1:
            year = current.year
        if year_reg2:
            year = current.year - 1
        if not year:
            year = current.year
            
        if mode == 'only_year':
            return year
        else:
            if year == current.year:
                return [pd.to_datetime(f"{year}-01-01"), pd.to_datetime(time.asctime())]
            else:
                return [pd.to_datetime(f"{year}-01-01"), pd.to_datetime(f"{year}-12-31")] 
    
    def get_half_yaer(self):
        # полугодия    
        di_q_num = {"(?:1-?(?:о[ем])?|перв[а-я]{2}) полугод": 1,
                    "(?:2-?(?:о[ем])?|втор[а-я]{2}) полугод": 2}
        val = [di_q_num[i] for i in di_q_num  if re.compile(i).findall(self.sent)]
        if val:
            val = int(val[0])
        else:
            return []
        year = self.get_yaer_final_hope()
        half = (val == 1)*"01" + (val == 2)*"07"
        date1 = pd.to_datetime(f"{year}-{half}-01")
        date2 = date1 + pd.offsets.MonthEnd(6)
        return [date1, date2]
    
    def get_last_mnth(self):
        # то же самое сделаем для времен года        
        get_mnth = re.compile(r"(?:последн[а-я]{2,3}) месяц[а-я]{0,1}").findall(self.sent)
        if len(get_mnth) > 0:
            return [(pd.Timestamp('today') - pd.offsets.MonthEnd(1)).normalize(),
                    pd.Timestamp('today').normalize()]
        else:
            return []
    
    def get_quarter(self):
        # то же самое сделаем для времен года        
        di_q_num = {"(?:1-?(?:ый|ом)?|перв[а-я]{2}) квартал": 1,
                    "(?:2-?(?:о[йм])?|втор[а-я]{2}) квартал": 2,
                    "(?:3-?(?:ий|ь?ем)?|трет[а-я]{2,3}) квартал": 3,
                    "(?:4-?(?:ый|ом)?|четверт[а-я]{2}|последн[а-я]{2}) квартал": 4}
        val = [di_q_num[i] for i in di_q_num  if re.compile(i).findall(self.sent)]
        # print(val)
        if val:
            val = int(val[0])
        else:
            return []
        year = self.get_yaer_final_hope()
        quarter = (val == 1)*"01" + (val == 2)*"04" + (val == 3)*"07" + (val == 4)*"10"
        date1 = pd.to_datetime(f"{year}-{quarter}-01")
        date2 = date1 + pd.offsets.MonthEnd(3)
        #print(date1, date2)
        return [date1, date2]
    
    def get_season(self):
        # то же самое сделаем для времен года        
        di_q_num = {"(?:зимой|зим[ау])": 1,
                    "(?:весной|весн[ау])": 2,
                    "(?:летом?)": 3,
                    "(?:осенью?)": 4}
        val = [di_q_num[i] for i in di_q_num  if re.compile(i).findall(self.sent)]
        # print(val)
        if val:
            val = int(val[0])
        else:
            return []
        year = self.get_yaer_final_hope()
        season = (val == 1)*"12" + (val == 2)*"03" + (val == 3)*"06" + (val == 4)*"09"
        if val == 1:
            year = year - 1
        date1 = pd.to_datetime(f"{year}-{season}-01")
        date2 = date1 + pd.offsets.MonthEnd(3)
        #print(date1, date2)
        return [date1, date2]
            
    def preregs_dates(self):
        for key in self.mnths_lit:
            #print(key, '->', re.compile(key).findall(self.sent))
            self.sent = re.compile(key).sub(self.mnths_lit[key] + "-", self.sent)
            
        dates = []
        year = self.get_yaer_final_hope()
        for variant in self.dates_fotmat:
            seek = re.compile(variant).findall(self.sent)
            #print(variant, '->', seek)
            if not seek:
                continue
            for found in seek:
                dates.append(found) 
                self.sent = self.sent.replace(found, "DATES")
        addit_dates = re.compile(r"(?:1[0-2]|0[1-9])-").findall(self.sent)
        addit_dates = [dt + f"{year}" for dt in addit_dates]
        if addit_dates:
            for dt in addit_dates:
                dates.append(dt)
        #print("dates1: ", dates)
        dates = list(map(lambda x: self.dates_clean(x), dates))
        #print("dates2: ", dates)
        
        for curtime in self.currenttime:
            cuttimefound = re.compile(curtime).findall(self.sent)
            if cuttimefound:
                dates.append(pd.to_datetime(time.asctime()))
                for variants_curtime in cuttimefound:
                    self.sent = self.sent.replace(variants_curtime, "DATES")
        #print("Dates in sent: ", dates) 
        dates = list(map(pd.to_datetime, dates))
        return sorted(dates)
