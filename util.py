from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
import pandas as pd
import numpy as np
import json
import re
from pydantic import BaseModel,Field
import asyncio
from tqdm.asyncio import tqdm_asyncio
from tqdm import tqdm
from dotenv import load_dotenv
from pathlib import Path
import os
from functools import reduce,partial

parallel_calls=3
model_name='alibayram/medgemma:27b'
# ollama_url = "http://hsuweb.kemri-wellcome.org:11434"  # replace with the IP of the computer running Ollama
ollama_url = "http://127.0.0.1:11434"  # replace with the IP of the computer running Ollama
# load environmental variables
load_dotenv(".env")
data_folder=Path(os.getenv("DATA_FOLDER"))
result_folder=Path(os.getenv("RESULTS_FOLDER"))

cin=pd.read_parquet(data_folder/"cin_labeled 1.parquet")
cin['age_mths']=cin['age_mths'].map(lambda x: np.nan if (x<=0) | (x>18*12) else x,na_action='ignore')
cin['age_years']=cin['age_years'].map(lambda x: np.nan if (x<=0) | (x>18) else x,na_action='ignore')
cin['age_days']=cin['age_days'].map(lambda x: np.nan if (x<1) | (x>31) else x,na_action='ignore')
cin['age']=cin[['age_mths','age_years']].apply(lambda x: x[0] if x[0]>11 else np.nansum([x[0],12*x[1]]),axis=1)
cin.loc[cin['age']==0 ,'age']=cin.loc[cin['age']==0 ,'age_days']/31
cin=cin.loc[(cin['age']>0) & (cin['age']< (10 *12))].reset_index().copy()


free_text_vars=['dsc_dx1_other_1','dsc_dx1_other_2','dsc_dx1_other_3','dsc_dx1_other_4',
                'dsc_dx1_other_5','dsc_dx1_other_6','dsc_dx2_other_1','dsc_dx2_other_2',
                'dsc_dx2_other_3','dsc_dx2_other_4','dsc_dx2_other_5','dsc_dx2_other_6',
                'dsc_dx2_other_7','dsc_dx2_other_8']


diag_long=pd.melt(cin[['id']+free_text_vars],id_vars=['id'])
diag_long=diag_long.dropna()
diag_long['diag_text']=diag_long['value'].str.lower().str.strip()

diag_long.to_parquet(result_folder/"diag_long_freetext.parquet")


unique_diags=diag_long['diag_text'].unique()
diag_data=pd.DataFrame({'diag_text':unique_diags})

# def concat_text(x):
#     x2=x.dropna()
#     x2=[i for i in x2 if i != ""]
#     return " | ".join(x2)
#
# cin['diag_text']=cin[free_text_vars].apply(lambda row: concat_text(row),axis=1)
#
# cin=cin.loc[~cin['diag_text'].isna() & (cin['diag_text'] != ''),['id','age','diag_text']].copy().reset_index(drop=True)




class DiagnosisCategories(BaseModel):
    Malaria: bool
    Tuberculosis: bool
    HIV_AIDS: bool
    Sickle_Cell_Disorders: bool
    Neonatal_Conditions: bool
    Enteric_Infections: bool
    Respiratory_Infections: bool
    Meningitis: bool
    Measles: bool
    Congenital_Genetic: bool
    Asthma: bool
    Chronic_Kidney_Disease: bool
    Malnutrition: bool
    Diabetes_Mellitus: bool
    Epilepsy_Convulsive: bool
    Neoplasms: bool
    Injuries_Drowning_Poisoning: bool
    Anaemia: bool
    Sepsis: bool
    Others: bool

model=ChatOllama(model=model_name,temperature=0.,base_url=ollama_url)
# model with structured output
structured_model=model.with_structured_output(DiagnosisCategories)





system_prompt = """
You are a health records officer that converts unstructured medical diagnoses—written in free text or ICD-9/ICD-10/ICD-11 codes—into structured boolean indicators for predefined disease categories.

YOUR TASK:
Given any diagnosis input (free text, ICD code, or both), determine whether each condition category is present.
A category is True if:
- the diagnosis explicitly mentions the disease, OR
- synonyms or clinical equivalents appear, OR
- an ICD-9, ICD-10, or ICD-11 code that corresponds to the condition is present.
If there is no evidence, return False.

CONDITION DEFINITIONS:

1. Malaria (eg malaria, plasmodium, P. falciparum)
2. Tuberculosis (eg TB, PTB, pulmonary tuberculosis)
3. HIV AIDS (eg HIV, AIDS, PLHIV)
4. Sickle Cell Disorders (eg sickle cell disease, SCD, sickle cell anemia, vaso-occlusive crisis)
5. Neonatal Conditions (eg prematurity, neonatal sepsis, birth asphyxia, neonatal jaundice, RDS)
6. Enteric Infections (eg diarrhea, gastroenteritis, cholera, dysentery, dehydration)
7. Respiratory Infections (eg pneumonia, bronchiolitis, URTI, LRTI, SARI)
8. Meningitis (eg meningitis, meningoencephalitis)
9. Measles (eg measles, rubeola)
10. Congenital Genetic (eg congenital heart disease, Down syndrome, cleft palate, genetic disorder)
11. Asthma (eg asthma, acute asthma exacerbation, wheezing responsive to bronchodilators)
12. Chronic Kidney Disease (eg CKD, ESRD, chronic renal failure)
13. Malnutrition (eg SAM, MAM, kwashiorkor, marasmus)
14. Diabetes Mellitus (eg diabetes, DKA, T1DM, T2DM)
15. Epilepsy Convulsive (eg epilepsy, seizure, convulsion, status epilepticus)
16. Neoplasms (eg leukemia, lymphoma, Wilms tumor, neuroblastoma, childhood cancers)
17. Injuries Drowning Poisoning (eg fractures, burns, trauma, road traffic injury, poisoning, ingestion, drowning)
18. Anaemia (eg anaemia, anemia, severe anaemia, iron deficiency, Hb low)
19. Sepsis (eg sepsis, septicemia, septic shock, severe sepsis, bacteremia)
20. Others (any diagnosis or ICD code not captured by the above categories)



Return ONLY a JSON object with this exact structure:

{{
  "Malaria": false,
  "Tuberculosis": false,
  "HIV_AIDS": false,
  "Sickle_Cell_Disorders": false,
  "Neonatal_Conditions": false,
  "Enteric_Infections": false,
  "Respiratory_Infections": false,
  "Meningitis": false,
  "Measles": false,
  "Congenital_Genetic": false,
  "Asthma": false,
  "Chronic_Kidney_Disease": false,
  "Malnutrition": false,
  "Diabetes_Mellitus": false,
  "Epilepsy_Convulsive": false,
  "Neoplasms": false,
  "Injuries_Drowning_Poisoning": false,
  "Anaemia": false,
  "Sepsis": false,
  "Others": false
}}
"""

prompt_template = ChatPromptTemplate.from_messages(
        [("system", system_prompt), ("user", "{text}")]
    )


sema = asyncio.Semaphore(parallel_calls)   # limit to 2 parallel calls from what is defined by parralel_calls

async def call_llm(text):
    prompt_text = text.replace('\t', " ")
    prompt = prompt_template.invoke({'text': prompt_text})
    async with sema: # If the limit is reached, wait here until another task finishes then run ainvoke.
        return await model.ainvoke(prompt)



async def run_all(diags):
    tasks = [asyncio.create_task(call_llm(i)) for i in diags]
    # results = await asyncio.gather(*tasks)
    results = []
    for f in tqdm_asyncio.as_completed(tasks, total=len(tasks)):
        result = await f
        results.append(result.content)
    return results


diags=diag_data['diag_text'].tolist()#[:5]
print("Running LLM ....")
model_results=asyncio.run(run_all(diags))
with open(result_folder/"raw_diagnoses.json", "w") as f:
    json.dump(model_results, f)

extracted_diagnoses={}
error_visits=[]
print("Formatting model results...")
for text,result in tqdm(zip(diags, model_results),total=len(diags)):
    # text=row.get('diag_text')
    # # ensure consistent key for missing text
    # key = text
    # if key in extracted_diagnoses.keys():
    #     continue
    # if not text or pd.isna(text):
    #     extracted_diagnoses[key]=None
    #     continue
    #
    #
    # prompt_text=text.replace('\t'," ")
    # prompt = prompt_template.invoke({'text': prompt_text})
    # result = structured_model.invoke(prompt)

    # robust parsing + logging
    try:
        raw = getattr(result, "content", None) or str(result)
        # strip triple backticks if present
        raw = re.sub(r'```(?:json)?', '', raw).strip('` \n')
        result_dict = json.loads(raw)


        extracted_diagnoses[text] = result_dict
    except Exception as e:
        # save raw output for debugging
        raw = getattr(result, "content", None) or str(result)
        print(f"PARSE ERROR record={text} error={e}")
        print("RAW OUTPUT:", raw[:1000])
        error_visits.append(text)
        extracted_diagnoses[text] = {"parse_error": True, "raw": raw, "record_id": text}


with open(result_folder/"extracted_diagnoses.json", "w") as f:
    json.dump(extracted_diagnoses, f)

# system=pd.DataFrame(extracted_diagnoses.values())
