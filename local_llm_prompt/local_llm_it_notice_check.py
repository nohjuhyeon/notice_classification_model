from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
import time

def llm_it_notice_check(text, llm_name):
    """
    공고문이 소프트웨어 회사가 참여할 수 있는 프로젝트인지 여부를 판단하는 함수.

    Args:
        text(str): 공고 내용         
        llm_name(str): 사용할 LLM 모델 이름

    Returns:
        tuple: 
            - it_notice("True" 또는 "False"): IT 관련 여부 
            - execution_time(float): 실행 시간 
            - total_tokens(int 또는 None): LLM이 사용한 총 토큰 수 
    """
    # 환경 변수 로드 (API 키 등)
    load_dotenv()

    # IT 프로젝트 참여 여부를 판단하기 위한 프롬프트 템플릿 정의
    prompt = PromptTemplate.from_template(
        """
        Please classify whether this notice is a project that software companies can participate in. 
        Even if it is related to IT, if it includes tasks such as video content development, event hosting, event management, or educational program development, they cannot participate. 
        If they can participate, respond with **only** "True". If they cannot participate, respond with **only** "False".
        Do not include any additional explanation.

        ### Provided Notice Content:
        {context}
        
        ### Output Format (JSON):
        ```json
        {{"it_notice": "Output True if it is related to IT, otherwise output False."}}
        ```      
        """
    )

    # JSON 형식의 응답을 처리하기 위한 파서 초기화
    parser = JsonOutputParser()
    
    # LLM 모델 초기화
    llm = ChatOllama(
        model=llm_name,
        format="json",  # JSON 형식으로 입출력 설정
        temperature=0   # 출력의 일관성을 위해 온도값 설정
    )

    # 실행 시작 시간 기록
    start_time = time.time()
    
    # LLM 호출 및 응답 처리
    response = llm.invoke(prompt.format(context=text))
    parsed_output = parser.parse(response.content)
    
    # 실행 종료 시간 및 소요 시간 계산
    end_time = time.time()
    execution_time = end_time - start_time

    # 사용된 총 토큰 수 확인
    try:
        total_tokens = response.usage_metadata['total_tokens']
    except:
        total_tokens = None

    # 결과 반환 (IT 관련 여부, 실행 시간, 사용된 토큰 수)
    return parsed_output['it_notice'], execution_time, total_tokens
