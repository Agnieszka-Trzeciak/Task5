from fpdf import FPDF
import pandas as pd
import datetime

class PDF(FPDF):
    def add_title(self):
        self.set_font('times','B',20)
        self.cell(0,10,'Weyland-Yutani mines raport',ln=True, align='C')
        self.ln()
    def sub_title(self,text):
        self.set_font('times','B',18)
        self.cell(0,10,text,ln=True, align='C')
    def add_plot(self,mine_name):
        self.image(mine_name.replace(" ","_")+".png",w=self.w*0.9)
    def add_metrics(self,mine_summary):
        self.set_font('times','B',14)
        self.cell(0,10,'Metrics:',ln=True)
        information = ["Mean daily output","Standard deviation","Median","Interquartile range"]
        self.set_font('times','',12)
        for i in range(2):
            self.cell(80,10,f'{information[2*i]}: {round(mine_summary[2*i],2)}',align='L')
            self.cell(80,10,f'{information[2*i+1]}: {round(mine_summary[2*i+1],2)}',align='L')
            self.ln()
    def add_outliers(self,all_outliers):
        self.set_font('times','B',14)
        self.cell(0,10,'Outliers:',ln=True)
        self.set_font('times','',12)
        if len(all_outliers)>=1:        
            with self.table() as table:
                row = table.row()
                row.cell('Date')
                row.cell('Value')
                row.cell('Outlier type')
                for data_row in all_outliers.drop_duplicates('Date').iterrows():
                    row = table.row()
                    for datum in data_row[1][['Date','Value','Outlier type']]:
                        row.cell(str(datum))
            self.ln()
        else:
            self.cell(0,10,"None detected",ln=True)
    def mine_information(self,mine_name,mine_summary,outliers):
        self.sub_title(mine_name)
        self.add_metrics(mine_summary)
        self.add_outliers(outliers)
        self.add_plot(mine_name)
        self.add_page()
    def outlier_information(self,mine_name,outliers):
        Test_names = ["IQR","Z-score","Moving average","""Grubbs'"""]
        Already_done = []
        if len(outliers)>0:
            self.sub_title(f'{mine_name} outliers')
            Unique_dates = outliers.drop_duplicates('Date')
            for date_index in range(len(Unique_dates)):
                series_len = 0
                if Unique_dates['Date'].values[date_index] not in Already_done:
                    for i in range(1,len(Unique_dates)):
                        if (Unique_dates['Date'].values[date_index]+datetime.timedelta(days=i) in Unique_dates['Date'].values):
                            if Unique_dates[Unique_dates['Date']==datetime.timedelta(days=i)+Unique_dates['Date'].values[date_index]]['Outlier type'].values:
                                series_len+=1
                            else:
                                break
                        else:
                            break
                    if series_len == 0:
                        self.set_font('times','B',12)
                        self.cell(0,8,f"""On {Unique_dates['Date'].values[date_index]}: {Unique_dates['Outlier type'].values[date_index]}""",ln=True)
                        self.set_font('times','',12)
                        self.cell(0,8,f"""Detected by tests: {", ".join(outliers[outliers['Date']==Unique_dates['Date'].values[date_index]]['Test'].unique())}""",ln=True)
                        self.ln()
                    else:
                        self.set_font('times','B',12)
                        self.cell(0,8,f"""From {Unique_dates['Date'].values[date_index]} to {Unique_dates['Date'].values[date_index]+datetime.timedelta(days=series_len)}: {Unique_dates['Outlier type'].values[date_index]}""",ln=True)
                        self.set_font('times','',12)
                        self.cell(0,8,f"Detected by tests:",ln=True)
                        Already_done += [Unique_dates['Date'].values[date_index]+datetime.timedelta(days=x) for x in range(series_len+1)]
                        with self.table() as table:
                            row = table.row()
                            row.cell('Date')
                            for test_name in Test_names:
                                row.cell(test_name)
                            for date in Already_done[-series_len-1:]:
                                row = table.row()
                                row.cell(str(date))
                                for test_name in Test_names:
                                    if test_name in outliers[outliers['Date']==date]['Test'].values:
                                        row.cell("X",align='C')
                                    else:
                                        row.cell(" ")
                        self.ln()

                
            
