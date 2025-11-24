"""자격증명 관리자 자동 테스트"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from credentials_manager import CredentialsManager


def test_save_and_load():
    """저장 및 로드 테스트"""
    print("=" * 60)
    print("🧪 자격증명 암호화 테스트")
    print("=" * 60)

    # 테스트용 자격증명
    test_credentials = {
        'user_id': 'test_user',
        'password': 'test_password_123!',
        'name': '홍길동',
        'phone': '01012345678',
        'car_number': '12가3456'
    }

    # 테스트용 마스터 비밀번호
    master_password = 'TestMasterPassword123!'

    print("\n📝 테스트 데이터:")
    for key, value in test_credentials.items():
        if key == 'password':
            print(f"  {key}: {'*' * len(value)}")
        else:
            print(f"  {key}: {value}")

    print(f"\n🔑 마스터 비밀번호: {'*' * len(master_password)}")

    # 매니저 생성
    manager = CredentialsManager('test_credentials.enc')

    # Step 1: 저장
    print("\n" + "=" * 60)
    print("STEP 1: 암호화하여 저장")
    print("=" * 60)
    manager.save_credentials(test_credentials, master_password)

    # 파일 확인
    if os.path.exists('test_credentials.enc'):
        file_size = os.path.getsize('test_credentials.enc')
        print(f"✅ 파일 생성됨: test_credentials.enc ({file_size} bytes)")

        # 파일 내용 보기 (암호화되어 읽을 수 없음)
        with open('test_credentials.enc', 'rb') as f:
            encrypted_data = f.read()
            print(f"\n📄 암호화된 내용 (처음 100바이트):")
            print(f"   {encrypted_data[:100]}...")
            print(f"   → 암호화되어 읽을 수 없습니다!")
    else:
        print("❌ 파일 생성 실패")
        return False

    # Step 2: 잘못된 비밀번호로 시도
    print("\n" + "=" * 60)
    print("STEP 2: 잘못된 비밀번호로 복호화 시도")
    print("=" * 60)
    try:
        wrong_password = 'WrongPassword123!'
        print(f"🔑 잘못된 비밀번호: {'*' * len(wrong_password)}")
        manager.load_credentials(wrong_password)
        print("❌ 테스트 실패: 잘못된 비밀번호로 복호화되면 안됩니다!")
        return False
    except ValueError as e:
        print(f"✅ 예상대로 실패함: {e}")

    # Step 3: 올바른 비밀번호로 로드
    print("\n" + "=" * 60)
    print("STEP 3: 올바른 비밀번호로 복호화")
    print("=" * 60)
    try:
        print(f"🔑 올바른 비밀번호: {'*' * len(master_password)}")
        loaded_credentials = manager.load_credentials(master_password)

        print("\n✅ 복호화 성공!")
        print("\n📄 복호화된 데이터:")
        for key, value in loaded_credentials.items():
            if key == 'password':
                print(f"  {key}: {'*' * len(value)}")
            else:
                print(f"  {key}: {value}")

        # 데이터 일치 확인
        print("\n" + "=" * 60)
        print("STEP 4: 데이터 일치 확인")
        print("=" * 60)

        all_match = True
        for key in test_credentials:
            original = test_credentials[key]
            loaded = loaded_credentials.get(key)

            if original == loaded:
                print(f"  ✅ {key}: 일치")
            else:
                print(f"  ❌ {key}: 불일치 (원본: {original}, 로드: {loaded})")
                all_match = False

        if all_match:
            print("\n" + "=" * 60)
            print("🎉 모든 테스트 성공!")
            print("=" * 60)
            print("\n✅ 암호화/복호화가 정상적으로 작동합니다.")
            print("✅ 잘못된 비밀번호는 차단됩니다.")
            print("✅ 데이터가 정확하게 보존됩니다.")
        else:
            print("\n❌ 테스트 실패: 데이터 불일치")
            return False

    except Exception as e:
        print(f"❌ 복호화 실패: {e}")
        return False

    # 정리
    print("\n" + "=" * 60)
    print("🧹 테스트 파일 정리")
    print("=" * 60)
    try:
        os.remove('test_credentials.enc')
        print("✅ test_credentials.enc 삭제됨")
    except:
        pass

    try:
        os.remove('.credentials.salt')
        print("✅ .credentials.salt 삭제됨")
    except:
        pass

    return True


if __name__ == "__main__":
    success = test_save_and_load()

    print("\n" + "=" * 60)
    if success:
        print("✅ 테스트 완료: 정상 작동")
        print("\n📝 이제 실제 자격증명을 저장하려면:")
        print("   python credentials_manager.py save")
    else:
        print("❌ 테스트 실패")
    print("=" * 60)
