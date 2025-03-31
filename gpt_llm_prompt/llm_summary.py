from langchain_core.output_parsers import JsonOutputParser  
from langchain_core.prompts import PromptTemplate  
from langchain_openai import ChatOpenAI  
from langchain_core.runnables import RunnableConfig  
from dotenv import load_dotenv 
import time  

def llm_summary(text):
    """
    공고 텍스트를 요약하여 JSON 형식으로 반환합니다.

    Args:
        text (str): 공고 텍스트

    Returns:
        tuple: 
            - summary(str)요약 결과 
            - execution_time(float): 실행 시간 
            - token_usage(dict): LLM 응답 메타데이터 
    """
    # 환경 변수 로드 (예: OpenAI API 키)
    load_dotenv()

    # LLM에 전달할 프롬프트 생성
    prompt = PromptTemplate.from_template(
        """
            이 공고의 사업(과업) 추진 내용을 요약해주세요.

            ### 제공된 공고 내용:
            {context}

            ---

            ### **출력 형식(JSON)**:

            ```json
                "summary": "공고의 사업(과업) 수행 내용을 5줄로 요약한 내용입니다."
            ```

            ### **요약 작성 규칙**:
            1. `"summary"` 필드는 항상 **5줄 이내**로 작성합니다.
            2. 요약 내용은 반드시 **"~입니다."** 형식으로 끝납니다.
            - 예시: "이 사업은 AI 기술을 활용하여 데이터를 분석하는 과업을 포함하고 있습니다."
        """
    )

    # ChatOpenAI 객체 생성 (LLM 초기화)
    llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0)

    # JSON 형식 출력을 위한 파서 생성
    parser = JsonOutputParser()

    # LLM 실행 태그 설정
    llm_tag = RunnableConfig(tags=["summarization", "gpt-4o-mini"])

    # 시작 시간 기록
    start_time = time.time()

    # LLM 호출 및 응답 수신
    response = llm.invoke(prompt.format(context=text), config=llm_tag)

    # 응답을 JSON 형식으로 파싱
    parsed_output = parser.parse(response.content)
    summary = parsed_output["summary"]  # 요약 내용 추출

    # 종료 시간 기록 및 실행 시간 계산
    end_time = time.time()
    execution_time = end_time - start_time
    token_usage = response.usage_metadata
    # 요약 결과, 실행 시간, 응답 메타데이터 반환
    return summary, execution_time, token_usage