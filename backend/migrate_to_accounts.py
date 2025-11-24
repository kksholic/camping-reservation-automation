"""
기존 CampingSite의 로그인/예약자 정보를 CampingSiteAccount로 마이그레이션하는 스크립트
"""
import sys
import os

# 프로젝트 루트를 파이썬 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.database import CampingSite, CampingSiteAccount
from loguru import logger

def migrate_camping_site_accounts():
    """기존 CampingSite 데이터를 CampingSiteAccount로 마이그레이션"""
    app = create_app()

    with app.app_context():
        try:
            # 모든 캠핑장 조회
            sites = CampingSite.query.all()
            migrated_count = 0
            skipped_count = 0

            logger.info(f"📋 총 {len(sites)}개의 캠핑장을 확인합니다...")

            for site in sites:
                # 로그인 정보가 있는 경우만 마이그레이션
                if site.login_username and site.login_password:
                    # 이미 계정이 있는지 확인
                    existing_account = CampingSiteAccount.query.filter_by(
                        camping_site_id=site.id,
                        login_username=site.login_username
                    ).first()

                    if existing_account:
                        logger.info(f"⏭️  캠핑장 '{site.name}' - 이미 계정이 존재합니다 (스킵)")
                        skipped_count += 1
                        continue

                    # 새 계정 생성
                    account = CampingSiteAccount(
                        camping_site_id=site.id,
                        login_username=site.login_username,
                        login_password=site.login_password,
                        booker_name=site.booker_name or '',
                        booker_phone=site.booker_phone or '',
                        booker_car_number=site.booker_car_number,
                        is_active=True,
                        priority=0,
                        nickname='기본 계정'
                    )

                    db.session.add(account)
                    migrated_count += 1
                    logger.info(f"✅ 캠핑장 '{site.name}' - 계정 마이그레이션 완료")
                else:
                    logger.info(f"⏭️  캠핑장 '{site.name}' - 로그인 정보 없음 (스킵)")
                    skipped_count += 1

            # 커밋
            if migrated_count > 0:
                db.session.commit()
                logger.success(f"🎉 마이그레이션 완료: {migrated_count}개 계정 생성, {skipped_count}개 스킵")
            else:
                logger.info(f"ℹ️  마이그레이션할 데이터가 없습니다 (스킵: {skipped_count}개)")

            return True

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ 마이그레이션 실패: {e}")
            return False

if __name__ == '__main__':
    logger.info("🚀 캠핑장 계정 마이그레이션 시작...")
    success = migrate_camping_site_accounts()
    sys.exit(0 if success else 1)
