from dotenv import load_dotenv  
from langchain_openai import ChatOpenAI  
from langchain_core.output_parsers import JsonOutputParser  
from typing import List  
from langchain_core.prompts import PromptTemplate  
import time  

def llm_category_classification(text) -> List[str]:
    """
    주어진 텍스트에서 IT 관련 기술을 분류하는 함수.

    Args:
        text (str): 공고 요약문 텍스트

    Returns:
        tuple:
            - category_dict(List[dict]): 추출된 IT 기술 정보
            - category_list(List[str]): 기술 카테고리 리스트
            - execution_time(float): 분석 실행 시간
            - token_usage(dict): LLM 응답 메타데이터
    """
    # 환경 변수 로드 (예: API 키)
    load_dotenv()

    # LLM에 전달할 프롬프트 생성
    # IT 관련 기술 분류 조건과 출력 형식(JSON)을 명시
    prompt = PromptTemplate.from_template(
        """
        다음은 공고의 요약문입니다.  
        이 요약문에서 요구하는 **IT 관련 기술**(예시: 인공지능, 클라우드, 데이터베이스)을 분류해주세요.  
        단, 아래 조건을 반드시 준수하여 IT 관련 기술을 정확히 분류하세요:  


        ## **분류 조건**  

        1. **IT 관련 기술로 인정되는 경우**  
        - 기술이 명확히 언급되거나, 기술의 구현 또는 활용이 구체적으로 요구되는 경우.  
        - 예를 들어, "데이터베이스 구축 및 유지보수", "클라우드 기반 시스템 설계"와 같이 특정 IT 기술의 적용이 필요한 과업.  

        2. **IT 관련 기술로 인정되지 않는 경우**  
        - 단순히 **데이터 입력**, **데이터 점검**, **기초 통계 분석**과 같은 비기술적 작업.  
        - **IT 교육 커리큘럼 개발**이나 **IT 관련 교육 제공**, **IT 관련 전문 인력 개발**과 같은 간접적인 활동.  
        - **시설 점검**, **공사 관리**, **단순 모니터링** 등 IT 기술의 활용이 아닌 일반 업무.  

        3. **기술이 포함될 수 있는 경우**  
        - 기술의 구체적인 활용이 언급되었거나, 기술적 작업이 암시되는 경우만 포함.  
        - 예: "클라우드 환경에서 데이터 관리 시스템 구축"은 포함되지만, "데이터 관리"만 언급된 경우 제외.  



        ## **IT 관련 기술**:
            1. **인공지능**  
            인간의 지능을 모방하여 학습, 추론, 문제 해결 등을 수행하는 기술.

            2. **데이터베이스**  
            데이터베이스를 구축하고, 유지 및 장애 처리를 수행하는 기술.

            3. **클라우드 컴퓨팅**  
            인터넷을 통해 컴퓨팅 자원(서버, 스토리지 등)을 제공하고 관리하는 기술.

            4. **소프트웨어 개발 및 관리**  
            소프트웨어를 설계, 구현, 테스트 및 유지보수하는 과정과 관련 기술.

            5. **네트워크 및 보안**  
            디지털 통신 네트워크의 설계, 운영, 최적화와 데이터 보호를 위한 보안 기술 및 솔루션.

            6. **IoT**  
            인터넷에 연결된 물리적 디바이스와 센서를 통해 데이터를 수집하고 상호작용하는 기술.

            7. **블록체인**  
            거래 기록을 분산 원장에 저장하여 투명성과 보안을 강화하는 기술.

            8. **AR/VR 및 메타버스**  
                증강현실과 가상현실 기술을 활용한 몰입형 가상 환경과 메타버스 플랫폼 기술.

            9. **기타 기술**  
                미래 기술(양자 컴퓨팅, 5G 등)과 특수 목적의 새로운 IT 기술.

        
        ### 제공된 공고 요약문 내용:
        {context}

        ### 출력 형식(JSON):

        ```
        “IT 관련 기술": [
            
            “name": “[한국어로 된 카테고리 이름]”,
            “참조_텍스트": “[발견된 관련 텍스트]
        ```

        ### **주의사항**  
        - IT 관련 기술이 언급되지 않은 경우, 빈 리스트로 남겨주세요.  
        - 공사, 점검, 데이터 입력, 교육 커리큘럼 개발과 같은 활동은 IT 관련 기술로 포함하지 마세요.  
        - 기술의 이름이 명확히 언급되지 않았더라도, 기술적 활용이 구체적으로 암시된 경우에만 포함하세요.  

            """
    )

    # LLM 초기화
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    # IT 관련 기술 카테고리 리스트 정의
    it_tech_list = [
        '인공지능', '데이터베이스', '클라우드 컴퓨팅', '소프트웨어 개발 및 관리',
        '네트워크 및 보안', 'IoT', '블록체인', 'AR/VR 및 메타버스'
    ]

    try:
        # 출력 파서를 JSON 형식으로 설정
        parser = JsonOutputParser()

        # LLM 실행 전 시간 기록
        start_time = time.time()

        # LLM에 프롬프트 전달 및 응답 수신
        response = llm.invoke(prompt.format(context=text))

        # 응답을 JSON 형식으로 파싱
        parsed_output = parser.parse(response.content)

        # 결과 저장을 위한 변수 초기화
        category_dict = []  # IT 관련 기술과 참조 텍스트를 저장
        category_list = []  # 중복되지 않은 기술 이름 리스트

        # 파싱된 출력에서 IT 관련 기술 필터링
        for i in parsed_output['IT 관련 기술']:
            # 참조 텍스트가 존재하고, 기술 이름이 사전 정의된 리스트에 포함된 경우만 처리
            if i['참조_텍스트'] != '' and i['참조_텍스트'] is not None and i['name'] in it_tech_list:
                category_dict.append(i)  # 기술 정보 추가
                if i['name'] not in category_list:  # 중복 방지
                    category_list.append(i['name'])

        # LLM 실행 후 시간 기록
        end_time = time.time()
        execution_time = end_time - start_time  # 실행 시간 계산
        token_usage = response.usage_metadata

        # 결과 반환 (IT 기술 딕셔너리, 기술 리스트, 실행 시간, 응답 메타데이터)
        return category_dict, category_list, execution_time, token_usage

    except Exception as e:
        # 오류 발생 시 메시지 출력 및 기본값 반환
        print(f"Error processing response: {e}")
        return [], [], None, None