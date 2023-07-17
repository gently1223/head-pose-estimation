# (A) INIT
# (A1) LOAD MODULES
from flask import Flask, render_template, request, make_response, session
import pandas as pd
import os
import numpy as np
import openai
from openai.embeddings_utils import cosine_similarity
import time
from openpyxl import load_workbook
from werkzeug.utils import secure_filename
openai.api_key = "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"###input your api key
 
# (A2) FLASK SETTINGS + INIT
HOST_NAME = "localhost"
HOST_PORT = 80
app = Flask(__name__)
# app.debug = True
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
# Define folder to save uploaded files to process further
UPLOAD_FOLDER = os.path.join('static', 'uploads')
DOWNLOAD_FOLDER = os.path.join('static', 'downloads')
app.config['UPLOAD'] = UPLOAD_FOLDER
app.config['DOWNLOAD'] = DOWNLOAD_FOLDER
# Define allowed files (for this example I want only csv file)
ALLOWED_EXTENSIONS = {'xlsx'}

# @app.route('/')
# def index():
#     return render_template('index_read.html')

my_model = 'text-embedding-ada-002'
def get_embedding(my_input) -> list[float]:
    result = openai.Embedding.create(
      model = my_model,
      input = my_input
    )
    return result['data'][0]['embedding']

@app.route('/',  methods=("POST", "GET"))
def index():
    if request.method == 'GET':
      return render_template('index_upload.html')
    if request.method == 'POST':
        # upload file flask
        uploaded_df = request.files['uploaded-file']
 
        # Extracting uploaded data file name
        data_filename = secure_filename(uploaded_df.filename)
 
        # flask upload file to database (defined uploaded folder in static path)
        uploaded_df.save(os.path.join(app.config['UPLOAD'], data_filename))
        
        final_labels=['LISTED ON PD or NOT', 'DEVELOPER NAME', 'PROJECT NAME', 'LISTING ID', 'BEDROOMS', 'Min Price AED', 'Max Price AED',
        'Min Size SQF', 'Max Size SQF', 'DLD %', 'Downpayment %', 'Durring Construction %', 'Handover %', 'Handover Date', 'Post Handover %', 'Post Handover Months Number', 'Status']
        vector1s=pd.read_csv("embeddings.csv",  header= None)
        vector1_list=[]
        for i in range(len(vector1s)):
            vector1_list.append(vector1s.loc[i,1:].to_list())
        df_all = pd.read_excel(os.path.join(app.config['UPLOAD'], data_filename), header=None, sheet_name= None)
        final_df=pd.read_excel("final.xlsx", header= None)
        final_df.rename(columns= final_df.iloc[0], inplace= True)
        final_df=final_df[1:]

        print(list(df_all.keys()))
        for key in list(df_all.keys()):
            if key != 'hiddenSheet':
                df=df_all[key]
                label_row_index = 100
                ################################
                df_num = df.applymap(lambda x: 1 if isinstance(x, str) else 0)
                row_sums = df_num.sum(axis=1)
                row = df.loc[row_sums.idxmax()]
                first_not_nan_index = row.first_valid_index()
                df=df.loc[:, first_not_nan_index:]
                #################################
                for row_index, row in df.iterrows():
                    row = df.loc[row_index]
                    string_frequency = row.astype(str).value_counts()
                    # print(string_frequency)
                    for cell in row:
                        if isinstance(cell, str) and not df.isna().loc[row_index].any():
                            label_row_index = row_index
                            break
                    if label_row_index != 100: 
                        break
                df = df.iloc[label_row_index :].reset_index(drop=True)         
                df.rename(columns=df.iloc[0],inplace= True)
                new_df=df[1:]
                new_df.reset_index(drop=True)

                # print(new_df)

                common_columns = final_df.columns.intersection(new_df.columns)
                print(common_columns)
                if list(common_columns)!=[]:
                # ## remake new_df with common columns between final and new.
                    new_df_common_columns = df[common_columns][1:]
                    # print(new_df_common_columns)
                    new_df=new_df_common_columns.reindex(final_df.columns, axis=1)
                # ## join two dataframe , keep all the final columns and just add common columns in new dataframe
                    final_df = pd.concat([final_df, new_df], axis=0)
                    print(final_df)
                # # ## Save into "out.xlsx" file
        ########################################
        
        final_df.to_excel(os.path.join(app.config['DOWNLOAD'], 'outut.xlsx'), index=False)
        # Storing uploaded file path in flask sessionw3
        session['Downloaded_data_file_path'] = os.path.join(app.config['DOWNLOAD'], 'outut.xlsx')
 
        return render_template('index_upload.html')
 

# (B) DEMO - READ EXCEL & GENERATE HTML TABLE
@app.route("/show_data")
def showData():
  # (B1) OPEN EXCEL FILE + WORKSHEET

  # Retrieving uploaded file path from session
  data_file_path = session.get('Downloaded_data_file_path', None)
  book = load_workbook(data_file_path)
  sheet = book.active
  # (B2) PASS INTO HTML TEMPLATE
  return render_template("excel_table.html", sheet=sheet)

 
# (C) START
if __name__ == "__main__":
  app.run(HOST_NAME, HOST_PORT)