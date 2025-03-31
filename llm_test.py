from dotenv import load_dotenv
from gpt_llm_prompt.llm_summary import llm_summary
from gpt_llm_prompt.llm_cate_classification import llm_category_classification
from function_list.basic_options import mongo_setting
from gpt_llm_prompt.llm_it_notice_check import llm_it_notice_check
import json

# MongoDB 연결 설정
load_dotenv()

import json

collection = mongo_setting("llm_notice_test","test_notice_dataset")
results = collection.find({}, {"_id": 0, "notice_id": 1})
new_dict = []

collection = mongo_setting("llm_notice_test", "gpt-4o-mini-test")
results = collection.find({}, {"_id": 0, "notice_id": 1})
id_list = [i["notice_id"] for i in results]

for i in results:
    try:
        if i["notice_id"] not in id_list and i['notice_text'].replace('\n','').replace(' ','') != '':
            context = i["notice_text"]
            # LLM 모델 초기화
            # notice_type = notice_keyword_search(context)
            it_notice_check,check_time,check_token = llm_it_notice_check(context)
            if it_notice_check.lower() == 'true':
                summary,summary_time,summary_token = llm_summary(context)
                category_dict, category_list,category_time,category_token = llm_category_classification(summary)
                collection.insert_one(
                    {
                        "notice_id": i["notice_id"],
                        "notice_text": i["notice_text"],
                        "notice_check": it_notice_check,
                        "check_time":round(check_time,2),
                        "check_token":check_token,
                        "summary": summary,
                        "summary_time":round(summary_time,2),
                        "summary_token":summary_token,
                        "category": category_dict,
                        "category_time":round(category_time,2),
                        "category_token":category_token
                    }
                )
            else:
                collection.insert_one(
                    {
                        "notice_id": i["notice_id"],
                        "notice_text": i["notice_text"],
                        "notice_check": it_notice_check,
                        "check_time":round(check_time,2),
                        "check_token":check_token,
                        "category": [],

                        }
                )                
        else:
            pass
    except:
        pass

