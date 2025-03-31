from langchain_core.prompts import PromptTemplate  
from langchain_openai import ChatOpenAI  
from dotenv import load_dotenv  
from langchain.output_parsers.enum import EnumOutputParser  
from enum import Enum  
import time  

# IT 공고 참여 가능 여부를 나타내는 Enum 클래스 정의
class it_notice(Enum):
    TRUE = "True"  # 소프트웨어 회사 참여 가능
    FALSE = "False"  # 소프트웨어 회사 참여 불가능

# EnumOutputParser 객체 생성 (it_notice Enum 기반)
parser = EnumOutputParser(enum=it_notice)

def llm_it_notice_check(text):
    """
    공고 텍스트를 분석하여 소프트웨어 회사가 참여 가능한지 판단합니다.

    Args:
        text (str): 공고 텍스트

    Returns:
        tuple:
            - it_notice_check(str): "True" 또는 "False"
            - execution_time(float): 분석 실행 시간
            - token_usage(dict): LLM 응답 메타데이터 
    """
    # 환경 변수 로드 (예: OpenAI API 키)
    load_dotenv()

    # LLM에 전달할 프롬프트 생성
    prompt = PromptTemplate.from_template(
        """
        이 공고가 소프트웨어 회사가 참여할 수 있는 프로젝트인지 분류해 주세요.  
        IT와 관련된 경우라도, 영상 콘텐츠 개발, 행사 주최, 행사 운영, 교육 프로그램 개발과 같은 작업이 포함되어 있다면 참여할 수 없습니다.  
        참여할 수 있는 경우 **반드시** "True"만 응답하고, 참여할 수 없는 경우 **반드시** "False"만 응답하세요.  
        추가적인 설명은 포함하지 마세요.

        ### 제공된 공고 내용:
        {context}
        
        ### 지시 사항: 
        {instructions}
        """
    ).partial(instructions=parser.get_format_instructions())  # 출력 형식 지침 포함

    # ChatOpenAI 객체 생성 (LLM 초기화)
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    # 시작 시간 기록
    start_time = time.time()

    # LLM 호출 및 응답 수신
    response = llm.invoke(prompt.format(context=text))

    # 응답을 Enum 형식으로 파싱
    parsed_output = parser.parse(response.content)

    # 종료 시간 기록 및 실행 시간 계산
    end_time = time.time()
    execution_time = end_time - start_time
    it_notice_check = parsed_output.value
    token_usage = response.usage_metadata
    # 판단 결과(Enum 값), 실행 시간, 응답 메타데이터 반환
    return it_notice_check, execution_time, token_usage
