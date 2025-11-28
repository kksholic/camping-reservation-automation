"""API 라우트"""
from flask import Blueprint, jsonify, request, session
from loguru import logger
from datetime import datetime, timedelta, timezone

from app.models.database import CampingSite, CampingSiteAccount, CampingSiteSeat, Reservation, MonitoringTarget, UserInfo, AppSettings, ReservationSchedule
from app.services.monitor_service import MonitorService
from app.services.reservation_service import ReservationService
from app.services.multi_account_reservation_service import MultiAccountReservationService
from app.services.scheduler_service import scheduler_service
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


@bp.route('/server-time', methods=['GET'])
@require_auth
def get_simple_server_time():
    """간단한 서버 시간 조회 (AutoReservation용)"""
    now = datetime.now()
    return jsonify({
        'server_time': now.isoformat(),
        'timestamp': now.timestamp() * 1000  # 밀리초
    }), 200


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


@bp.route('/camping-sites/<int:site_id>/server-time', methods=['GET'])
@require_auth
def get_camping_site_server_time(site_id):
    """캠핑장 서버 시간 조회 및 offset 계산"""
    try:
        site = CampingSite.query.get_or_404(site_id)

        # URL에서 shop_encode 파싱
        from urllib.parse import urlparse, parse_qs
        from app.scrapers.xticket_scraper import XTicketScraper

        parsed_url = urlparse(site.url)
        query_params = parse_qs(parsed_url.query)

        shop_encode = query_params.get('shopEncode', [None])[0]

        if not shop_encode:
            logger.error(f"Missing shopEncode in URL: {site.url}")
            return jsonify({'error': 'Invalid camping site URL format'}), 400

        # XTicket 스크래퍼 생성 (서버 시간 조회에는 shop_code가 필요 없지만 생성자에서 필수이므로 shop_encode를 재사용)
        scraper = XTicketScraper(shop_encode=shop_encode, shop_code=shop_encode)

        # 로컬 시간 기록 (before)
        local_time_before = datetime.now(timezone.utc)

        # 서버 시간 조회
        server_time = scraper.get_server_time()

        # 로컬 시간 기록 (after)
        local_time_after = datetime.now(timezone.utc)

        if not server_time:
            logger.warning(f"Failed to get server time for site {site.name}")
            return jsonify({'error': 'Failed to get server time'}), 500

        # RTT 보정된 로컬 시간 계산 (요청 전후 평균)
        rtt = (local_time_after - local_time_before).total_seconds()
        local_time_avg = local_time_before + timedelta(seconds=rtt / 2)

        # Offset 계산 (서버 시간 - 로컬 시간)
        offset_seconds = (server_time - local_time_avg).total_seconds()

        logger.info(f"Server time for {site.name}: {server_time}, offset: {offset_seconds:.3f}s, RTT: {rtt:.3f}s")

        return jsonify({
            'server_time': server_time.strftime('%Y-%m-%d %H:%M:%S'),
            'local_time': local_time_avg.strftime('%Y-%m-%d %H:%M:%S'),
            'offset_seconds': offset_seconds,
            'rtt_seconds': rtt
        }), 200

    except Exception as e:
        logger.error(f"Error getting camping site server time: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


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


@bp.route('/monitoring/server-time', methods=['GET'])
@require_auth
def get_server_time():
    """서버 시간 정보 조회"""
    try:
        now = datetime.now()
        return jsonify({
            'server_time': now.strftime('%Y-%m-%d %H:%M:%S'),
            'hour': now.hour,
            'minute': now.minute,
            'second': now.second
        }), 200
    except Exception as e:
        logger.error(f"Failed to get server time: {e}")
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
            zone_code=data.get('zone_code'),
            reservation_time=data.get('reservation_time'),
            server_time_offset=data.get('server_time_offset', 0)  # 서버 시간 오프셋 전달
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


# 앱 설정
@bp.route('/settings', methods=['GET'])
@require_auth
def get_settings():
    """앱 설정 조회"""
    try:
        settings = AppSettings.query.first()
        if not settings:
            # 설정이 없으면 빈 설정 생성
            settings = AppSettings()
            db.session.add(settings)
            db.session.commit()

        return jsonify(settings.to_dict()), 200
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/settings/telegram', methods=['PUT'])
@require_auth
def update_telegram_settings():
    """텔레그램 설정 업데이트"""
    try:
        data = request.json

        settings = AppSettings.query.first()
        if not settings:
            settings = AppSettings()
            db.session.add(settings)

        settings.telegram_bot_token = data.get('telegram_bot_token', '')
        settings.telegram_chat_id = data.get('telegram_chat_id', '')

        # xticket_dry_run 필드도 업데이트 (있으면)
        if 'xticket_dry_run' in data:
            settings.xticket_dry_run = data.get('xticket_dry_run', False)

        db.session.commit()

        logger.info(f"✅ Telegram settings updated")
        return jsonify({
            'success': True,
            'message': '텔레그램 설정이 저장되었습니다',
            'settings': settings.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update telegram settings: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/settings/telegram/test', methods=['POST'])
@require_auth
def test_telegram():
    """텔레그램 알림 테스트"""
    try:
        settings = AppSettings.query.first()
        if not settings or not settings.telegram_bot_token or not settings.telegram_chat_id:
            return jsonify({
                'success': False,
                'message': '텔레그램 설정이 없습니다'
            }), 400

        # 텔레그램 알림 테스트
        from app.notifications.telegram_notifier import TelegramNotifier
        notifier = TelegramNotifier(settings.telegram_bot_token, settings.telegram_chat_id)

        success = notifier.send_message(
            "🔔 테스트 알림\n\n"
            "텔레그램 알림이 정상적으로 작동합니다!"
        )

        if success:
            return jsonify({
                'success': True,
                'message': '테스트 알림이 전송되었습니다'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '알림 전송에 실패했습니다'
            }), 500

    except Exception as e:
        logger.error(f"Failed to test telegram: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/camping-sites/<int:site_id>/available-sites', methods=['POST'])
@require_auth
@limiter.limit("30 per minute")
def get_available_sites(site_id):
    """캠핑장 사용 가능한 좌석 목록 조회"""
    try:
        site = CampingSite.query.get_or_404(site_id)
        data = request.json

        target_date = data.get('target_date')  # YYYY-MM-DD
        product_group_code = data.get('product_group_code', '0004')  # 기본값: 파쇄석사이트

        if not target_date:
            return jsonify({'error': 'target_date is required'}), 400

        # URL에서 shop_encode 파싱
        from urllib.parse import urlparse, parse_qs
        from app.scrapers.xticket_scraper import XTicketScraper

        parsed_url = urlparse(site.url)
        query_params = parse_qs(parsed_url.query)
        shop_encode = query_params.get('shopEncode', [None])[0]

        if not shop_encode:
            logger.error(f"Missing shopEncode in URL: {site.url}")
            return jsonify({'error': 'Invalid camping site URL format'}), 400

        # XTicket 스크래퍼 생성
        scraper = XTicketScraper(shop_encode=shop_encode, shop_code=shop_encode)

        # 사용 가능한 좌석 조회
        available_sites = scraper.get_available_sites(target_date, product_group_code)

        logger.info(f"Found {len(available_sites)} available sites for {site.name} on {target_date}")

        return jsonify({
            'target_date': target_date,
            'product_group_code': product_group_code,
            'available_sites': available_sites,
            'count': len(available_sites)
        }), 200

    except Exception as e:
        logger.error(f"Failed to get available sites: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/camping-sites/<int:site_id>/product-groups', methods=['POST'])
@require_auth
@limiter.limit("30 per minute")
def get_product_groups(site_id):
    """캠핑장 상품 그룹(구역) 목록 조회"""
    try:
        site = CampingSite.query.get_or_404(site_id)
        data = request.json

        start_date = data.get('start_date')  # YYYYMMDD
        end_date = data.get('end_date')  # YYYYMMDD

        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400

        # URL에서 shop_encode 파싱
        from urllib.parse import urlparse, parse_qs
        from app.scrapers.xticket_scraper import XTicketScraper

        parsed_url = urlparse(site.url)
        query_params = parse_qs(parsed_url.query)
        shop_encode = query_params.get('shopEncode', [None])[0]

        if not shop_encode:
            logger.error(f"Missing shopEncode in URL: {site.url}")
            return jsonify({'error': 'Invalid camping site URL format'}), 400

        # XTicket 스크래퍼 생성
        scraper = XTicketScraper(shop_encode=shop_encode, shop_code=shop_encode)

        # 상품 그룹 조회
        product_groups = scraper.get_product_groups(start_date, end_date)

        logger.info(f"Found {len(product_groups)} product groups for {site.name}")

        return jsonify({
            'start_date': start_date,
            'end_date': end_date,
            'product_groups': product_groups,
            'count': len(product_groups)
        }), 200

    except Exception as e:
        logger.error(f"Failed to get product groups: {e}")
        return jsonify({'error': str(e)}), 500


# ========================================
# 좌석 관리
# ========================================

@bp.route('/camping-sites/<int:site_id>/seats', methods=['GET'])
@require_auth
@limiter.limit("60 per minute")
def get_camping_site_seats(site_id):
    """
    캠핑장의 전체 좌석 목록 조회 (카테고리별 분류)

    Query Parameters:
        - category: 좌석 카테고리 필터 (grass, deck, crushed_stone)

    Returns:
        {
            'seats': [
                {
                    'id': 1,
                    'product_code': '00040009',
                    'product_group_code': '0004',
                    'seat_name': '금관-09',
                    'seat_category': 'crushed_stone',
                    'display_order': 209
                },
                ...
            ],
            'count': 60,
            'categories': {
                'grass': 20,
                'deck': 15,
                'crushed_stone': 25
            }
        }
    """
    try:
        site = CampingSite.query.get_or_404(site_id)
        logger.info(f"Fetching seats for camping site: {site.name} (ID: {site_id})")

        # 카테고리 필터
        category = request.args.get('category')

        # 쿼리 생성
        query = CampingSiteSeat.query.filter_by(camping_site_id=site_id).order_by(CampingSiteSeat.display_order)

        if category:
            query = query.filter_by(seat_category=category)

        seats = query.all()

        # 카테고리별 개수 계산
        grass_count = CampingSiteSeat.query.filter_by(
            camping_site_id=site_id,
            seat_category='grass'
        ).count()
        deck_count = CampingSiteSeat.query.filter_by(
            camping_site_id=site_id,
            seat_category='deck'
        ).count()
        crushed_stone_count = CampingSiteSeat.query.filter_by(
            camping_site_id=site_id,
            seat_category='crushed_stone'
        ).count()

        return jsonify({
            'seats': [seat.to_dict() for seat in seats],
            'count': len(seats),
            'categories': {
                'grass': grass_count,
                'deck': deck_count,
                'crushed_stone': crushed_stone_count,
                'total': grass_count + deck_count + crushed_stone_count
            }
        }), 200

    except Exception as e:
        logger.error(f"Failed to get camping site seats: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/camping-sites/<int:site_id>/seats/by-category', methods=['GET'])
@require_auth
@limiter.limit("60 per minute")
def get_seats_by_category(site_id):
    """
    카테고리별로 그룹화된 좌석 목록 조회

    Returns:
        {
            'grass': [
                {'id': 1, 'seat_name': '금관-01', 'product_code': '00010001', ...},
                ...
            ],
            'deck': [...],
            'crushed_stone': [...]
        }
    """
    try:
        site = CampingSite.query.get_or_404(site_id)
        logger.info(f"Fetching seats by category for: {site.name} (ID: {site_id})")

        # 카테고리별 좌석 조회 (한글 카테고리명 사용)
        grass_seats = CampingSiteSeat.query.filter_by(
            camping_site_id=site_id,
            seat_category='잔디사이트'
        ).order_by(CampingSiteSeat.display_order).all()

        deck_seats = CampingSiteSeat.query.filter_by(
            camping_site_id=site_id,
            seat_category='데크사이트'
        ).order_by(CampingSiteSeat.display_order).all()

        crushed_stone_seats = CampingSiteSeat.query.filter_by(
            camping_site_id=site_id,
            seat_category='파쇄석사이트'
        ).order_by(CampingSiteSeat.display_order).all()

        return jsonify({
            'grass': [seat.to_dict() for seat in grass_seats],
            'deck': [seat.to_dict() for seat in deck_seats],
            'crushed_stone': [seat.to_dict() for seat in crushed_stone_seats],
            'total_count': len(grass_seats) + len(deck_seats) + len(crushed_stone_seats)
        }), 200

    except Exception as e:
        logger.error(f"Failed to get seats by category: {e}")
        return jsonify({'error': str(e)}), 500


# =====================================================
# 스케줄 예약 관리
# =====================================================

@bp.route('/schedules', methods=['GET'])
@require_auth
def get_reservation_schedules():
    """예약 스케줄 목록 조회"""
    try:
        schedules = ReservationSchedule.query.order_by(ReservationSchedule.execute_at.desc()).all()
        return jsonify({
            'schedules': [s.to_dict() for s in schedules],
            'count': len(schedules)
        }), 200
    except Exception as e:
        logger.error(f"Failed to get schedules: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/schedules', methods=['POST'])
@require_auth
def create_reservation_schedule():
    """
    예약 스케줄 생성 (고도화 버전)

    지원 기능:
    - 다중 좌석 우선순위 (seat_ids)
    - Wave Attack 간격 설정
    - Burst Retry 설정
    - Pre-fire 시간 설정
    - Session Warmup 시간 설정
    """
    try:
        data = request.json
        logger.info(f"Creating schedule: {data}")

        # 필수 필드 검증
        if not data.get('camping_site_id'):
            return jsonify({'error': '캠핑장을 선택해주세요'}), 400
        if not data.get('execute_at'):
            return jsonify({'error': '실행 시간을 입력해주세요'}), 400
        if not data.get('target_date'):
            return jsonify({'error': '예약 날짜를 입력해주세요'}), 400

        # 실행 시간 파싱
        execute_at = datetime.fromisoformat(data['execute_at'].replace('Z', '+00:00'))
        if execute_at.tzinfo:
            execute_at = execute_at.replace(tzinfo=None)

        # 타겟 날짜 파싱
        target_date = datetime.strptime(data['target_date'], '%Y-%m-%d').date()

        # 좌석 처리: seat_ids (다중) 또는 seat_id (단일) 지원
        seat_ids = data.get('seat_ids')
        seat_id = data.get('seat_id')

        # 단일 좌석이 주어진 경우 배열로 변환
        if seat_id and not seat_ids:
            seat_ids = [seat_id]

        # 고급 설정 기본값
        wave_interval_ms = data.get('wave_interval_ms', 50)
        burst_retry_count = data.get('burst_retry_count', 3)
        pre_fire_ms = data.get('pre_fire_ms', 0)
        session_warmup_minutes = data.get('session_warmup_minutes', 5)
        dry_run = data.get('dry_run', False)  # DRY_RUN 모드 (기본: False)

        # 스케줄 생성
        schedule = ReservationSchedule(
            camping_site_id=data['camping_site_id'],
            execute_at=execute_at,
            target_date=target_date,
            seat_ids=seat_ids,
            seat_id=seat_id,  # 하위 호환성
            account_ids=data.get('account_ids'),
            retry_count=data.get('retry_count', 3),
            retry_interval=data.get('retry_interval', 30),
            wave_interval_ms=wave_interval_ms,
            burst_retry_count=burst_retry_count,
            pre_fire_ms=pre_fire_ms,
            session_warmup_minutes=session_warmup_minutes,
            dry_run=dry_run,
            status='pending'
        )

        db.session.add(schedule)
        db.session.flush()  # ID 생성

        # APScheduler에 작업 등록 (워밍업 포함)
        job_id, warmup_job_id = scheduler_service.add_reservation_job(
            schedule.id,
            execute_at,
            warmup_minutes=session_warmup_minutes
        )
        schedule.job_id = job_id
        schedule.warmup_job_id = warmup_job_id

        db.session.commit()

        logger.info(f"Created schedule #{schedule.id}")
        logger.info(f"  job_id: {job_id}, warmup_job_id: {warmup_job_id}")
        logger.info(f"  execute_at: {execute_at}")
        logger.info(f"  seat_ids: {seat_ids}")
        logger.info(f"  wave_interval: {wave_interval_ms}ms, burst_retry: {burst_retry_count}")
        logger.info(f"  pre_fire: {pre_fire_ms}ms, warmup: {session_warmup_minutes}min")

        return jsonify({
            'success': True,
            'message': '스케줄이 등록되었습니다',
            'schedule': schedule.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to create schedule: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500


@bp.route('/schedules/<int:schedule_id>', methods=['GET'])
@require_auth
def get_reservation_schedule(schedule_id):
    """예약 스케줄 상세 조회"""
    try:
        schedule = ReservationSchedule.query.get_or_404(schedule_id)
        return jsonify(schedule.to_dict()), 200
    except Exception as e:
        logger.error(f"Failed to get schedule: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/schedules/<int:schedule_id>', methods=['DELETE'])
@require_auth
def delete_reservation_schedule(schedule_id):
    """예약 스케줄 삭제"""
    try:
        schedule = ReservationSchedule.query.get_or_404(schedule_id)

        # APScheduler에서 메인 작업 제거
        if schedule.job_id:
            scheduler_service.remove_job(schedule.job_id)

        # APScheduler에서 워밍업 작업도 제거
        if schedule.warmup_job_id:
            scheduler_service.remove_job(schedule.warmup_job_id)

        # 세션 워밍업 정리
        from app.services.session_warmup_service import session_warmup_service
        session_warmup_service.stop_warmup(schedule_id)

        db.session.delete(schedule)
        db.session.commit()

        logger.info(f"Deleted schedule #{schedule_id} with warmup cleanup")

        return jsonify({
            'success': True,
            'message': '스케줄이 삭제되었습니다'
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete schedule: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/schedules/<int:schedule_id>/toggle', methods=['POST'])
@require_auth
def toggle_reservation_schedule(schedule_id):
    """예약 스케줄 활성화/비활성화"""
    try:
        schedule = ReservationSchedule.query.get_or_404(schedule_id)

        if schedule.status == 'pending':
            # 비활성화
            schedule.status = 'paused'
            if schedule.job_id:
                scheduler_service.pause_job(schedule.job_id)
            message = '스케줄이 일시 중지되었습니다'
        elif schedule.status == 'paused':
            # 활성화
            schedule.status = 'pending'
            if schedule.job_id:
                scheduler_service.resume_job(schedule.job_id)
            message = '스케줄이 재개되었습니다'
        else:
            return jsonify({'error': f'현재 상태({schedule.status})에서는 토글할 수 없습니다'}), 400

        db.session.commit()

        return jsonify({
            'success': True,
            'message': message,
            'schedule': schedule.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to toggle schedule: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/schedules/<int:schedule_id>/cancel', methods=['POST'])
@require_auth
def cancel_reservation_schedule(schedule_id):
    """예약 스케줄 취소"""
    try:
        schedule = ReservationSchedule.query.get_or_404(schedule_id)

        if schedule.status in ['completed', 'cancelled']:
            return jsonify({'error': '이미 완료되었거나 취소된 스케줄입니다'}), 400

        # APScheduler에서 메인 작업 제거
        if schedule.job_id:
            scheduler_service.remove_job(schedule.job_id)

        # APScheduler에서 워밍업 작업도 제거
        if schedule.warmup_job_id:
            scheduler_service.remove_job(schedule.warmup_job_id)

        # 세션 워밍업 정리
        from app.services.session_warmup_service import session_warmup_service
        session_warmup_service.stop_warmup(schedule_id)

        schedule.status = 'cancelled'
        db.session.commit()

        logger.info(f"Cancelled schedule #{schedule_id} with warmup cleanup")

        return jsonify({
            'success': True,
            'message': '스케줄이 취소되었습니다',
            'schedule': schedule.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to cancel schedule: {e}")
        return jsonify({'error': str(e)}), 500


# =====================================================
# 텔레그램 봇 대화자 목록
# =====================================================

@bp.route('/settings/telegram/chats', methods=['GET'])
@require_auth
def get_telegram_chats():
    """텔레그램 봇에 대화한 사용자/채팅방 목록 조회"""
    try:
        settings = AppSettings.query.first()
        if not settings or not settings.telegram_bot_token:
            return jsonify({
                'success': False,
                'message': '텔레그램 봇 토큰이 설정되지 않았습니다',
                'chats': []
            }), 400

        import requests

        # getUpdates API로 최근 대화 목록 가져오기
        bot_token = settings.telegram_bot_token
        url = f"https://api.telegram.org/bot{bot_token}/getUpdates"

        response = requests.get(url, timeout=10)
        data = response.json()

        if not data.get('ok'):
            return jsonify({
                'success': False,
                'message': f"텔레그램 API 오류: {data.get('description', 'Unknown error')}",
                'chats': []
            }), 400

        # 고유한 채팅방/사용자 추출
        chats_dict = {}
        for update in data.get('result', []):
            message = update.get('message') or update.get('edited_message') or update.get('channel_post')
            if message:
                chat = message.get('chat', {})
                chat_id = chat.get('id')
                if chat_id and chat_id not in chats_dict:
                    chat_type = chat.get('type', 'unknown')

                    # 채팅 이름 결정
                    if chat_type == 'private':
                        name = f"{chat.get('first_name', '')} {chat.get('last_name', '')}".strip()
                        username = chat.get('username', '')
                    elif chat_type in ['group', 'supergroup']:
                        name = chat.get('title', 'Unknown Group')
                        username = ''
                    elif chat_type == 'channel':
                        name = chat.get('title', 'Unknown Channel')
                        username = chat.get('username', '')
                    else:
                        name = 'Unknown'
                        username = ''

                    chats_dict[chat_id] = {
                        'chat_id': str(chat_id),
                        'type': chat_type,
                        'name': name or f"User {chat_id}",
                        'username': username,
                        'is_current': str(chat_id) == settings.telegram_chat_id
                    }

        # 리스트로 변환 (현재 선택된 것 먼저)
        chats_list = sorted(
            chats_dict.values(),
            key=lambda x: (not x['is_current'], x['name'].lower())
        )

        return jsonify({
            'success': True,
            'chats': chats_list,
            'count': len(chats_list),
            'current_chat_id': settings.telegram_chat_id
        }), 200

    except requests.Timeout:
        logger.error("Telegram API timeout")
        return jsonify({
            'success': False,
            'message': '텔레그램 API 응답 시간 초과',
            'chats': []
        }), 500
    except Exception as e:
        logger.error(f"Failed to get telegram chats: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'chats': []
        }), 500
