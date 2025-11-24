"""
암호화된 자격증명 관리 유틸리티

사용법:
1. 저장: python credentials_manager.py save
2. 조회: python credentials_manager.py get
3. 암호화 파일: credentials.enc (자동 생성)
"""
import os
import json
import getpass
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CredentialsManager:
    """암호화된 자격증명 관리자"""

    def __init__(self, filename='credentials.enc'):
        self.filename = filename
        self.salt_file = '.credentials.salt'

    def _get_or_create_salt(self) -> bytes:
        """Salt 생성 또는 로드"""
        if os.path.exists(self.salt_file):
            with open(self.salt_file, 'rb') as f:
                return f.read()
        else:
            salt = os.urandom(16)
            with open(self.salt_file, 'wb') as f:
                f.write(salt)
            return salt

    def _derive_key(self, password: str) -> bytes:
        """비밀번호로부터 암호화 키 생성"""
        salt = self._get_or_create_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        # Fernet는 base64 인코딩된 32바이트 키를 기대함
        from base64 import urlsafe_b64encode
        return urlsafe_b64encode(key)

    def save_credentials(self, credentials: dict, master_password: str):
        """
        자격증명을 암호화하여 저장

        Args:
            credentials: {'user_id': '...', 'password': '...', ...}
            master_password: 마스터 비밀번호
        """
        # 암호화 키 생성
        key = self._derive_key(master_password)
        f = Fernet(key)

        # JSON 직렬화 및 암호화
        data = json.dumps(credentials).encode()
        encrypted = f.encrypt(data)

        # 파일 저장
        with open(self.filename, 'wb') as file:
            file.write(encrypted)

        print(f"✅ 자격증명이 암호화되어 저장되었습니다: {self.filename}")

    def load_credentials(self, master_password: str) -> dict:
        """
        암호화된 자격증명 로드

        Args:
            master_password: 마스터 비밀번호

        Returns:
            {'user_id': '...', 'password': '...'}
        """
        if not os.path.exists(self.filename):
            raise FileNotFoundError(f"암호화 파일이 없습니다: {self.filename}")

        # 암호화 키 생성
        key = self._derive_key(master_password)
        f = Fernet(key)

        # 파일 읽기 및 복호화
        with open(self.filename, 'rb') as file:
            encrypted = file.read()

        try:
            decrypted = f.decrypt(encrypted)
            credentials = json.loads(decrypted.decode())
            return credentials
        except Exception as e:
            raise ValueError("잘못된 마스터 비밀번호이거나 파일이 손상되었습니다")

    def update_credential(self, key: str, value: str, master_password: str):
        """특정 자격증명 업데이트"""
        credentials = self.load_credentials(master_password)
        credentials[key] = value
        self.save_credentials(credentials, master_password)
        print(f"✅ {key} 업데이트 완료")


def interactive_save():
    """대화형 저장"""
    print("=" * 60)
    print("🔐 자격증명 암호화 저장")
    print("=" * 60)

    # 자격증명 입력
    print("\n📝 자격증명 입력:")
    user_id = input("사용자 ID: ")
    password = getpass.getpass("비밀번호: ")

    # 추가 정보 (선택사항)
    print("\n📝 추가 정보 (선택사항, Enter로 건너뛰기):")
    name = input("이름: ")
    phone = input("휴대폰: ")
    car_number = input("차량번호: ")

    credentials = {
        'user_id': user_id,
        'password': password,
    }

    if name:
        credentials['name'] = name
    if phone:
        credentials['phone'] = phone
    if car_number:
        credentials['car_number'] = car_number

    # 마스터 비밀번호 입력
    print("\n🔑 마스터 비밀번호 설정:")
    print("(이 비밀번호로 자격증명이 암호화됩니다. 절대 잊지 마세요!)")
    master_password = getpass.getpass("마스터 비밀번호: ")
    master_password_confirm = getpass.getpass("마스터 비밀번호 확인: ")

    if master_password != master_password_confirm:
        print("❌ 비밀번호가 일치하지 않습니다.")
        return

    # 저장
    manager = CredentialsManager()
    manager.save_credentials(credentials, master_password)

    print("\n✅ 완료!")
    print(f"암호화 파일: {manager.filename}")
    print(f"Salt 파일: {manager.salt_file}")
    print("\n⚠️ 중요: 마스터 비밀번호를 절대 잊지 마세요!")


def interactive_load():
    """대화형 로드"""
    print("=" * 60)
    print("🔓 자격증명 조회")
    print("=" * 60)

    manager = CredentialsManager()

    if not os.path.exists(manager.filename):
        print(f"❌ 암호화 파일이 없습니다: {manager.filename}")
        print("먼저 'python credentials_manager.py save'로 저장하세요.")
        return

    # 마스터 비밀번호 입력
    master_password = getpass.getpass("\n🔑 마스터 비밀번호: ")

    try:
        credentials = manager.load_credentials(master_password)

        print("\n✅ 자격증명 조회 성공!")
        print("=" * 60)
        for key, value in credentials.items():
            if key == 'password':
                # 비밀번호는 마스킹
                print(f"{key}: {'*' * len(value)}")
            else:
                print(f"{key}: {value}")
        print("=" * 60)

        return credentials

    except ValueError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ 에러: {e}")


def main():
    """메인 함수"""
    import sys

    if len(sys.argv) < 2:
        print("사용법:")
        print("  저장: python credentials_manager.py save")
        print("  조회: python credentials_manager.py get")
        return

    command = sys.argv[1]

    if command == 'save':
        interactive_save()
    elif command == 'get':
        interactive_load()
    else:
        print(f"알 수 없는 명령: {command}")
        print("사용 가능한 명령: save, get")


if __name__ == "__main__":
    main()
