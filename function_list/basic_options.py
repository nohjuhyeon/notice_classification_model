from selenium.webdriver.firefox.options import Options
import os
from pymongo import MongoClient
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager  # GeckoDriverManager 사용

# 다운로드 폴더 설정 함수
def download_path_setting(folder_path, firefox_options):
    """
    다운로드 폴더 경로를 설정하고 Firefox 옵션에 적용합니다.

    Args:
        folder_path (str): 다운로드 폴더의 기본 디렉토리 경로.
        firefox_options (Options): Firefox 브라우저 옵션 객체. 다운로드 관련 설정이 추가됩니다.

    Returns:
        tuple:
            - firefox_options (Options): 업데이트된 Firefox 옵션 객체.
            - download_folder_path (str): 생성된 다운로드 폴더의 절대 경로.
    """
    # 다운로드 폴더 경로 생성
    download_folder_path = os.path.abspath(folder_path + '/notice_list')
    if not os.path.exists(download_folder_path):
        os.makedirs(download_folder_path)  # 폴더가 없으면 생성

    # Firefox 프로필 설정 (다운로드 관련 설정)
    firefox_profile = {
        "browser.download.dir": download_folder_path,  # 다운로드 경로 지정
        "browser.download.folderList": 2,  # 2: 사용자 지정 경로에 다운로드
        "browser.helperApps.neverAsk.saveToDisk": "application/pdf,application/octet-stream",  # 다운로드 시 저장 대화 상자 생략
        "pdfjs.disabled": True,  # 내장 PDF 뷰어 비활성화 (PDF 파일 직접 다운로드)
    }

    # Firefox 옵션에 다운로드 설정 추가
    for key, value in firefox_profile.items():
        firefox_options.set_preference(key, value)

    return firefox_options, download_folder_path  # 업데이트된 옵션과 다운로드 경로 반환

# Selenium 설정 함수
def selenium_setting():
    """
    Selenium WebDriver를 위한 Firefox 브라우저 옵션을 설정합니다.

    Returns:
        firefox_options(Options): 설정된 Firefox 브라우저 옵션 객체.
    """
    # Firefox 브라우저 옵션 생성
    firefox_options = Options()

    # User-Agent 설정 (웹사이트에서 요청을 특정 브라우저로 인식하도록 설정)
    firefox_options.set_preference(
        "general.useragent.override",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
    )

    # Docker 환경 등 GUI가 없는 환경에서 실행하기 위한 추가 옵션
    firefox_options.add_argument('--headless')  # 브라우저를 숨김 모드로 실행
    firefox_options.add_argument('--no-sandbox')  # 샌드박스 기능 비활성화
    firefox_options.add_argument('--disable-dev-shm-usage')  # 공유 메모리 사용 제한
    firefox_options.add_argument('--disable-gpu')  # GPU 사용 비활성화 (선택 사항)

    return firefox_options  # 설정된 Firefox 옵션 반환

# WebDriver 초기화 함수
def init_browser(firefox_options):
    """
    Firefox WebDriver를 초기화합니다.

    Args:
        firefox_options (Options): 설정된 Firefox 브라우저 옵션 객체.

    Returns:
        browser(WebDriver): 초기화된 Firefox WebDriver 객체.
    """
    # GeckoDriverManager를 사용하여 GeckoDriver 설치 및 캐시 정리
    cache_path = os.path.expanduser("~/.wdm")  # WebDriver Manager 캐시 경로
    if os.path.exists(cache_path):
        os.system(f"rm -rf {cache_path}")  # 기존 캐시 삭제

    # GeckoDriver 설치 및 WebDriver 서비스 생성
    webdriver_manager_directory = GeckoDriverManager().install()
    service = FirefoxService(webdriver_manager_directory)

    # Firefox WebDriver 초기화
    browser = webdriver.Firefox(service=service, options=firefox_options)

    return browser  # 초기화된 WebDriver 반환

# MongoDB 설정 함수
def mongo_setting(database_name, collection_name):
    """
    MongoDB 데이터베이스 및 컬렉션을 설정합니다.

    Args:
        database_name (str): MongoDB 데이터베이스 이름.
        collection_name (str): MongoDB 컬렉션 이름.

    Returns:
        Collection(MongoDB Collection): 설정된 MongoDB 컬렉션 객체.
    """
    # 환경 변수에서 MongoDB 연결 URL 가져오기
    mongo_url = os.environ.get("DATABASE_URL")
    mongo_client = MongoClient(mongo_url)  # MongoDB 클라이언트 생성

    # 데이터베이스 및 컬렉션 연결
    database = mongo_client[database_name]  # 데이터베이스 선택
    collection = database[collection_name]  # 컬렉션 선택

    return collection  # MongoDB 컬렉션 반환
