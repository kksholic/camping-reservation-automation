"""인증 및 보안 유틸리티"""
import bcrypt
from functools import wraps
from flask import session, jsonify
from loguru import logger


def hash_password(password: str) -> str:
    """비밀번호 해싱"""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """비밀번호 검증"""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False


def generate_password_hash(password: str) -> str:
    """
    비밀번호 해시 생성 (관리자 비밀번호 설정용)

    사용법:
    python -c "from app.utils.auth import generate_password_hash; print(generate_password_hash('your_password'))"
    """
    return hash_password(password)


def require_auth(f):
    """
    인증 필수 데코레이터

    로그인하지 않은 사용자의 요청을 차단합니다.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            logger.warning(f"Unauthorized access attempt to {f.__name__}")
            return jsonify({'error': 'Unauthorized', 'message': '로그인이 필요합니다'}), 401
        return f(*args, **kwargs)
    return decorated_function


def get_admin_user(username: str):
    """
    DB에서 관리자 사용자 가져오기

    Args:
        username: 사용자 이름

    Returns:
        Admin 모델 객체 또는 None
    """
    from app.models.database import Admin

    try:
        admin = Admin.query.filter_by(username=username).first()
        return admin
    except Exception as e:
        logger.error(f"Error fetching admin user: {e}")
        return None


def authenticate_user(username: str, password: str) -> bool:
    """
    사용자 인증

    Args:
        username: 사용자 이름
        password: 비밀번호 (평문)

    Returns:
        인증 성공 여부
    """
    admin = get_admin_user(username)

    if not admin:
        return False

    return verify_password(password, admin.password_hash)


def create_default_admin():
    """
    기본 관리자 계정 생성 (DB에 admin 계정이 없을 때)

    Returns:
        생성 성공 여부
    """
    from app.models.database import Admin
    from app import db
    import os

    try:
        # 이미 관리자 계정이 있는지 확인
        if Admin.query.first():
            return True

        # 환경 변수 또는 기본값 사용
        default_username = os.getenv('ADMIN_USERNAME', 'admin')
        default_password = os.getenv('ADMIN_PASSWORD', 'admin123')

        # 기본 관리자 계정 생성
        admin = Admin(
            username=default_username,
            password_hash=hash_password(default_password)
        )

        db.session.add(admin)
        db.session.commit()

        logger.info(f"✅ Default admin account created: {default_username}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to create default admin: {e}")
        db.session.rollback()
        return False


def update_admin_credentials(current_username: str, new_username: str = None,
                            current_password: str = None, new_password: str = None) -> tuple[bool, str]:
    """
    관리자 인증 정보 업데이트

    Args:
        current_username: 현재 사용자 이름
        new_username: 새 사용자 이름 (None이면 변경하지 않음)
        current_password: 현재 비밀번호 (비밀번호 변경 시 필수)
        new_password: 새 비밀번호 (None이면 변경하지 않음)

    Returns:
        (성공 여부, 메시지)
    """
    from app.models.database import Admin
    from app import db

    try:
        logger.info(f"🔄 Updating credentials for user: {current_username}")
        logger.debug(f"   new_username: {new_username if new_username else 'N/A'}")
        logger.debug(f"   password change: {'Yes' if new_password else 'No'}")

        # 현재 관리자 가져오기
        admin = get_admin_user(current_username)

        if not admin:
            logger.warning(f"⚠️ Admin account not found: {current_username}")
            return False, "관리자 계정을 찾을 수 없습니다"

        changes_made = []

        # 비밀번호 변경 시 현재 비밀번호 확인
        if new_password:
            if not current_password:
                logger.warning("⚠️ Password change requested but current password not provided")
                return False, "현재 비밀번호를 입력해주세요"

            if not verify_password(current_password, admin.password_hash):
                logger.warning(f"⚠️ Invalid current password for user: {current_username}")
                return False, "현재 비밀번호가 올바르지 않습니다"

            # 새 비밀번호 해시 설정
            old_hash = admin.password_hash[:20]
            admin.password_hash = hash_password(new_password)
            new_hash = admin.password_hash[:20]

            logger.info(f"✅ Password hash updated for user: {current_username}")
            logger.debug(f"   Old hash prefix: {old_hash}...")
            logger.debug(f"   New hash prefix: {new_hash}...")
            changes_made.append("비밀번호")

        # 사용자 이름 변경
        if new_username and new_username != current_username:
            # 새 사용자 이름 중복 확인
            existing = Admin.query.filter_by(username=new_username).first()
            if existing and existing.id != admin.id:
                logger.warning(f"⚠️ Username already exists: {new_username}")
                return False, "이미 사용 중인 아이디입니다"

            logger.info(f"✅ Username will be updated: {current_username} -> {new_username}")
            admin.username = new_username
            changes_made.append("아이디")

        if not changes_made:
            logger.warning("⚠️ No changes requested")
            return False, "변경할 내용이 없습니다"

        # 데이터베이스 커밋
        db.session.commit()
        logger.info(f"✅ Database committed successfully. Changes: {', '.join(changes_made)}")

        # 커밋 후 확인
        updated_admin = get_admin_user(admin.username)
        if updated_admin:
            logger.debug(f"   Verification - Username in DB: {updated_admin.username}")
            logger.debug(f"   Verification - Password hash prefix: {updated_admin.password_hash[:20]}...")

        return True, f"{', '.join(changes_made)} 변경이 성공적으로 완료되었습니다"

    except Exception as e:
        logger.error(f"❌ Failed to update admin credentials: {e}")
        logger.error(f"   Exception type: {type(e).__name__}")
        logger.error(f"   Exception details: {str(e)}")
        db.session.rollback()
        logger.info("🔄 Database rolled back")
        return False, f"계정 정보 업데이트 실패: {str(e)}"
