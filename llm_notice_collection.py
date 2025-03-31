import requests 
import json
from selenium.webdriver.common.by import By
import os 
import time
from function_list.basic_options import mongo_setting
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from function_list.basic_options import selenium_setting,download_path_setting,init_browser
from function_list.g2b_func import notice_file_check,folder_clear


# url 주소 변수 지정
def wait_for_downloads(download_dir, timeout=30):
    """
    다운로드가 완료될 때까지 기다리는 함수.

    :param download_dir: 다운로드 디렉토리 (예: '/path/to/downloads')
    :param timeout: 최대 대기 시간 (초)
    :return: 다운로드 완료 여부 (True/False)
    """
    end_time = time.time() + timeout
    while True:
        # 다운로드 디렉토리의 파일 목록 가져오기
        files = os.listdir(download_dir)
        
        # 임시 파일(`.part`)이 없는지 확인
        if not any(file.endswith('.part') for file in files):
            return True  # 다운로드 완료
        
        # 타임아웃 확인
        if time.time() > end_time:
            return False
        
        # 0.5초 대기 후 다시 확인
        time.sleep(0.5)


def notice_search(notice_ids, notice_list,folder_path):
    collection = mongo_setting('llm_notice_test','test_notice_dataset')
    try:
        url = 'http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServcPPSSrch?serviceKey=Qa6CXT4r6qEr%2BkQt%2FJx6wJr5MPx45hKNJwNTScoYryT2uGz7GozIqpjBw%2FRMk1uE8l92NU7h89m20sa%2FXHKuaQ%3D%3D&pageNo=1&numOfRows=500&inqryDiv=1&inqryBgnDt={}&inqryEndDt={}&type=json'.format('202503170000', '202503240000')
        # url과 parameters를 response라는 변수로 받음 
        response = requests.get(url) 
        # json 파일을 dictionary 형태로 변환
        contents = json.loads(response.content)

        items = contents['response']['body']['items']

        totalCount = contents['response']['body']['totalCount']
        numOfRows = contents['response']['body']['numOfRows']
        pages = totalCount//numOfRows + 1
        item_list = []
        for i in range(pages):
            pagenum = i + 1
            url = 'http://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoServcPPSSrch?serviceKey=Qa6CXT4r6qEr%2BkQt%2FJx6wJr5MPx45hKNJwNTScoYryT2uGz7GozIqpjBw%2FRMk1uE8l92NU7h89m20sa%2FXHKuaQ%3D%3D&pageNo={}&numOfRows=500&inqryDiv=1&inqryBgnDt={}&inqryEndDt={}&type=json'.format(pagenum,'202503170000', '202503240000')
            response = requests.get(url) 
            contents = json.loads(response.content)
            items = contents['response']['body']['items']
            item_list.extend(items)
        output_file = "item_list.json"  # 저장할 파일 이름

        try:
            with open(output_file, "w", encoding="utf-8") as file:
                json.dump(item_list, file, ensure_ascii=False, indent=4)  # JSON 저장
            print(f"item_list가 '{output_file}'로 저장되었습니다.")
        except Exception as e:
            print(f"JSON 저장 중 오류 발생: {e}")
    except:
        file_path = folder_path + 'item_list.json'
        print(file_path)
        # JSON 파일 읽기
        with open(file_path, 'r', encoding='utf-8') as file:
            item_list = json.load(file)

    chrome_options = selenium_setting()
    chrome_options,download_folder_path = download_path_setting(folder_path,chrome_options)
    browser = init_browser(chrome_options)
    notice_id_list  = []
    item_num = 0
    print("총 공고 수 : ", len(item_list))
    db_insert_count = 0
    for item in item_list:
        bidNtceNo = item['bidNtceNo']
        bidNtceOrd = item['bidNtceOrd']
        notice_id = bidNtceNo + '-' + bidNtceOrd
        item_num += 1
        if item_num % 100 == 0:
            print(item_num)
        if notice_id not in notice_id_list and notice_id not in notice_ids:
            notice_id_list.append(notice_id)
            notice_title = item['bidNtceNm']
            notice_link = item['bidNtceDtlUrl']
            for k in range(10):
                try:
                    folder_clear(download_folder_path)
                    browser.get(notice_link)    
                    time.sleep(3)
                    WebDriverWait(browser, 10).until(
                        EC.invisibility_of_element_located((By.ID, "___processbar2"))  # 로딩 창의 ID를 사용
                    )
                except:
                    pass
                try:
                    alarm_btn = browser.find_element(by=By.CSS_SELECTOR,value="input[value='확인']")
                    alarm_btn.click()
                except:
                    pass
                try:
                    download_elements = browser.find_elements(By.CSS_SELECTOR,value='td>nobr>a')
                    # 찾은 요소 출력
                    for element in download_elements:
                        element.click()
                        wait_for_downloads(download_folder_path)
                        time.sleep(2)
                except:
                    pass
                try:
                    entire_files = WebDriverWait(browser, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'table > thead > tr:nth-child(1) >th:nth-child(1)> div >input[title="전체선택"]'))
                        )
                    entire_files.click()
                    download_btn = browser.find_elements(By.CSS_SELECTOR, "input[value='다운로드']")[0]
                    download_btn.click()
                    wait_for_downloads(download_folder_path)
                    time.sleep(2)
                    try:
                        alarm_btn = browser.find_element(by=By.CSS_SELECTOR,value="input[value='확인']")
                        alarm_btn.click()
                    except Exception as e:
                        pass
                    try:
                        rfp_btn = browser.find_element(by=By.CSS_SELECTOR,value='#mf_wfm_container_mainWframe_grdPrpsDmndInfoView_cell_0_2 > nobr:nth-child(1) > a:nth-child(1)')
                        rfp_btn.click()
                        time.sleep(2)
                    except:
                        pass
                    text = notice_file_check(download_folder_path)
                    folder_clear(download_folder_path)
                    time.sleep(1)
                    dict_notice = {'notice_id':notice_id,'link':notice_link,'title':notice_title,'notice_text':text}
                    notice_list.append(dict_notice)
                    collection.insert_one(dict_notice)
                    db_insert_count += 1
                    # print(dict_notice)
                    break
                except Exception as e:
                    # print("download_error")
                    time.sleep(2)
            pass
    browser.quit()
    print("저장한 공고 수:", db_insert_count)
    pass
    return notice_list

def notice_collection():
    collection = mongo_setting('news_scraping','gpt_llm_large_dataset')
    results = collection.find({},{'_id':0})
    existing_df = [i for i in results]
    existing_df = pd.DataFrame(existing_df)
    existing_df.rename(columns={
        'notice_id': '공고번호',
        'title': '공고명',
        'link': '링크',
        }, inplace=True)
    notice_ids = existing_df['공고번호'].to_list()
    # notice_ids = []
    notice_list = []
    folder_path = os.environ.get("folder_path")
    notice_list = notice_search(notice_ids,notice_list,folder_path)

    return notice_list

if __name__ == "__main__":
    notice_collection()