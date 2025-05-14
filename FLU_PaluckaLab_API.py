#!/bin/python

import sys, time, json, csv, pandas as pd
from openai import AzureOpenAI, RateLimitError, APIError, APIConnectionError
import openai

csvOutput = []

from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
) 

client = AzureOpenAI(
    api_version="",
    azure_endpoint="",
    api_key = "",
)

genesDF = pd.read_csv('Input_Genelist.csv')
genesDF = genesDF['Genes']
#genesDF = genesDF['Genes'].iloc[1:5]
for row,gene in genesDF.items():

    ############################################
    ## KEEP THIS FOR TESTING TO REDUCE COSTS
    #if row == 3:
        #break 
    ############################################
 
    time.sleep(1)

    print(gene)

    system0 = "Assistant is an intelligent chatbot designed to help users answer questions about genomics and systems biology." \
            "The answers must be precise, scientific, and accurate. " \
            "Please utilize scientific sources such as PubMed (https://pubmed.ncbi.nlm.nih.gov/), MGI (https://www.informatics.jax.org/), and Google Scholar (https://scholar.google.com/) " \
            "for answers before sourcing anything else.  Please respond in JSON format, using the JSON key that is specified." 
    
    system1 = "Assistant is an intelligent chatbot designed to help users answer questions about genomics and systems biology." \
            "The answers must be precise, scientific, and accurate. " \
            "Please utilize scientific sources such as PubMed (https://pubmed.ncbi.nlm.nih.gov/), MGI (https://www.informatics.jax.org/), and Google Scholar (https://scholar.google.com/) " \
            "for answers before sourcing anything else.  Please respond in JSON format, using the JSON key that is specified." \
            "Score the questions using an integer from 0 to 10, with 0 indicating no evidence and 10 indicating very strong evidence." \
            "Use the following additional criteria for scoring:" \
            "0 - No evidence found" \
            "1-3 - Very limited evidence" \
            "4-6 - Some evidence, but needs validation or is limited to certain conditions" \
            "7-8 - Good evidence" \
            "9-10 - Strong evidence"

    user0 = "For the gene " + gene + " please give me the response in JSON format answering the following questions." \
           "What is the gene name? JSON Key: gene_name." \
           "A two sentence summary of the gene. JSON Key: summary." 
           
    user1 = "For the gene " + gene + " please give me the response in JSON format answering the following questions." \
           "Score the following statements from 0 to 10: " \
           "Is the " + gene + " gene specifically associated with the biology of the airway epithelium? JSON Key: bio_airway_epi." \
           "Is the " + gene + " gene specifically associated with the biology of basal cells within the airway epithelium? JSON Key: bio_basal_airway_epi." \
           "Is the " + gene + " gene specifically associated with the biology of goblet cells within the airway epithelium? JSON Key: bio_goblet_airway_epi." \
           "Is the " + gene + " gene specifically associated with the biology of ciliated cells within airway epithelium? JSON Key: bio_ciliated_airway_epi." 
    
    user2 = "For the gene " + gene + " please give me the response in JSON format answering the following questions." \
           "Score the following statements from 0 to 10: " \
           "Is the " + gene + " gene involved in mediating the influenza virus-induced increase in mucus production and airway blockage within airway epithelium? JSON Key: mucus_production." \
           "Is the " + gene + " gene implicated in influenza virus-mediated ciliated cell damage in the airway epithelium? JSON Key: ciliated_cell_damage." \
           "Is the " + gene + " gene involved in mediating influenza virus attachment and entry within the airway epithelium? JSON Key: virus_attachment." \
           "Is the " + gene + " gene implicated in the process of influenza virus replication within the airway epithelium? JSON Key: virus_replication." 
    
    user3 = "For the gene " + gene + " please give me the response in JSON format answering the following questions." \
           "Score the following statements from 0 to 10: " \
           "Is the " + gene + " gene involved in mediating influenza virus egress? JSON Key: virus_egress." \
           "Is the " + gene + " gene implicated in the tissue damage and impairment of the airway epithelium barrier function? JSON Key: tissue_damage_and_impairment." \
           "Is the " + gene + " gene involved in conferring resistance to influenza virus infection? JSON Key: virus_registance." \
           "Is the " + gene + " gene involved in mediating the innate immune response in the airway epithelium following in vitro influenza virus infection? JSON Key: innate_immune_virus." 
    
    user4 = "For the gene " + gene + " please give me the response in JSON format answering the following questions." \
           "Score the following statements from 0 to 10: " \
           "Is the " + gene + " gene involved in mediating the initiation or priming of the adaptive immune response in the airway epithelium following in vitro influenza virus infection? JSON Key: adaptive_immune_virus." \
           "Is the " + gene + " gene involved in mediating the innate immune response? JSON Key: overall_innate." \
           "Is the " + gene + " gene involved in mediating the initiation or priming of the adaptive immune response? JSON Key: overall_adaptive."

    #building an array of the prompts
    promptArray = [[system0,user0],[system1,user1],[system1,user2],[system1,user3],[system1,user4]]

    #build empty json object
    jsonOutput = {}

    #count for loop
    i = 0

    #loop through prompts (reducing the size of the context window)
    for prompt in promptArray:

        i=i+1

        @retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
        def completion_with_backoff(**kwargs):
            return client.chat.completions.create(**kwargs)
        
        try:
            response = completion_with_backoff(
                model="",
                response_format={ "type": "json_object" },
                temperature=0.1,
                messages=[
                    {"role": "system", "content": prompt[0] },
                    {"role": "user", "content": prompt[1] }
                ]
            )

        except AzureOpenAI.APIError as e:
            #Handle API error here, e.g. retry or log
            print(f"OpenAI API returned an API Error: {e}")
            pass

        except AzureOpenAI.APIConnectionError as e:
            #Handle connection error here
            print(f"Failed to connect to OpenAI API: {e}")
            pass

        except AzureOpenAI.RateLimitError as e:
            #Handle rate limit error (we recommend using exponential backoff)
            print(f"OpenAI API request exceeded rate limit: {e}")
            pass
        
        if i == 0:
            jsonOutput = json.loads(response.choices[0].message.content)
        else:
            jsonResponse = json.loads(response.choices[0].message.content)
            jsonOutput.update(jsonResponse)

    csvOutput.append(jsonOutput)

outputDF = pd.DataFrame(csvOutput)

#if you want to export out to csv
outputDF.to_csv('Output.csv', index=False)

