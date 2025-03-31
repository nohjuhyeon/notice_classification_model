from typing import Any, Dict, List, Optional, Iterator
import olefile
import zlib
import struct
import re
import unicodedata
from langchain.schema import Document
from langchain.document_loaders.base import BaseLoader


class HWPLoader(BaseLoader):
    """HWP 파일 읽기 클래스. HWP 파일의 내용을 읽고 문서 객체를 생성합니다."""

    def __init__(self, file_path: str, *args: Any, **kwargs: Any) -> None:
        """
        HWPLoader 초기화 메서드.

        Args:
            file_path (str): 읽을 HWP 파일 경로.
            *args, **kwargs: 추가 인자.
        """
        super().__init__(*args, **kwargs)
        self.file_path = file_path  # 파일 경로 저장
        self.extra_info = {"source": file_path}  # 파일 정보 저장
        self._initialize_constants()  # 상수 초기화

    def _initialize_constants(self) -> None:
        """클래스에서 사용할 상수를 초기화합니다."""
        self.FILE_HEADER_SECTION = "FileHeader"  # 파일 헤더 섹션 이름
        self.HWP_SUMMARY_SECTION = "\x05HwpSummaryInformation"  # 요약 정보 섹션 이름
        self.SECTION_NAME_LENGTH = len("Section")  # 섹션 이름 길이
        self.BODYTEXT_SECTION = "BodyText"  # 본문 텍스트 섹션 이름
        self.HWP_TEXT_TAGS = [67]  # 텍스트 태그 ID

    def lazy_load(self) -> Iterator[Document]:
        """
        HWP 파일에서 데이터를 로드하고 문서 객체를 생성합니다.

        Yields:
            Document: 추출된 문서 객체.
        """
        load_file = olefile.OleFileIO(self.file_path)  # OleFileIO를 사용하여 파일 열기
        file_dir = load_file.listdir()  # 파일 디렉토리 목록 가져오기

        # 파일 유효성 검사
        if not self._is_valid_hwp(file_dir):
            raise ValueError("유효하지 않은 HWP 파일입니다.")

        # 텍스트 추출 및 문서 객체 생성
        result_text = self._extract_text(load_file, file_dir)
        yield self._create_document(text=result_text, extra_info=self.extra_info)

    def _is_valid_hwp(self, dirs: List[List[str]]) -> bool:
        """
        HWP 파일의 유효성을 검사합니다.

        Args:
            dirs (List[List[str]]): 파일 디렉토리 목록.

        Returns:
            bool: 파일이 유효한 경우 True, 그렇지 않으면 False.
        """
        return [self.FILE_HEADER_SECTION] in dirs and [self.HWP_SUMMARY_SECTION] in dirs

    def _get_body_sections(self, dirs: List[List[str]]) -> List[str]:
        """
        본문 섹션 목록을 반환합니다.

        Args:
            dirs (List[List[str]]): 파일 디렉토리 목록.

        Returns:
            List[str]: 본문 섹션 이름 리스트.
        """
        section_numbers = [
            int(d[1][self.SECTION_NAME_LENGTH :])
            for d in dirs
            if d[0] == self.BODYTEXT_SECTION
        ]
        return [
            f"{self.BODYTEXT_SECTION}/Section{num}" for num in sorted(section_numbers)
        ]

    def _create_document(
        self, text: str, extra_info: Optional[Dict] = None
    ) -> Document:
        """
        문서 객체를 생성합니다.

        Args:
            text (str): 문서 내용 텍스트.
            extra_info (Optional[Dict]): 추가 정보.

        Returns:
            Document: 생성된 문서 객체.
        """
        return Document(page_content=text, metadata=extra_info or {})

    def _extract_text(
        self, load_file: olefile.OleFileIO, file_dir: List[List[str]]
    ) -> str:
        """
        모든 섹션에서 텍스트를 추출합니다.

        Args:
            load_file (olefile.OleFileIO): OleFileIO 객체.
            file_dir (List[List[str]]): 파일 디렉토리 목록.

        Returns:
            str: 추출된 텍스트.
        """
        sections = self._get_body_sections(file_dir)  # 본문 섹션 목록 가져오기
        return "\n".join(
            self._get_text_from_section(load_file, section) for section in sections
        )

    def _is_compressed(self, load_file: olefile.OleFileIO) -> bool:
        """
        파일이 압축되었는지 확인합니다.

        Args:
            load_file (olefile.OleFileIO): OleFileIO 객체.

        Returns:
            bool: 압축된 경우 True, 그렇지 않으면 False.
        """
        with load_file.openstream(self.FILE_HEADER_SECTION) as header:
            header_data = header.read()
            return bool(header_data[36] & 1)  # 압축 여부 확인

    def _get_text_from_section(self, load_file: olefile.OleFileIO, section: str) -> str:
        """
        특정 섹션에서 텍스트를 추출합니다.

        Args:
            load_file (olefile.OleFileIO): OleFileIO 객체.
            section (str): 섹션 이름.

        Returns:
            str: 추출된 텍스트.
        """
        with load_file.openstream(section) as bodytext:
            data = bodytext.read()

        # 압축 여부에 따라 데이터 처리
        unpacked_data = (
            zlib.decompress(data, -15) if self._is_compressed(load_file) else data
        )

        text = []
        i = 0
        while i < len(unpacked_data):
            # 레코드 헤더 파싱
            header, rec_type, rec_len = self._parse_record_header(
                unpacked_data[i : i + 4]
            )
            if rec_type in self.HWP_TEXT_TAGS:  # 텍스트 태그인지 확인
                rec_data = unpacked_data[i + 4 : i + 4 + rec_len]
                text.append(rec_data.decode("utf-16"))  # UTF-16으로 디코딩
            i += 4 + rec_len

        # 텍스트 정제 (중국어 문자 및 제어 문자 제거)
        text = [self.remove_chinese_characters(line) for line in text]
        text = [self.remove_control_characters(line) for line in text]
        text = "\n".join(text)
        return text

    @staticmethod
    def remove_chinese_characters(s: str) -> str:
        """
        중국어 문자를 제거합니다.

        Args:
            s (str): 입력 문자열.

        Returns:
            str: 중국어 문자가 제거된 문자열.
        """
        return re.sub(r"[\u4e00-\u9fff]+", "", s)

    @staticmethod
    def remove_control_characters(s: str) -> str:
        """
        제어 문자를 제거합니다.

        Args:
            s (str): 입력 문자열.

        Returns:
            str: 제어 문자가 제거된 문자열.
        """
        return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")

    @staticmethod
    def _parse_record_header(header_bytes: bytes) -> tuple:
        """
        레코드 헤더를 파싱합니다.

        Args:
            header_bytes (bytes): 레코드 헤더 바이트.

        Returns:
            tuple: (헤더, 레코드 타입, 레코드 길이).
        """
        header = struct.unpack_from("<I", header_bytes)[0]
        rec_type = header & 0x3FF  # 레코드 타입 추출
        rec_len = (header >> 20) & 0xFFF  # 레코드 길이 추출
        return header, rec_type, rec_len


if __name__ == "__main__":
    # HWPLoader를 사용하여 HWP 파일 로드 및 내용 출력
    loader = HWPLoader("test.hwp")

    # 문서 로드
    docs = loader.load()
    contents = docs[0].page_content  # 첫 번째 문서의 내용 가져오기
    print(contents)  # 문서 내용 출력
