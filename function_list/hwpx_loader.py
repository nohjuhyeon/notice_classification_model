import zipfile
import os  
import xml.etree.ElementTree as ET  
import re
import unicodedata

def remove_chinese_characters(s: str):
    """
    문자열에서 중국어 문자를 제거합니다.

    Args:
        s (str): 입력 문자열

    Returns:
        str: 중국어 문자가 제거된 문자열
    """
    return re.sub(r"[\u4e00-\u9fff]+", "", s)

def remove_control_characters(s):
    """
    문자열에서 제어 문자를 제거합니다.

    Args:
        s (str): 입력 문자열

    Returns:
        str: 제어 문자가 제거된 문자열
    """
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")

def get_hwpx_text(file_path):
    """
    HWPX 파일에서 텍스트를 추출합니다.

    Args:
        file_path (str): HWPX 파일 경로

    Returns:
        tuple:
            - docs(List[str]): 파일에서 추출된 텍스트
            - metadata(dict): 파일과 관련된 메타데이터
    """
    try:
        # ZIP 파일 열기
        with zipfile.ZipFile(file_path, 'r') as zf:
            # Contents 폴더 내의 섹션 파일(.xml) 목록 찾기
            section_files = [name for name in zf.namelist() if name.startswith('Contents/section') and name.endswith('.xml')]

            # 섹션 데이터를 저장할 디렉토리 생성 (필요시)
            output_dir = "extracted_sections"
            os.makedirs(output_dir, exist_ok=True)  # 디렉토리가 없으면 생성

            # 메타데이터와 텍스트 데이터를 저장할 변수 초기화
            metadata = {}
            docs = []

            # 각 섹션 파일 처리
            for section_file in section_files:
                with zf.open(section_file) as section_file_content:
                    # 섹션 파일 내용 읽기
                    section_content = section_file_content.read().decode('utf-8')

                # XML 파싱
                root = ET.fromstring(section_content)

                # 페이지별 텍스트를 저장할 리스트 초기화
                pages = []
                current_page = []

                # 테이블 텍스트를 별도로 저장
                table_texts = []
                for tbl in root.findall(".//hp:tbl", namespaces={"hp": "http://www.hancom.co.kr/hwpml/2011/paragraph"}):
                    # 테이블 내 텍스트 추출
                    table_texts.extend(
                        [t.text for t in tbl.findall(".//hp:t", namespaces={"hp": "http://www.hancom.co.kr/hwpml/2011/paragraph"}) if t.text]
                    )

                # 문단(p) 요소에서 텍스트 추출
                for p in root.findall(".//hp:p", namespaces={"hp": "http://www.hancom.co.kr/hwpml/2011/paragraph"}):
                    # pageBreak 속성 확인 (페이지 구분)
                    page_break = p.attrib.get("pageBreak", "0")  # 기본값은 "0"
                    
                    # 문단 내 텍스트 추출
                    text_elements = p.findall(".//hp:t", namespaces={"hp": "http://www.hancom.co.kr/hwpml/2011/paragraph"})
                    text = " ".join([t.text for t in text_elements if t.text and t.text not in table_texts])  # 테이블 텍스트 제외

                    # 페이지가 구분될 경우 처리
                    if page_break == "1":  # 새로운 페이지 시작
                        if current_page:
                            pages.append(current_page)  # 이전 페이지 저장
                        current_page = []  # 새로운 페이지 초기화

                    if text:  # 텍스트가 있으면 현재 페이지에 추가
                        current_page.append(text)

                # 마지막 페이지 저장
                if current_page:
                    pages.append(current_page)

                # 페이지별 텍스트 처리
                for i, page in enumerate(pages, start=1):
                    # 중국어 문자 제거
                    page = [remove_chinese_characters(line) for line in page]
                    # 제어 문자 제거
                    page = [remove_control_characters(line) for line in page]

                    # 페이지 텍스트를 하나로 합치기
                    text = "\n".join(page)
                    docs.append(text)

            # 각 섹션의 텍스트를 메타데이터에 저장
            for idx in range(len(docs)):
                section_name = f"section{idx}"  # 섹션 이름 생성 (예: section0, section1, ...)
                metadata[section_name] = docs[idx]  # 메타데이터에 저장

            # 모든 섹션 텍스트와 메타데이터 반환
            return docs, metadata
    except Exception as e:
        # 오류 발생 시 에러 메시지 반환
        return f"Error extracting text: {e}"
