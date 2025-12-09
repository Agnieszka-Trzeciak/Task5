import pandas as pd
import requests
import csv
from io import StringIO,BytesIO
import numpy as np
from outliers import smirnov_grubbs as grubbs
import matplotlib.pyplot as plt
import datetime
import streamlit as st
import os
from pdf_functions import *

pdf = PDF('P','mm','A4')
pdf.set_auto_page_break(auto = True, margin = 15)
pdf.add_page()
pdf.add_title()

st.title("Task5 Trzeciak Agnieszka")
st.set_page_config(layout="wide")

col1, col2 = st.columns(2)

col1.markdown("<h4 style='text-align: center;'>Outlier detection settings</h4>", unsafe_allow_html=True)
Z_score_test_arg = int(col1.text_input("Z-score test range",value = 3))

col11,col12 = col1.columns(2)
Moving_avg_test_window = int(col11.text_input("Moving average window size",value = 4))
Moving_avg_test_arg = float(col12.text_input("Moving average percentage",value = 0.5))
Grubbs_alpha = float(col1.text_input("Grubbs' test alpha",value = 0.05))

col2.markdown("<h4 style='text-align: center;'>Display settings</h4>", unsafe_allow_html=True)
pol_degree = int(col2.selectbox("Degree of fit polynomial",[1,2,3,4]))
Chosen_type = col2.selectbox("Plot type", ["Line","Bar","Stacked"]).lower()
Temp,col2m,Temp = col2.columns([1,4,1])
col2m.button("Refresh data source",width='stretch')

st.divider()

Sheet_ID = '1MLWhmBbvCv53OldMdOoqUH7oP93dMQU-zRDtt-qoCy8'
Url = f'https://docs.google.com/spreadsheets/d/{Sheet_ID}/export?format=csv'

response_Data_Source = requests.get(Url+f'&range=C6:I7')
Mines_names = []
for row in csv.reader(StringIO(response_Data_Source.text)):
    Mines_names+=[name for name in row if name!='']

Mines_data = pd.read_csv(Url+f'&gid=1239218550&range=AS4:BG1002',header=None).dropna(how='all').dropna(how='all',axis=1)
Mines_data.columns = Mines_names+["Total"]
Start_date = datetime.date.fromisoformat(pd.read_csv(Url+f'&range=D4',header=None).values[0][0])

Mine_Summary = [[float(np.mean(mine_data)),
                 float(np.std(mine_data)),
                 float(np.median(mine_data)),
                 float(np.percentile(mine_data,75)-np.percentile(mine_data,25))]
                 for mine_data in [Mines_data[mine_name] for mine_name in Mines_names+["Total"]]]

IQR_test_arg = 1.5
Outlier_DataFrames = []

st.markdown("<h1 style='text-align: center;'>Mines data</h1>", unsafe_allow_html=True)
i = 0
for mine_name in Mines_names+["Total"]:
    st.divider()
    col1, col2 = st.columns([2,3])
    col1.markdown(f"<h2 style='text-align: center;'>{mine_name}</h2>", unsafe_allow_html=True)

    col11,col12 = col1.columns(2)
    Name = ["Mean daily output","Standard deviation","Median","Interquartile range"]
    for idx in range(2):
        col11.metric(label=f"{Name[2*idx]}", value=str(round(Mine_Summary[i][2*idx],2)))
        col12.metric(label=f"{Name[1+2*idx]}", value=str(round(Mine_Summary[i][1+2*idx],2)))
    
    mine_data = Mines_data[mine_name]
    
    Max_IQR_outliers = (mine_data[pd.Series(mine_data)>np.percentile(mine_data,75)+
                             IQR_test_arg*(np.percentile(mine_data,75)-np.percentile(mine_data,25))])
    Min_IQR_outliers = (mine_data[pd.Series(mine_data)<np.percentile(mine_data,25)-
                             IQR_test_arg*(np.percentile(mine_data,75)-np.percentile(mine_data,25))])
    Max_Z_score_outliers = (mine_data[(mine_data-np.mean(mine_data))/np.std(mine_data)>Z_score_test_arg])
    Min_Z_score_outliers = (mine_data[(-mine_data+np.mean(mine_data))/np.std(mine_data)>Z_score_test_arg])
    Max_Moving_avg_outliers = (mine_data[(mine_data-(mine_data.rolling(Moving_avg_test_window).sum()/Moving_avg_test_window))
                                      /(mine_data.rolling(Moving_avg_test_window).sum()/Moving_avg_test_window)>Moving_avg_test_arg])
    Min_Moving_avg_outliers = (mine_data[(-mine_data+(mine_data.rolling(Moving_avg_test_window).sum()/Moving_avg_test_window))
                                      /(mine_data.rolling(Moving_avg_test_window).sum()/Moving_avg_test_window)>Moving_avg_test_arg])
    Max_Grubbs_outliers = (mine_data[grubbs.max_test_indices(list(mine_data), alpha=Grubbs_alpha)])
    Min_Grubbs_outliers = (mine_data[grubbs.min_test_indices(list(mine_data), alpha=Grubbs_alpha)])
    
    def test_data_to_df(Start_date,data,test_name,outliner_type_max = True):
        df = pd.DataFrame(data)
        df['Outliner type'] = 'Spike' if outliner_type_max else 'Drop'
        df['Date'] = [Start_date + datetime.timedelta(days=x) for x in data.index]
        df['Test'] = test_name
        df.columns = ['Value','Outlier type','Date','Test']
        return df[['Date','Value','Outlier type','Test']]
    Test_names = ["IQR","Z-score","Moving average","""Grubbs'"""]
    Max_tests = [Max_IQR_outliers,Max_Z_score_outliers,Max_Moving_avg_outliers,Max_Grubbs_outliers]
    Min_tests = [Min_IQR_outliers,Min_Z_score_outliers,Min_Moving_avg_outliers,Min_Grubbs_outliers]
    Outlier_DataFrames.append(pd.concat([pd.concat([test_data_to_df(Start_date,Max_tests[i],Test_names[i],True) for i in range(4)]),
                            pd.concat([test_data_to_df(Start_date,Min_tests[i],Test_names[i],False) for i in range(4)])],axis=0).sort_values(by='Date'))

    col1.markdown(f"<h3 style='text-align: center;'>Outliers</h3>", unsafe_allow_html=True)
    col1.write(Outlier_DataFrames[-1].drop_duplicates('Date')[['Date','Value','Outlier type']].sort_values('Date'))

    with col2:
        fig,ax = plt.subplots()
        if Chosen_type == 'line':
            ax.plot([Start_date + datetime.timedelta(days=x) for x in range(len(mine_data))],mine_data,color='green')
            ax.scatter(Outlier_DataFrames[-1]['Date'],Outlier_DataFrames[-1]['Value'],color='red')
            polynomial = np.poly1d(np.polyfit(range(len(mine_data)), mine_data, pol_degree))
            ax.plot([Start_date + datetime.timedelta(days=x) for x in range(len(mine_data))],polynomial(range(len(mine_data))),color='blue')
            ax.legend(["Mine output","Outlier","Polynomial"])
        elif Chosen_type=='stacked' and mine_name == "Total":
            bottom_arg_green = [0 for i in range(len(mine_data))]
            step = 0.8/len(Mines_names)
            greens = [(0.1,1-step*i,0.1) for i in range(len(Mines_names))]
            for i in range(len(Mines_names)):
                ax.bar([Start_date + datetime.timedelta(days=x) for x in range(len(mine_data))],Mines_data[Mines_names[i]],bottom = bottom_arg_green,color=greens[i])
                bottom_arg_green += Mines_data[Mines_names[i]]
            ax.scatter(Outlier_DataFrames[-1]['Date'],Outlier_DataFrames[-1]['Value'],color='red')
            polynomial = np.poly1d(np.polyfit(range(len(mine_data)), mine_data, pol_degree))
            ax.plot([Start_date + datetime.timedelta(days=x) for x in range(len(mine_data))],polynomial(range(len(mine_data))),color='blue')
            ax.legend(['Outlier','Polynomial']+Mines_names if len(Outlier_DataFrames[-1])>0 else ['Polynomial']+Mines_names)
        else:
            ax.bar([Start_date + datetime.timedelta(days=x) for x in range(len(mine_data))],mine_data,color='green')
            ax.bar(Outlier_DataFrames[-1]['Date'],Outlier_DataFrames[-1]['Value'],color='red')
            polynomial = np.poly1d(np.polyfit(range(len(mine_data)), mine_data, pol_degree))
            ax.plot([Start_date + datetime.timedelta(days=x) for x in range(len(mine_data))],polynomial(range(len(mine_data))),color='blue')
            ax.legend(['Polynomial','Mine output','Outlier'] if len(Outlier_DataFrames[-1])>0 else ['Polynomial','Mine output'])
        ax.set_title(f'{mine_name} mine output')
        ax.set_xlabel('Date')
        ax.set_ylabel('Output')
        ax.tick_params(rotation=45)
        st.pyplot(fig)
        img_buffer = BytesIO()
        fig.savefig(img_buffer,format='png',dpi=fig.dpi*2, bbox_inches='tight')
        img_buffer.seek(0)
    pdf.mine_information(mine_name,Mine_Summary[i],Outlier_DataFrames[-1],img_buffer)
    i+=1
for i in range(len(Mines_names+["Total"])):
    pdf.outlier_information((Mines_names+["Total output"])[i], Outlier_DataFrames[i])   
pdf_buffer = BytesIO(pdf.output())
pdf_buffer.seek(0)
#pdf_bytes = pdf.output(dest='S').encode('utf-8')

st.divider()
st.download_button(label = "Download pdf report",data=pdf_buffer, file_name = 'Report.pdf', mime="application/pdf",width='stretch')











