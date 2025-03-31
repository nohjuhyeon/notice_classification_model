from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_core.output_parsers import JsonOutputParser
from typing import List
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig
import time

def llm_category_classification(text, llm_name) -> List[str]:
    """
    공고 요약문에서 IT 관련 기술을 분류하는 함수.

    Args:
        text(str): 공고 요약문         
        llm_name(str): 사용할 LLM 모델 이름

    Returns:
        tuple: 
            - category_dict(List[dict]): 분류된 IT 관련 기술과 참조 텍스트의 리스트 
            - category_list(List[str]): 분류된 IT 관련 기술 이름 리스트 
            - execution_time(float): 실행 시간 
            - total_tokens(int 또는 None): LLM이 사용한 총 토큰 수 
    """
    load_dotenv()  # 환경 변수 로드

    # 분류 작업에 사용할 프롬프트 템플릿 정의
    prompt = PromptTemplate.from_template(
        """
        다음은 공고의 요약문입니다.  
        이 요약문에서 요구하는 **IT 관련 기술**(예시: 인공지능, 클라우드, 데이터베이스)을 분류해주세요.  
        단, 아래 조건을 반드시 준수하여 IT 관련 기술을 정확히 분류하세요:  

        ## **주의사항**  
        - IT 관련 기술이 언급되지 않은 경우, 빈 리스트로 남겨주세요.  
        - 공사, 점검, 데이터 입력, 교육 커리큘럼 개발과 같은 활동은 IT 관련 기술로 포함하지 마세요.  
        - 기술의 이름이 명확히 언급되지 않았더라도, 기술적 활용이 구체적으로 암시된 경우에만 포함하세요.  

        ## **IT 관련 기술**:
            1. **인공지능**  
            2. **데이터베이스**  
            3. **클라우드 컴퓨팅**  
            4. **소프트웨어 개발 및 관리**  
            5. **네트워크 및 보안**  
            6. **IoT**  
            7. **블록체인**  
            8. **AR/VR 및 메타버스**  
            9. **기타 기술**  

        ## 제공된 공고 요약문 내용:
        {context}

        ## 출력 형식(JSON):
        ```
        {{“IT 관련 기술": [
            {{“name": “[한국어로 된 카테고리 이름]”,
            “참조_텍스트": “[발견된 관련 텍스트]"}}
            ]
        }}
        ```
        """
    )

    # LLM 모델 초기화
    llm = ChatOllama(
        model=llm_name,
        format="json",  # JSON 형식으로 입출력 설정
        temperature=0   # 출력의 일관성을 위해 온도값 설정
    )

    try:
        parser = JsonOutputParser()  # JSON 파싱을 위한 파서 초기화
        llm_tag = RunnableConfig(tags=["classification", llm_name])  # 태그 설정
        
        # 실행 시작 시간 기록
        start_time = time.time()
        
        # 프롬프트를 기반으로 LLM 호출
        response = llm.invoke(prompt.format(context=text), config=llm_tag)
        
        # 응답 파싱
        parsed_output = parser.parse(response.content)
        
        # IT 관련 기술 필터링
        category_dict = []
        for i in parsed_output['IT 관련 기술']:
            if i['참조_텍스트'] != '' and i['참조_텍스트'] is not None:
                category_dict.append(i)
        category_list = [category["name"] for category in category_dict]
        
        # 실행 종료 시간 및 소요 시간 계산
        end_time = time.time()
        execution_time = end_time - start_time

        # 사용된 총 토큰 수 확인
        try:
            total_tokens = response.usage_metadata['total_tokens']
        except:
            total_tokens = None

        return category_dict, category_list, execution_time, total_tokens

    except Exception as e:
        # 에러 발생 시 빈 결과 반환
        print(f"Error processing response: {e}")
        return [], [], None, None
