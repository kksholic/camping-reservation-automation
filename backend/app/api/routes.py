"""API 라우트"""
from flask import Blueprint, jsonify, request, session
from loguru import logger

from app.models.database import CampingSite, CampingSiteAccount, Reservation, MonitoringTarget, UserInfo
from app.services.monitor_service import MonitorService
from app.services.reservation_service import ReservationService
from app.services.multi_account_reservation_service import MultiAccountReservationService
from app.utils.auth import authenticate_user, require_auth
from app import db, limiter
import os


bp = Blueprint('api', __name__, url_prefix='/api')

# 서비스 초기화
monitor_service = MonitorService()
reservation_service = ReservationService()
multi_account_service = MultiAccountReservationService()


@bp.route('/health', methods=['GET'])
def health_check():
    """헬스 체크"""
    return jsonify({'status': 'healthy', 'message': 'Server is running'}), 200


# 인증 관련
@bp.route('/auth/login', methods=['POST'])
@limiter.limit("5 per minute")  # 1분에 5번까지만 시도 가능
def login():
    """로그인 (Rate Limiting 적용)"""
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': '아이디와 비밀번호를 입력해주세요'}), 400

    # 인증 시도
    if authenticate_user(username, password):
        # 세션에 로그인 정보 저장
        session.permanent = True  # 영구 세션 (PERMANENT_SESSION_LIFETIME 설정 적용)
        session['logged_in'] = True
        session['username'] = username
        logger.info(f"✅ User logged in: {username} from IP: {request.remote_addr}")
        return jsonify({'success': True, 'message': '로그인 성공'}), 200
    else:
        logger.warning(f"⚠️ Failed login attempt for user: {username} from IP: {request.remote_addr}")
        return jsonify({'success': False, 'message': '아이디 또는 비밀번호가 올바르지 않습니다'}), 401


@bp.route('/auth/logout', methods=['POST'])
@require_auth
def logout():
    """로그아웃"""
    username = session.get('username')
    session.clear()
    logger.info(f"✅ User logged out: {username}")
    return jsonify({'success': True, 'message': '로그아웃 되었습니다'}), 200


@bp.route('/auth/check', methods=['GET'])
def check_auth():
    """인증 상태 확인 (인증 불필요)"""
    if session.get('logged_in'):
        return jsonify({'authenticated': True, 'username': session.get('username')}), 200
    else:
        return jsonify({'authenticated': False}), 200


@bp.route('/auth/change-credentials', methods=['POST'])
@require_auth
def change_credentials():
    """관리자 계정 정보 변경"""
    from app.utils.auth import update_admin_credentials

    data = request.json
    current_username = session.get('username')

    if not current_username:
        return jsonify({'success': False, 'message': '세션이 만료되었습니다'}), 401

    new_username = data.get('new_username')
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    # 최소한 하나의 변경사항이 있는지 확인
    if not new_username and not new_password:
        return jsonify({'success': False, 'message': '변경할 정보를 입력해주세요'}), 400

    # 계정 정보 업데이트
    success, message = update_admin_credentials(
        current_username=current_username,
        new_username=new_username,
        current_password=current_password,
        new_password=new_password
    )

    if success:
        # 사용자 이름이 변경된 경우 세션 업데이트
        if new_username and new_username != current_username:
            session['username'] = new_username
            logger.info(f"✅ Session username updated: {current_username} -> {new_username}")

        return jsonify({'success': True, 'message': message}), 200
    else:
        return jsonify({'success': False, 'message': message}), 400


# 캠핑장 관리
@bp.route('/camping-sites', methods=['GET'])
@require_auth
def get_camping_sites():
    """캠핑장 목록 조회"""
    sites = CampingSite.query.all()
    return jsonify([site.to_dict() for site in sites]), 200


@bp.route('/camping-sites', methods=['POST'])
@require_auth
def create_camping_site():
    """캠핑장 추가"""
    data = request.json

    site = CampingSite(
        name=data['name'],
        site_type=data['site_type'],
        url=data['url'],
        login_username=data.get('login_username'),
        login_password=data.get('login_password'),
        booker_name=data.get('booker_name'),
        booker_phone=data.get('booker_phone'),
        booker_car_number=data.get('booker_car_number')
    )

    db.session.add(site)
    db.session.commit()

    logger.info(f"Created camping site: {site.name}")
    return jsonify(site.to_dict()), 201


@bp.route('/camping-sites/<int:site_id>', methods=['PUT'])
@require_auth
def update_camping_site(site_id):
    """캠핑장 정보 업데이트"""
    site = CampingSite.query.get_or_404(site_id)
    data = request.json

    site.name = data.get('name', site.name)
    site.site_type = data.get('site_type', site.site_type)
    site.url = data.get('url', site.url)
    site.login_username = data.get('login_username', site.login_username)
    site.login_password = data.get('login_password', site.login_password)
    site.booker_name = data.get('booker_name', site.booker_name)
    site.booker_phone = data.get('booker_phone', site.booker_phone)
    site.booker_car_number = data.get('booker_car_number', site.booker_car_number)

    db.session.commit()

    logger.info(f"Updated camping site: {site.name}")
    return jsonify(site.to_dict()), 200


@bp.route('/camping-sites/<int:site_id>', methods=['DELETE'])
@require_auth
def delete_camping_site(site_id):
    """캠핑장 삭제"""
    site = CampingSite.query.get_or_404(site_id)
    db.session.delete(site)
    db.session.commit()

    logger.info(f"Deleted camping site: {site.name}")
    return jsonify({'message': 'Camping site deleted'}), 200


# 캠핑장 계정 관리
@bp.route('/camping-sites/<int:site_id>/accounts', methods=['GET'])
@require_auth
def get_site_accounts(site_id):
    """특정 캠핑장의 계정 목록 조회"""
    site = CampingSite.query.get_or_404(site_id)
    accounts = CampingSiteAccount.query.filter_by(camping_site_id=site_id).order_by(CampingSiteAccount.priority).all()
    return jsonify([account.to_dict() for account in accounts]), 200


@bp.route('/camping-sites/<int:site_id>/accounts', methods=['POST'])
@require_auth
def create_site_account(site_id):
    """캠핑장 계정 추가"""
    site = CampingSite.query.get_or_404(site_id)
    data = request.json

    # 필수 필드 검증
    required_fields = ['login_username', 'login_password', 'booker_name', 'booker_phone']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'success': False, 'message': f'{field}는 필수 입력 항목입니다'}), 400

    # 같은 캠핑장에 동일한 로그인 아이디가 있는지 확인
    existing = CampingSiteAccount.query.filter_by(
        camping_site_id=site_id,
        login_username=data['login_username']
    ).first()

    if existing:
        return jsonify({'success': False, 'message': '이미 등록된 로그인 아이디입니다'}), 400

    # 새 계정 생성
    account = CampingSiteAccount(
        camping_site_id=site_id,
        login_username=data['login_username'],
        login_password=data['login_password'],
        booker_name=data['booker_name'],
        booker_phone=data['booker_phone'],
        booker_car_number=data.get('booker_car_number'),
        is_active=data.get('is_active', True),
        priority=data.get('priority', 0),
        nickname=data.get('nickname')
    )

    db.session.add(account)
    db.session.commit()

    logger.info(f"Created account for camping site '{site.name}': {account.login_username}")
    return jsonify(account.to_dict()), 201


@bp.route('/camping-sites/<int:site_id>/accounts/<int:account_id>', methods=['PUT'])
@require_auth
def update_site_account(site_id, account_id):
    """캠핑장 계정 수정"""
    site = CampingSite.query.get_or_404(site_id)
    account = CampingSiteAccount.query.filter_by(id=account_id, camping_site_id=site_id).first_or_404()
    data = request.json

    # 필드 업데이트
    if 'login_username' in data:
        # 동일한 아이디가 이미 있는지 확인
        existing = CampingSiteAccount.query.filter_by(
            camping_site_id=site_id,
            login_username=data['login_username']
        ).first()
        if existing and existing.id != account_id:
            return jsonify({'success': False, 'message': '이미 등록된 로그인 아이디입니다'}), 400
        account.login_username = data['login_username']

    if 'login_password' in data:
        account.login_password = data['login_password']
    if 'booker_name' in data:
        account.booker_name = data['booker_name']
    if 'booker_phone' in data:
        account.booker_phone = data['booker_phone']
    if 'booker_car_number' in data:
        account.booker_car_number = data['booker_car_number']
    if 'is_active' in data:
        account.is_active = data['is_active']
    if 'priority' in data:
        account.priority = data['priority']
    if 'nickname' in data:
        account.nickname = data['nickname']

    db.session.commit()

    logger.info(f"Updated account for camping site '{site.name}': {account.login_username}")
    return jsonify(account.to_dict()), 200


@bp.route('/camping-sites/<int:site_id>/accounts/<int:account_id>', methods=['DELETE'])
@require_auth
def delete_site_account(site_id, account_id):
    """캠핑장 계정 삭제"""
    site = CampingSite.query.get_or_404(site_id)
    account = CampingSiteAccount.query.filter_by(id=account_id, camping_site_id=site_id).first_or_404()

    username = account.login_username
    db.session.delete(account)
    db.session.commit()

    logger.info(f"Deleted account from camping site '{site.name}': {username}")
    return jsonify({'message': 'Account deleted successfully'}), 200


@bp.route('/camping-sites/<int:site_id>/accounts/<int:account_id>/toggle', methods=['POST'])
@require_auth
def toggle_site_account(site_id, account_id):
    """캠핑장 계정 활성화/비활성화 토글"""
    site = CampingSite.query.get_or_404(site_id)
    account = CampingSiteAccount.query.filter_by(id=account_id, camping_site_id=site_id).first_or_404()

    account.is_active = not account.is_active
    db.session.commit()

    status = "활성화" if account.is_active else "비활성화"
    logger.info(f"Toggled account for camping site '{site.name}': {account.login_username} -> {status}")
    return jsonify({'success': True, 'is_active': account.is_active, 'message': f'계정이 {status}되었습니다'}), 200


# 모니터링 관리
@bp.route('/monitoring/targets', methods=['GET'])
@require_auth
def get_monitoring_targets():
    """모니터링 타겟 목록"""
    targets = MonitoringTarget.query.filter_by(is_active=True).all()
    return jsonify([target.to_dict() for target in targets]), 200


@bp.route('/monitoring/targets', methods=['POST'])
@require_auth
def create_monitoring_target():
    """모니터링 타겟 추가"""
    data = request.json

    target = MonitoringTarget(
        camping_site_id=data['camping_site_id'],
        target_date=data['target_date'],
        is_active=True
    )

    db.session.add(target)
    db.session.commit()

    logger.info(f"Created monitoring target for site {target.camping_site_id}")
    return jsonify(target.to_dict()), 201


@bp.route('/monitoring/start', methods=['POST'])
@require_auth
def start_monitoring():
    """모니터링 시작"""
    try:
        monitor_service.start()
        return jsonify({'message': 'Monitoring started'}), 200
    except Exception as e:
        logger.error(f"Failed to start monitoring: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/monitoring/stop', methods=['POST'])
@require_auth
def stop_monitoring():
    """모니터링 중지"""
    try:
        monitor_service.stop()
        return jsonify({'message': 'Monitoring stopped'}), 200
    except Exception as e:
        logger.error(f"Failed to stop monitoring: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/monitoring/status', methods=['GET'])
@require_auth
def get_monitoring_status():
    """모니터링 상태 조회"""
    status = monitor_service.get_status()
    return jsonify(status), 200


@bp.route('/monitoring/schedule', methods=['POST'])
@require_auth
def schedule_monitoring():
    """특정 시간에 예약 실행 스케줄 등록"""
    data = request.json

    try:
        hour = data.get('hour')
        minute = data.get('minute')
        second = data.get('second', 0)

        if hour is None or minute is None:
            return jsonify({'error': 'hour and minute are required'}), 400

        if not (0 <= hour <= 23):
            return jsonify({'error': 'hour must be between 0 and 23'}), 400

        if not (0 <= minute <= 59):
            return jsonify({'error': 'minute must be between 0 and 59'}), 400

        if not (0 <= second <= 59):
            return jsonify({'error': 'second must be between 0 and 59'}), 400

        job_id = monitor_service.schedule_at_specific_time(
            hour=hour,
            minute=minute,
            second=second,
            job_id=data.get('job_id')
        )

        return jsonify({
            'message': 'Schedule created',
            'job_id': job_id,
            'scheduled_time': f'{hour:02d}:{minute:02d}:{second:02d}'
        }), 200

    except Exception as e:
        logger.error(f"Failed to create schedule: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/monitoring/schedule/<job_id>', methods=['DELETE'])
@require_auth
def delete_schedule(job_id):
    """스케줄 삭제"""
    try:
        success = monitor_service.remove_scheduled_job(job_id)

        if success:
            return jsonify({'message': 'Schedule deleted'}), 200
        else:
            return jsonify({'error': 'Failed to delete schedule'}), 500

    except Exception as e:
        logger.error(f"Failed to delete schedule: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/monitoring/schedules', methods=['GET'])
@require_auth
def get_schedules():
    """스케줄 목록 조회"""
    try:
        schedules = monitor_service.list_scheduled_jobs()
        return jsonify(schedules), 200

    except Exception as e:
        logger.error(f"Failed to get schedules: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/monitoring/server-time', methods=['GET'])
@require_auth
def get_server_time_info():
    """XTicket 서버 시간 동기화 정보 조회"""
    try:
        from app.scrapers.xticket_scraper import XTicketScraper
        import os
        from datetime import datetime

        shop_encode = os.getenv('XTICKET_SHOP_ENCODE')
        shop_code = os.getenv('XTICKET_SHOP_CODE')

        if not shop_encode or not shop_code:
            return jsonify({'error': 'XTicket credentials not configured'}), 400

        scraper = XTicketScraper(
            shop_encode=shop_encode,
            shop_code=shop_code
        )

        # 서버 시간 가져오기
        server_time = scraper.get_server_time()
        local_time = datetime.utcnow()

        # 서버 시간 동기화
        scraper.sync_server_time()

        if server_time:
            return jsonify({
                'success': True,
                'server_time': server_time.isoformat(),
                'local_time': local_time.isoformat(),
                'offset_seconds': scraper.server_time_offset,
                'adjusted_local_time': scraper.get_adjusted_local_time().isoformat(),
                'message': f'서버 시간 오프셋: {scraper.server_time_offset:.2f}초'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to get server time'
            }), 500

    except Exception as e:
        logger.error(f"Failed to get server time info: {e}")
        return jsonify({'error': str(e)}), 500


# 예약 관리
@bp.route('/reservations', methods=['GET'])
@require_auth
def get_reservations():
    """예약 목록 조회"""
    reservations = Reservation.query.order_by(Reservation.created_at.desc()).all()
    return jsonify([r.to_dict() for r in reservations]), 200


@bp.route('/reservations/<int:reservation_id>', methods=['GET'])
@require_auth
def get_reservation(reservation_id):
    """예약 상세 조회"""
    reservation = Reservation.query.get_or_404(reservation_id)
    return jsonify(reservation.to_dict()), 200


@bp.route('/reservations', methods=['POST'])
@require_auth
def create_reservation():
    """수동 예약 생성"""
    data = request.json

    try:
        result = reservation_service.create_reservation(
            camping_site_id=data['camping_site_id'],
            check_in_date=data['check_in_date'],
            check_out_date=data['check_out_date'],
            user_info=data.get('user_info', {})
        )

        return jsonify(result), 201
    except Exception as e:
        logger.error(f"Failed to create reservation: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/reservations/multi-account', methods=['POST'])
@require_auth
def create_multi_account_reservation():
    """여러 계정으로 동시 예약 시도"""
    data = request.json

    try:
        camping_site = CampingSite.query.get_or_404(data['camping_site_id'])

        result = multi_account_service.attempt_reservation_with_accounts(
            camping_site=camping_site,
            target_date=data['target_date'],
            site_name=data.get('site_name'),
            zone_code=data.get('zone_code')
        )

        return jsonify(result), 200 if result['success'] else 400
    except Exception as e:
        logger.error(f"Failed to create multi-account reservation: {e}")
        return jsonify({'error': str(e)}), 500


# XTicket 좌석 조회
@bp.route('/xticket/sites', methods=['POST'])
@require_auth
def get_xticket_sites():
    """XTicket 특정 날짜의 좌석 정보 조회"""
    data = request.json
    target_date = data.get('target_date')  # YYYY-MM-DD 형식
    product_group_code = data.get('product_group_code', '0004')

    if not target_date:
        return jsonify({'error': 'target_date is required'}), 400

    try:
        from app.scrapers.xticket_scraper import XTicketScraper
        import os

        scraper = XTicketScraper(
            shop_encode=os.getenv('XTICKET_SHOP_ENCODE'),
            shop_code=os.getenv('XTICKET_SHOP_CODE'),
            user_id=os.getenv('XTICKET_USER_ID'),
            password=os.getenv('XTICKET_PASSWORD')
        )

        # 로그인
        if not scraper.login():
            return jsonify({'error': 'Login failed'}), 500

        # 좌석 정보 조회
        sites = scraper.get_available_sites(
            target_date=target_date,
            product_group_code=product_group_code
        )

        return jsonify({
            'success': True,
            'target_date': target_date,
            'total_sites': len(sites),
            'sites': sites
        }), 200

    except Exception as e:
        logger.error(f"Failed to get XTicket sites: {e}")
        return jsonify({'error': str(e)}), 500


# 통계
@bp.route('/statistics', methods=['GET'])
@require_auth
def get_statistics():
    """통계 조회"""
    stats = {
        'total_sites': CampingSite.query.count(),
        'active_monitoring': MonitoringTarget.query.filter_by(is_active=True).count(),
        'total_reservations': Reservation.query.count(),
        'successful_reservations': Reservation.query.filter_by(status='reserved').count(),
        'failed_reservations': Reservation.query.filter_by(status='failed').count()
    }

    return jsonify(stats), 200
