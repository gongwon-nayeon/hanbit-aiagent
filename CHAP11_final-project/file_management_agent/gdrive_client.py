"""
Google Drive API 클라이언트

Google Drive API를 사용하여 파일을 업로드, 다운로드, 관리합니다.

사전 설정:
1. Google Cloud Console에서 프로젝트 생성
2. Google Drive API 활성화
3. OAuth 2.0 클라이언트 ID 생성 (데스크톱 앱)
4. credentials.json 다운로드 후 이 파일과 같은 디렉토리에 배치

storage_ref 규칙:
- 모든 파일은 storage_ref = "gdrive://file/{FILE_ID}" 로 추상화
"""
import os
import logging

logger = logging.getLogger(__name__)
import io
from typing import Optional, Dict, Any, List
from datetime import datetime

# Google API 라이브러리
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from googleapiclient.errors import HttpError


# Google Drive API 스코프 (전체 접근)
SCOPES = [
    'https://www.googleapis.com/auth/drive.file',  # 앱이 생성한 파일만
    'https://www.googleapis.com/auth/drive',       # 전체 드라이브 접근
]


class GoogleDriveClient:
    """
    Google Drive API 클라이언트

    파일 업로드, 다운로드, 목록 조회, 삭제 등을 지원합니다.
    """

    def __init__(self, credentials_path: str = None, token_path: str = None): # [ 1 ]
        """
        클라이언트 초기화

        Args:
            credentials_path: OAuth 클라이언트 자격 증명 파일 경로 (credentials.json)
            token_path: 토큰 저장 경로 (token.json)
        """
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.credentials_path = credentials_path or os.path.join(base_dir, "credentials.json")
        self.token_path = token_path or os.path.join(base_dir, "token.json")

        self.service = None
        self.initialized = False

        self.app_folder_id = None

    def initialize(self) -> bool:
        """
        Google Drive API 서비스 초기화

        Returns:
            초기화 성공 여부
        """
        if self.initialized:
            return True

        creds = None

        # 저장된 토큰 확인
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        # 유효한 자격 증명이 없으면 로그인
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"credentials.json 파일을 찾을 수 없습니다: {self.credentials_path}\n"
                        "Google Cloud Console에서 OAuth 클라이언트 ID를 생성하고 다운로드하세요."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # 토큰 저장
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())

        # Drive API 서비스 생성
        self.service = build('drive', 'v3', credentials=creds)
        self.initialized = True

        # 앱 전용 폴더 생성/확인
        self._ensure_app_folder()

        logger.info("[GDRIVE CLIENT] [INIT] Google Drive API 초기화 완료")
        return True

    def _ensure_app_folder(self) -> None:
        """앱 전용 폴더 생성 또는 확인"""
        folder_name = "FileManagementAgent"

        # 기존 폴더 검색
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(q=query, fields="files(id, name)").execute()
        folders = results.get('files', [])

        if folders:
            self.app_folder_id = folders[0]['id']
        else:
            # 새 폴더 생성
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            folder = self.service.files().create(body=file_metadata, fields='id').execute()
            self.app_folder_id = folder.get('id')
            logger.info(f"[GDRIVE CLIENT] 앱 폴더 생성됨: {folder_name}")

    @staticmethod
    def create_storage_ref(file_id: str) -> str: # [ 2 ]
        """storage_ref 생성"""
        return f"gdrive://file/{file_id}"

    @staticmethod
    def parse_storage_ref(storage_ref: str) -> Optional[str]:
        """storage_ref에서 file_id 추출"""
        if storage_ref and storage_ref.startswith("gdrive://file/"):
            return storage_ref.replace("gdrive://file/", "")
        return storage_ref  # 이미 file_id인 경우 그대로 반환

    def upload_file( # [ 3 ]
        self,
        content: bytes,
        filename: str,
        mime_type: str = "application/octet-stream",
        description: str = None,
        parent_folder_id: str = None
    ) -> Dict[str, Any]:
        """
        파일 업로드

        Args:
            content: 파일 내용 (바이트)
            filename: 파일명
            mime_type: MIME 타입
            description: 파일 설명
            parent_folder_id: 부모 폴더 ID (None이면 앱 폴더에 저장)

        Returns:
            업로드 결과 (file_id, storage_ref, web_link 등)
        """
        if not self.initialized:
            self.initialize()

        # 파일 메타데이터
        file_metadata = {
            'name': filename,
            'description': description or f"Uploaded by FileManagementAgent at {datetime.now().isoformat()}"
        }

        # 부모 폴더 설정
        parent_id = parent_folder_id or self.app_folder_id
        if parent_id:
            file_metadata['parents'] = [parent_id]

        # 파일 업로드
        media = MediaIoBaseUpload(
            io.BytesIO(content),
            mimetype=mime_type,
            resumable=True
        )

        try:
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, mimeType, size, createdTime, modifiedTime, webViewLink, webContentLink'
            ).execute()

            return {
                "file_id": file.get('id'),
                "storage_ref": self.create_storage_ref(file.get('id')),
                "filename": file.get('name'),
                "mime_type": file.get('mimeType'),
                "size": int(file.get('size', 0)),
                "created_at": file.get('createdTime'),
                "updated_at": file.get('modifiedTime'),
                "web_view_link": file.get('webViewLink'),
                "web_content_link": file.get('webContentLink'),
            }
        except HttpError as e:
            raise Exception(f"파일 업로드 실패: {e}")

    def get_file_info(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        파일 정보 조회

        Args:
            file_id: 파일 ID 또는 storage_ref

        Returns:
            파일 메타데이터
        """
        if not self.initialized:
            self.initialize()

        file_id = self.parse_storage_ref(file_id)

        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size, createdTime, modifiedTime, description, webViewLink, webContentLink, parents, trashed'
            ).execute()

            return {
                "file_id": file.get('id'),
                "storage_ref": self.create_storage_ref(file.get('id')),
                "filename": file.get('name'),
                "mime_type": file.get('mimeType'),
                "size": int(file.get('size', 0)),
                "created_at": file.get('createdTime'),
                "updated_at": file.get('modifiedTime'),
                "description": file.get('description'),
                "web_view_link": file.get('webViewLink'),
                "web_content_link": file.get('webContentLink'),
                "parent_folders": file.get('parents', []),
                "is_trashed": file.get('trashed', False),
            }
        except HttpError as e:
            if e.resp.status == 404:
                return None
            raise Exception(f"파일 정보 조회 실패: {e}")

    def list_files(
        self,
        query: str = None,
        page_size: int = 50,
        folder_id: str = None,
        include_trashed: bool = False
    ) -> List[Dict[str, Any]]:
        """
        파일 목록 조회

        Args:
            query: 검색 쿼리 (Google Drive 쿼리 문법)
            page_size: 최대 반환 수
            folder_id: 특정 폴더 내 검색 (None이면 앱 폴더)
            include_trashed: 휴지통 파일 포함 여부

        Returns:
            파일 목록
        """
        if not self.initialized:
            self.initialize()

        # 기본 쿼리 구성
        query_parts = []

        # 폴더 필터
        parent_id = folder_id or self.app_folder_id
        if parent_id:
            query_parts.append(f"'{parent_id}' in parents")

        # 휴지통 제외
        if not include_trashed:
            query_parts.append("trashed=false")

        # 사용자 쿼리 추가
        if query:
            query_parts.append(f"({query})")

        final_query = " and ".join(query_parts) if query_parts else None

        try:
            results = self.service.files().list(
                q=final_query,
                pageSize=page_size,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink)"
            ).execute()

            files = results.get('files', [])

            return [
                {
                    "file_id": f.get('id'),
                    "storage_ref": self.create_storage_ref(f.get('id')),
                    "filename": f.get('name'),
                    "mime_type": f.get('mimeType'),
                    "size": int(f.get('size', 0)),
                    "created_at": f.get('createdTime'),
                    "updated_at": f.get('modifiedTime'),
                    "web_view_link": f.get('webViewLink'),
                }
                for f in files
            ]
        except HttpError as e:
            raise Exception(f"파일 목록 조회 실패: {e}")

    def delete_file(self, file_id: str, permanent: bool = False) -> bool:
        """
        파일 삭제

        Args:
            file_id: 파일 ID 또는 storage_ref
            permanent: 영구 삭제 여부 (False면 휴지통으로 이동)

        Returns:
            삭제 성공 여부
        """
        if not self.initialized:
            self.initialize()

        file_id = self.parse_storage_ref(file_id)

        try:
            if permanent:
                # 영구 삭제
                self.service.files().delete(fileId=file_id).execute()
            else:
                # 휴지통으로 이동
                self.service.files().update(
                    fileId=file_id,
                    body={'trashed': True}
                ).execute()
            return True
        except HttpError as e:
            if e.resp.status == 404:
                return False
            raise Exception(f"파일 삭제 실패: {e}")

    def update_file(
        self,
        file_id: str,
        content: bytes = None,
        new_name: str = None,
        new_description: str = None
    ) -> Dict[str, Any]:
        """
        파일 업데이트 (새 버전 생성)

        Args:
            file_id: 파일 ID 또는 storage_ref
            content: 새 파일 내용 (바이트)
            new_name: 새 파일명
            new_description: 새 설명

        Returns:
            업데이트된 파일 정보
        """
        if not self.initialized:
            self.initialize()

        file_id = self.parse_storage_ref(file_id)

        # 메타데이터 업데이트
        file_metadata = {}
        if new_name:
            file_metadata['name'] = new_name
        if new_description:
            file_metadata['description'] = new_description

        try:
            if content:
                # 파일 내용 업데이트 (새 버전)
                media = MediaIoBaseUpload(
                    io.BytesIO(content),
                    mimetype='application/octet-stream',
                    resumable=True
                )
                file = self.service.files().update(
                    fileId=file_id,
                    body=file_metadata if file_metadata else None,
                    media_body=media,
                    fields='id, name, mimeType, size, createdTime, modifiedTime, webViewLink'
                ).execute()
            else:
                # 메타데이터만 업데이트
                file = self.service.files().update(
                    fileId=file_id,
                    body=file_metadata,
                    fields='id, name, mimeType, size, createdTime, modifiedTime, webViewLink'
                ).execute()

            return {
                "file_id": file.get('id'),
                "storage_ref": self.create_storage_ref(file.get('id')),
                "filename": file.get('name'),
                "mime_type": file.get('mimeType'),
                "size": int(file.get('size', 0)),
                "created_at": file.get('createdTime'),
                "updated_at": file.get('modifiedTime'),
                "web_view_link": file.get('webViewLink'),
            }
        except HttpError as e:
            raise Exception(f"파일 업데이트 실패: {e}")

    def read_file_content(self, file_id: str, max_chars: int = 5000) -> Optional[Dict[str, Any]]:
        """
        텍스트 파일 내용 읽기

        Args:
            file_id: 파일 ID 또는 storage_ref
            max_chars: 최대 문자 수 (기본값: 5000)

        Returns:
            파일 정보 및 내용
        """
        if not self.initialized:
            self.initialize()

        file_id = self.parse_storage_ref(file_id)

        try:
            # 파일 정보 조회
            info = self.service.files().get(fileId=file_id, fields='name, mimeType').execute()

            # 파일 다운로드
            content = self.download_file(file_id)
            if content is None:
                return None

            # 텍스트 변환 시도
            try:
                text = content.decode('utf-8')
            except UnicodeDecodeError:
                text = f"[바이너리 파일: {len(content)} bytes]"

            return {
                "filename": info['name'],
                "mime_type": info['mimeType'],
                "content": text[:max_chars],
                "size": len(content),
                "truncated": len(text) > max_chars
            }
        except HttpError as e:
            if e.resp.status == 404:
                return None
            raise Exception(f"파일 내용 읽기 실패: {e}")

    def download_file_as_base64(self, file_id: str) -> Optional[Dict[str, Any]]:
        """
        파일을 Base64로 인코딩하여 다운로드 (Google Docs export 지원)

        Args:
            file_id: 파일 ID 또는 storage_ref

        Returns:
            Base64 인코딩된 파일 내용 및 메타데이터
        """
        import base64

        if not self.initialized:
            self.initialize()

        file_id = self.parse_storage_ref(file_id)

        try:
            # 파일 정보 조회
            info = self.service.files().get(
                fileId=file_id,
                fields='id, name, mimeType, size'
            ).execute()

            mime_type = info['mimeType']
            logger.info(f"[GDRIVE CLIENT] [DOWNLOAD] 파일 정보: {info['name']}, mimeType: {mime_type}")

            # Google Docs 형식인 경우 export 사용
            google_export_mapping = {
                'application/vnd.google-apps.document': ('application/pdf', 'pdf'),
                'application/vnd.google-apps.spreadsheet': ('application/pdf', 'pdf'),
                'application/vnd.google-apps.presentation': ('application/pdf', 'pdf'),
            }

            if mime_type in google_export_mapping:
                export_mime, _ = google_export_mapping[mime_type]
                logger.info(f"[GDRIVE CLIENT] [DOWNLOAD] Google Docs 형식, PDF로 export: {export_mime}")
                request = self.service.files().export_media(fileId=file_id, mimeType=export_mime)
                final_mime_type = export_mime
            else:
                # 일반 파일은 get_media 사용
                request = self.service.files().get_media(fileId=file_id)
                final_mime_type = mime_type

            # 다운로드
            buffer = io.BytesIO()
            downloader = MediaIoBaseDownload(buffer, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()

            content = buffer.getvalue()
            logger.info(f"[GDRIVE CLIENT] [DOWNLOAD] 다운로드 완료: {len(content)} bytes")

            # Base64 인코딩
            base64_content = base64.b64encode(content).decode('utf-8')

            return {
                "file_id": file_id,
                "storage_ref": self.create_storage_ref(file_id),
                "filename": info['name'],
                "mime_type": final_mime_type,
                "size": len(content),
                "base64_content": base64_content
            }
        except HttpError as e:
            if e.resp.status == 404:
                return None
            raise Exception(f"파일 다운로드 실패: {e}")

    def find_folder_by_name(self, folder_name: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """
        폴더 이름으로 검색

        Args:
            folder_name: 검색할 폴더 이름
            max_results: 최대 결과 수 (기본값: 10)

        Returns:
            폴더 목록
        """
        if not self.initialized:
            self.initialize()

        query = f"name contains '{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"

        try:
            results = self.service.files().list(
                q=query,
                pageSize=max_results,
                fields="files(id, name, webViewLink, createdTime)"
            ).execute()

            folders = results.get('files', [])

            return [
                {
                    "folder_id": f.get('id'),
                    "storage_ref": self.create_storage_ref(f.get('id')),
                    "folder_name": f.get('name'),
                    "web_view_link": f.get('webViewLink'),
                    "created_at": f.get('createdTime')
                }
                for f in folders
            ]
        except HttpError as e:
            raise Exception(f"폴더 검색 실패: {e}")

    def create_folder(self, folder_name: str, parent_folder_id: str = None) -> Dict[str, Any]:
        """
        폴더 생성

        Args:
            folder_name: 폴더명
            parent_folder_id: 부모 폴더 ID

        Returns:
            생성된 폴더 정보
        """
        if not self.initialized:
            self.initialize()

        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        parent_id = parent_folder_id or self.app_folder_id
        if parent_id:
            file_metadata['parents'] = [parent_id]

        try:
            folder = self.service.files().create(
                body=file_metadata,
                fields='id, name, createdTime, webViewLink'
            ).execute()

            return {
                "file_id": folder.get('id'),
                "storage_ref": self.create_storage_ref(folder.get('id')),
                "folder_name": folder.get('name'),
                "created_at": folder.get('createdTime'),
                "web_view_link": folder.get('webViewLink'),
            }
        except HttpError as e:
            raise Exception(f"폴더 생성 실패: {e}")


_gdrive_client: Optional[GoogleDriveClient] = None


def get_gdrive_client() -> GoogleDriveClient:
    """Google Drive 클라이언트 싱글톤 반환"""
    global _gdrive_client
    if _gdrive_client is None:
        _gdrive_client = GoogleDriveClient()
    return _gdrive_client
