from fastapi import FastAPI
import openai
import time
import json
from pydantic import BaseModel


openai.api_type = "azure"
openai.api_base = "https://sproutsai-gpt.openai.azure.com/"
openai.api_version = "2023-07-01-preview"
openai.api_key = '564db3f7e88b433a94110af1a5e52d4b'


app = FastAPI()

class necessary_details(BaseModel):
    warmup_question_validation : list
    job_parser : dict
    must_have_skills : list
    number_of_questions : int
  
class Resume_parser(BaseModel):
    Job_parser : dict
    
class candidate_response(BaseModel):
    Answer : list

def warmup_question_genreation(criteria,skills):
   
   
    response_format = '''{
    "criteria_tag": f"{criteria}",
    "skills_tag" : f"{skills}"
    "type_of_question": "warmup question",
                        }'''
    n = 0
    while n < 3:
        try:
            response = openai.ChatCompletion.create(
                    engine = 'gpt4-sproutsai',
                    messages=[
                        {"role": "system", "content": f"""Your role is skill finding by the way of creating warmup questions. 
                            I have a list of skill under some criteria and I have many questions on each skill. You need to find which skill candidate know 

                    Generate a simple warmup questions that cover the following aspects:
                            
                    1. Don't create a question like Can you briefly describe your experience?
                    2. The generated question should be in a general format for the {criteria} and {skills}.
                    3. The motive of asking the question is to assess the candidate's overall suitability for the position based on the {criteria}.
                    4. Generate one question.

                    
                    """},
                        
                        {"role": "user", "content": f"Give the response in JSON format, which is strictly a list of {response_format}. Use \" instead of ' for the response keys."},

                    ],

                    temperature=0.2,
                    max_tokens=3500,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0

                )
            
            
            return json.loads(response['choices'][0]['message']['content'])
        except Exception as e:
            n+=1
            time.sleep(60)
    return "Error with openai api"

def warmup_validation(criteria, skills, answer):
    output = {}
    response_format =  [
        {
            "skills": 'skill1',
            "reason": "Give reason why you picked the skill"
        },
        {
            "skills": 'skill2',
            "reason": "Give reason why you picked the skill"
        } ]
    
    n = 0
    while n < 3:
        try:
            response = openai.ChatCompletion.create(
                engine='gpt4-sproutsai',
                messages=[
                    {
                        "role": "system",
                        "content": f"""Your role is to find the skill from the answer: {answer}.
                                If the answer is incomplete or irrelevant, then return []
                                If the candidate answers like "I know this skill" or "I have experience in these skills" and the skill is available in {skills}, then only consider the skill.
                                If the answer is meaningless or insufficient, please respond in a reason section like "he doesn't have knowledge of that skill".
                                There is no need to add skills if that is not on the list of skills {skills}.
                                If the answer is "I don't know these skills" like that, then don't consider those skills in{response_format}"""
                    },
                    {"role": "user", "content": f"Give the response in JSON format, which is strictly a list of {response_format}. Use \" instead of ' for the response keys."},
                ],
                temperature=0.2,
                max_tokens=1000,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0)
            time.sleep(5)
            
            response_content = response['choices'][0]['message']['content']
            response_content = json.loads(response_content)
            output["criteria"] = criteria
            output["skills"] = response_content
            return output
        except Exception as e:
            n += 1
            time.sleep(25)
    return "Error with openai api"








def question_allocation(criteria_wise_questions,criteria_skill_dictionary,known_skills_to_candidate,must_have_skills):
        
    final_output = {}
    
    for i in criteria_wise_questions:
        Number_of_questions_criteria_wise = criteria_wise_questions[i]
        skills = criteria_skill_dictionary[i]
        must_have_skills_0 = []
        other_skills = []

        #dividing skills into 2 categories -> must have and others

        for i in skills:
            if i in must_have_skills:
                must_have_skills_0.append(i)
            else:
                other_skills.append(i)

        #dividing other skills into 2 categories -> candidate knows and don't knows

        other_high_priority = []
        other_low_priority = []
        

        for j in other_skills:
            if j in known_skills_to_candidate:
                other_high_priority.append(j)
            else:
                other_low_priority.append(j)
        
        #various conditions that we need to tackle -> to allocate questions
        if (len(must_have_skills_0) != 0) and (len(other_high_priority) != 0) and (len(other_low_priority) != 0):
            
            must_have_percentage = 0.6
            other_high_priority_percentage = 0.25
            other_low_priority_percentage = 0.15

        
            num_of_question_must_have_skills = max(0, round(Number_of_questions_criteria_wise * must_have_percentage))
            num_of_question_other_high_priority_skills = max(0, round(Number_of_questions_criteria_wise * other_high_priority_percentage))
            num_of_question_other_low_priority_skills = Number_of_questions_criteria_wise - num_of_question_must_have_skills - num_of_question_other_high_priority_skills
            
            if num_of_question_must_have_skills != 0:
                n = 0
                while n < num_of_question_must_have_skills:
                    for i in must_have_skills_0:
                        if i not in final_output:
                            final_output[i] = 1
                        else:
                            final_output[i] += 1
                        n += 1
                        if n >= num_of_question_must_have_skills:
                            break

            if num_of_question_other_high_priority_skills != 0:
                n = 0
                while n < num_of_question_other_high_priority_skills:
                    for i in other_high_priority:
                        if i not in final_output:
                            final_output[i] = 1
                        else:
                            final_output[i] += 1
                        n += 1
                        if n >= num_of_question_other_high_priority_skills:
                            break

            if num_of_question_other_low_priority_skills != 0 :
                n = 0
                while n < num_of_question_other_low_priority_skills:
                    for i in other_low_priority:
                        if i not in final_output:
                            final_output[i] = 1
                        else:
                            final_output[i] += 1
                        n += 1
                        if n >= num_of_question_other_low_priority_skills:
                            break


        elif (len(must_have_skills_0) != 0) and (len(other_high_priority) != 0) and (len(other_low_priority) == 0):
            
            must_have_percentage = 0.7
            other_high_priority_percentage = 0.3

            num_of_question_must_have_skills = max(1, round(Number_of_questions_criteria_wise * must_have_percentage))
            num_of_question_other_high_priority_skills = max(0, Number_of_questions_criteria_wise - num_of_question_must_have_skills)

            if num_of_question_must_have_skills != 0:
                n = 0
                while n < num_of_question_must_have_skills:
                    for i in must_have_skills_0:
                        if i not in final_output:
                            final_output[i] = 1
                        else:
                            final_output[i] += 1
                        n += 1
                        if n >= num_of_question_must_have_skills:
                            break

            if num_of_question_other_high_priority_skills != 0:
                n = 0
                while n < num_of_question_other_high_priority_skills:
                    for i in other_high_priority:
                        if i not in final_output:
                            final_output[i] = 1
                        else:
                            final_output[i] += 1
                        n += 1
                        if n >= num_of_question_other_high_priority_skills:
                            break
        
        elif (len(must_have_skills_0) != 0) and (len(other_high_priority) == 0) and (len(other_low_priority) != 0):
            
            must_have_percentage = 0.7
            other_low_priority_percentage = 0.3

            num_of_question_must_have_skills = max(1, round(Number_of_questions_criteria_wise * must_have_percentage))
            num_of_question_other_low_priority_skills = max(0, Number_of_questions_criteria_wise - num_of_question_must_have_skills)

            if num_of_question_must_have_skills != 0:
                n = 0
                while n < num_of_question_must_have_skills:
                    for i in must_have_skills_0:
                        if i not in final_output:
                            final_output[i] = 1
                        else:
                            final_output[i] += 1
                        n += 1
                        if n >= num_of_question_must_have_skills:
                            break

            if num_of_question_other_low_priority_skills != 0:
                n = 0
                while n < num_of_question_other_low_priority_skills:
                    for i in other_low_priority:
                        if i not in final_output:
                            final_output[i] = 1
                        else:
                            final_output[i] += 1
                        n += 1
                        if n >= num_of_question_other_low_priority_skills:
                            break

        elif (len(must_have_skills_0) == 0) and (len(other_high_priority) != 0) and (len(other_low_priority) != 0):

            other_high_priority_percentage = 0.5
            other_low_priority_percentage = 0.5

            num_of_question_other_high_priority_skills = max(1, round(Number_of_questions_criteria_wise * other_high_priority_percentage))
            num_of_question_other_low_priority_skills = max(0, Number_of_questions_criteria_wise - num_of_question_other_high_priority_skills)
            
            if num_of_question_other_high_priority_skills != 0:
              
                n = 0
                while n < num_of_question_other_high_priority_skills:
                    for i in other_high_priority:
                        if i not in final_output:
                            final_output[i] = 1
                        else:
                            final_output[i] += 1
                        n += 1
                        if n >= num_of_question_other_high_priority_skills:
                            break

            if num_of_question_other_low_priority_skills != 0:
                
                n = 0
                while n < num_of_question_other_low_priority_skills:
                    for i in other_low_priority:
                        if i not in final_output:
                            final_output[i] = 1
                        else:
                            final_output[i] += 1
                        n += 1
                        if n >= num_of_question_other_low_priority_skills:
                            break

        elif (len(must_have_skills_0) != 0) and (len(other_high_priority) == 0) and (len(other_low_priority) == 0):

            num_of_question_must_have_skills = Number_of_questions_criteria_wise

            if num_of_question_must_have_skills != 0:
                n = 0
                while n < num_of_question_must_have_skills:
                    for i in must_have_skills_0:
                        if i not in final_output:
                            final_output[i] = 1
                        else:
                            final_output[i] += 1
                        n += 1
                        if n >= num_of_question_must_have_skills:
                            break

        elif (len(must_have_skills_0) == 0) and (len(other_high_priority) != 0) and (len(other_low_priority) == 0):

            num_of_question_other_high_priority_skills = Number_of_questions_criteria_wise

            if num_of_question_other_high_priority_skills != 0:
                n = 0
                while n < num_of_question_other_high_priority_skills:
                    for i in other_high_priority:
                        if i not in final_output:
                            final_output[i] = 1
                        else:
                            final_output[i] += 1
                        n += 1
                        if n >= num_of_question_other_high_priority_skills:
                            break

        elif (len(must_have_skills_0) == 0) and (len(other_high_priority) == 0) and (len(other_low_priority) != 0):

            num_of_question_other_low_priority_skills = Number_of_questions_criteria_wise

            if num_of_question_other_low_priority_skills != 0:
                n = 0
                while n < num_of_question_other_low_priority_skills:
                    for i in other_low_priority:
                        if i not in final_output:
                            final_output[i] = 1
                        else:
                            final_output[i] += 1
                        n += 1
                        if n >= num_of_question_other_low_priority_skills:
                            break
       
    return final_output


@app.post("/question_allocation_and_next_question_selection")
def warmup_question_validation(payload : necessary_details):
    Known_skills_to_the_candidate = payload.warmup_question_validation
    job_parser = payload.job_parser
    must_have_skills = payload.must_have_skills


    #collecting  known skill of the candidate
    known_skills_to_candidate = []
    for i in Known_skills_to_the_candidate:
        for j in i['skills']:
            known_skills_to_candidate.append(j['skills'])
    

    #job parser output -> list of criteria and skill
    criteria_skill_dictionary = {}
    for i in job_parser['question_selection_data']['criterias']:
        if i['criteria'] in criteria_skill_dictionary:
            criteria_skill_dictionary[i['criteria']].append(i['skill'])
        else:
            criteria_skill_dictionary[i['criteria']] =  [i['skill']]


    #initializing questions to all the skills -> default = 0
    criteria_wise_questions = {}
    for i in criteria_skill_dictionary:
        criteria_wise_questions[i] = 0


    total_number_of_questions = payload.number_of_questions
    initializer = 1

    categories = sorted(criteria_wise_questions.keys(), key=lambda k: criteria_wise_questions[k], reverse=True)
    
    while initializer <= total_number_of_questions:
        for key in categories:
            criteria_wise_questions[key] += 1
            initializer += 1
            if initializer > total_number_of_questions:
                break


    skill_wise_question_allocation = question_allocation(criteria_wise_questions, criteria_skill_dictionary, known_skills_to_candidate, must_have_skills)
    final_output = []
    for i in skill_wise_question_allocation:
        b = {}
        for j in criteria_skill_dictionary:
            
            for k in criteria_skill_dictionary[j]:
                if k == i:
                    b['criteria'] = j
                    b['skills'] = {
                        "skill" : k,
                        "number_of_questions" : skill_wise_question_allocation[i]
                    }
    
        final_output.append(b)  
   
        
    return final_output


@app.post("/warmup_question_generation")
def warmup_question_generation(payload : Resume_parser):
    jobparser = payload.Job_parser
    criteria_skill_dictionary = {}
    for i in jobparser['question_selection_data']['criterias']:
        if i['criteria'] in criteria_skill_dictionary:
            criteria_skill_dictionary[i['criteria']].append(i['skill'])
        else:
            criteria_skill_dictionary[i['criteria']] =  [i['skill']]

  
    op = []
    for i in criteria_skill_dictionary:
        x = warmup_question_genreation(i,criteria_skill_dictionary[i])
        op.append(x)
    return op

@app.post("/warmup_answer_validation")
def warmup_question_validation(payload : candidate_response):
    
    candidate_response = payload.Answer
    result = []
    
    for i in candidate_response:
        print(i)
        validation_gpt = warmup_validation(i['criteria'],i['skills'],i['answer'])
        result.append(validation_gpt)
        
    return result
