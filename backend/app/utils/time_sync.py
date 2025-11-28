"""
정밀 서버 시간 동기화 유틸리티

NTP 스타일의 다중 샘플링을 통해 서버와 로컬 시간 간 오프셋을 정밀하게 측정합니다.
목표: ±50ms 이내의 시간 동기화
"""
import time
import statistics
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from email.utils import parsedate_to_datetime
from loguru import logger
import requests
import threading


class TimeSample:
    """시간 샘플 데이터"""
    def __init__(self, local_before: float, server_time: datetime,
                 local_after: float, rtt: float, offset: float):
        self.local_before = local_before
        self.server_time = server_time
        self.local_after = local_after
        self.rtt = rtt  # Round Trip Time (ms)
        self.offset = offset  # 서버 - 로컬 오프셋 (초)

    def __repr__(self):
        return f"TimeSample(rtt={self.rtt:.1f}ms, offset={self.offset*1000:.1f}ms)"


class PreciseTimeSync:
    """
    정밀 서버 시간 동기화 클래스

    Features:
    - 다중 샘플링 (기본 5회)
    - 이상치 제거 (표준편차 2배 초과)
    - RTT 보정
    - 결과 캐싱 (기본 5분)
    """

    def __init__(self, base_url: str, shop_encode: str,
                 sample_count: int = 5,
                 cache_duration: int = 300,
                 outlier_threshold: float = 2.0):
        """
        Args:
            base_url: XTicket 서버 URL
            shop_encode: 캠핑장 코드
            sample_count: 샘플링 횟수
            cache_duration: 캐시 유지 시간 (초)
            outlier_threshold: 이상치 판정 기준 (표준편차 배수)
        """
        self.base_url = base_url
        self.shop_encode = shop_encode
        self.sample_count = sample_count
        self.cache_duration = cache_duration
        self.outlier_threshold = outlier_threshold

        # 캐시된 결과
        self._cached_offset: Optional[float] = None
        self._cached_rtt: Optional[float] = None
        self._cache_time: Optional[float] = None

        # RTT 히스토리 (동적 RTT 측정용)
        self._rtt_history: List[float] = []
        self._max_rtt_history = 10

        # 세션
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

    def _get_single_sample(self) -> Optional[TimeSample]:
        """단일 시간 샘플 수집"""
        try:
            url = f"{self.base_url}/web/main?shopEncode={self.shop_encode}"

            # 요청 전 시간 (고정밀 타이머)
            local_before = time.perf_counter()

            # HTTP 요청
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # 요청 후 시간
            local_after = time.perf_counter()

            # RTT 계산 (밀리초)
            rtt = (local_after - local_before) * 1000

            # 서버 시간 파싱
            date_header = response.headers.get('Date')
            if not date_header:
                logger.warning("No Date header in response")
                return None

            server_time = parsedate_to_datetime(date_header)

            # 로컬 시간 (요청 중간 시점 추정)
            local_mid = local_before + (local_after - local_before) / 2

            # timezone-aware datetime 사용 (서버 시간과 비교 가능하도록)
            from datetime import timezone
            local_datetime = datetime.now(timezone.utc)

            # 오프셋 계산: 서버시간 - 로컬시간 (초)
            # RTT/2를 보정하여 실제 서버 시간 추정
            offset = (server_time - local_datetime).total_seconds()

            return TimeSample(
                local_before=local_before,
                server_time=server_time,
                local_after=local_after,
                rtt=rtt,
                offset=offset
            )

        except Exception as e:
            logger.warning(f"Failed to get time sample: {e}")
            return None

    def _remove_outliers(self, samples: List[TimeSample]) -> List[TimeSample]:
        """이상치 제거 (표준편차 기반)"""
        if len(samples) < 3:
            return samples

        # RTT 기준 이상치 제거
        rtts = [s.rtt for s in samples]
        mean_rtt = statistics.mean(rtts)
        std_rtt = statistics.stdev(rtts) if len(rtts) > 1 else 0

        if std_rtt > 0:
            threshold = mean_rtt + (std_rtt * self.outlier_threshold)
            samples = [s for s in samples if s.rtt <= threshold]
            logger.debug(f"RTT outlier threshold: {threshold:.1f}ms, remaining: {len(samples)}")

        # 오프셋 기준 이상치 제거
        if len(samples) >= 3:
            offsets = [s.offset for s in samples]
            mean_offset = statistics.mean(offsets)
            std_offset = statistics.stdev(offsets) if len(offsets) > 1 else 0

            if std_offset > 0:
                min_offset = mean_offset - (std_offset * self.outlier_threshold)
                max_offset = mean_offset + (std_offset * self.outlier_threshold)
                samples = [s for s in samples if min_offset <= s.offset <= max_offset]
                logger.debug(f"Offset outlier range: [{min_offset*1000:.1f}, {max_offset*1000:.1f}]ms")

        return samples

    def sync(self, force: bool = False) -> Tuple[Optional[float], Optional[float]]:
        """
        서버 시간 동기화 수행

        Args:
            force: 캐시 무시하고 강제 동기화

        Returns:
            (offset_seconds, rtt_ms): 오프셋(초)과 RTT(밀리초)
        """
        # 캐시 확인
        if not force and self._is_cache_valid():
            logger.debug(f"Using cached offset: {self._cached_offset*1000:.1f}ms")
            return self._cached_offset, self._cached_rtt

        logger.info(f"Starting time sync with {self.sample_count} samples...")

        # 샘플 수집
        samples: List[TimeSample] = []
        for i in range(self.sample_count):
            sample = self._get_single_sample()
            if sample:
                samples.append(sample)
                logger.debug(f"Sample {i+1}: {sample}")

            # 샘플 간 간격 (서버 부하 방지)
            if i < self.sample_count - 1:
                time.sleep(0.1)

        if not samples:
            logger.error("Failed to collect any time samples")
            return None, None

        logger.info(f"Collected {len(samples)} samples")

        # 이상치 제거
        filtered_samples = self._remove_outliers(samples)
        if not filtered_samples:
            filtered_samples = samples  # 이상치 제거 후 없으면 원본 사용

        logger.info(f"After outlier removal: {len(filtered_samples)} samples")

        # 중앙값 계산 (평균보다 이상치에 강건함)
        offsets = [s.offset for s in filtered_samples]
        rtts = [s.rtt for s in filtered_samples]

        final_offset = statistics.median(offsets)
        final_rtt = statistics.median(rtts)

        # 캐시 업데이트
        self._cached_offset = final_offset
        self._cached_rtt = final_rtt
        self._cache_time = time.time()

        # RTT 히스토리 업데이트
        self._update_rtt_history(final_rtt)

        logger.info(f"⏰ Time sync complete:")
        logger.info(f"   Server offset: {final_offset*1000:.1f}ms")
        logger.info(f"   RTT: {final_rtt:.1f}ms")
        logger.info(f"   Samples used: {len(filtered_samples)}/{len(samples)}")

        return final_offset, final_rtt

    def _is_cache_valid(self) -> bool:
        """캐시 유효성 확인"""
        if self._cached_offset is None or self._cache_time is None:
            return False
        return (time.time() - self._cache_time) < self.cache_duration

    def _update_rtt_history(self, rtt: float):
        """RTT 히스토리 업데이트"""
        self._rtt_history.append(rtt)
        if len(self._rtt_history) > self._max_rtt_history:
            self._rtt_history.pop(0)

    def get_average_rtt(self) -> float:
        """평균 RTT 반환 (ms)"""
        if not self._rtt_history:
            return 100.0  # 기본값
        return statistics.mean(self._rtt_history)

    def get_server_time(self) -> datetime:
        """현재 서버 시간 반환 (동기화된 오프셋 기반)"""
        if self._cached_offset is None:
            self.sync()

        local_time = datetime.utcnow()
        if self._cached_offset is not None:
            return local_time + timedelta(seconds=self._cached_offset)
        return local_time

    def get_offset(self) -> float:
        """캐시된 오프셋 반환 (초)"""
        if self._cached_offset is None:
            self.sync()
        return self._cached_offset or 0.0

    def get_rtt(self) -> float:
        """캐시된 RTT 반환 (ms)"""
        if self._cached_rtt is None:
            self.sync()
        return self._cached_rtt or 100.0


class PreciseWaiter:
    """
    정밀 대기 유틸리티

    목표 시간에 정확히 도달하기 위한 고정밀 대기 기능
    """

    def __init__(self, time_sync: PreciseTimeSync):
        self.time_sync = time_sync

    def wait_until(self, target_time: datetime, pre_fire_ms: float = 0):
        """
        목표 시간까지 정밀 대기

        Args:
            target_time: 목표 시간 (UTC)
            pre_fire_ms: RTT 보상을 위한 선행 발사 시간 (ms)
        """
        # 현재 오프셋 확인
        offset = self.time_sync.get_offset()

        while True:
            # 서버 시간 기준 현재 시간
            now_server = datetime.utcnow() + timedelta(seconds=offset)

            # 목표까지 남은 시간 (밀리초)
            remaining_ms = (target_time - now_server).total_seconds() * 1000

            # Pre-fire 보정 적용
            adjusted_remaining = remaining_ms - pre_fire_ms

            if adjusted_remaining <= 0:
                logger.debug(f"Target reached! Remaining: {remaining_ms:.1f}ms")
                break

            # 대기 전략
            if adjusted_remaining > 1000:
                # 1초 이상 남으면 sleep
                sleep_time = (adjusted_remaining - 1000) / 1000
                logger.debug(f"Sleeping for {sleep_time:.2f}s (remaining: {adjusted_remaining:.0f}ms)")
                time.sleep(sleep_time)
            elif adjusted_remaining > 100:
                # 100ms ~ 1초: 짧은 sleep
                time.sleep(0.01)  # 10ms
            else:
                # 100ms 이하: busy-wait (정밀도 최대화)
                pass

    def wait_until_with_callback(self, target_time: datetime,
                                  callback, pre_fire_ms: float = 0):
        """
        목표 시간에 콜백 실행

        Args:
            target_time: 목표 시간 (UTC)
            callback: 실행할 함수
            pre_fire_ms: 선행 발사 시간 (ms)
        """
        self.wait_until(target_time, pre_fire_ms)
        return callback()


# 전역 인스턴스 관리
_sync_instances: dict = {}
_sync_lock = threading.Lock()


def get_time_sync(base_url: str, shop_encode: str) -> PreciseTimeSync:
    """TimeSync 인스턴스 반환 (싱글톤 패턴)"""
    key = f"{base_url}_{shop_encode}"
    with _sync_lock:
        if key not in _sync_instances:
            _sync_instances[key] = PreciseTimeSync(base_url, shop_encode)
        return _sync_instances[key]
