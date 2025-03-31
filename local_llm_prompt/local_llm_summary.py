from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
import time

def llm_summary(text, llm_name):
    """
    공고 텍스트를 분석하여 JSON 형식으로 요약을 생성하는 함수.

    Args:
        text (str): 분석할 공고 텍스트
        llm_name (str): 사용할 LLM 모델 이름

    Returns:
        tuple: 
            - summary (str): 요약 결과 (JSON 형식에서 추출된 문자열)
            - execution_time (float): LLM 실행 소요 시간
            - total_tokens (int or None): 사용된 총 토큰 수
    """
    # 환경 변수 로드 (API 키 등)
    load_dotenv()

    # 공고 내용을 요약하기 위한 프롬프트 템플릿 정의
    prompt = PromptTemplate.from_template(
        """
        이 공고의 **사업(과업) 수행 내용**을 요약해주세요.

        ### 제공된 공고 내용:
        {context}

        ### 출력 형식(JSON):
        ```json
        {{"summary": "공고의 사업(과업) 수행 내용을 5줄로 요약한 내용입니다."}}
        ```

        ### 요약 작성 규칙:
        1. "summary" 필드는 항상 5줄 이내로 작성합니다.
        2. 요약 내용은 반드시 "~입니다." 형식으로 끝납니다.
        - 예시: '이 사업은 AI 기술을 활용하여 데이터를 분석하는 과업을 포함하고 있습니다.'
        """
    )

    # LLM 모델 초기화
    llm = ChatOllama(
        model=llm_name,
        format="json",  # 입출력 형식을 JSON으로 설정
        temperature=0   # 출력의 일관성을 위해 온도값 설정
    )

    # JSON 응답 파싱을 위한 파서 초기화
    parser = JsonOutputParser()

    try:
        # LLM 실행 태그 설정
        llm_tag = RunnableConfig(tags=["summarization", llm_name])
        
        # 실행 시작 시간 기록
        start_time = time.time()
        
        # 프롬프트를 기반으로 LLM 호출
        response = llm.invoke(prompt.format(context=text), config=llm_tag)
        
        # 응답 파싱
        parsed_output = parser.parse(response.content)
        
        # 실행 종료 시간 및 소요 시간 계산
        end_time = time.time()
        execution_time = end_time - start_time

        # 사용된 총 토큰 수 확인
        try:
            total_tokens = response.usage_metadata['total_tokens']
        except:
            total_tokens = None

        # 요약 결과 반환
        return parsed_output['summary'], execution_time, total_tokens

    except Exception as e:
        # 오류 발생 시 기본값 반환
        print(f"[오류] LLM 호출 실패: {e}")
        return text, None, None
