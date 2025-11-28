import React, { useState, useEffect, useRef } from 'react'
import {
  Box, Typography, Tabs, Tab, Paper, Button, TextField, MenuItem,
  Alert, CircularProgress, Chip, Card, CardContent, IconButton,
  List, ListItem, ListItemText, ListItemSecondaryAction, Switch,
  Dialog, DialogTitle, DialogContent, DialogActions, Divider,
  LinearProgress, FormControlLabel, Checkbox, Tooltip, Badge,
  Accordion, AccordionSummary, AccordionDetails, Slider
} from '@mui/material'
import {
  PlayArrow, Stop, Schedule, Refresh, Delete, Add,
  AccessTime, CalendarMonth, CheckCircle, Error, Pending,
  Speed, Timer, Search, ExpandMore, Settings, EventSeat
} from '@mui/icons-material'
import SeatSelectionDialog from '../components/SeatSelectionDialog'
import {
  getCampingSites, getCampingSiteAccounts, getSeatsByCategory,
  createMultiAccountReservation, getServerTime,
  getReservationSchedules, createReservationSchedule,
  deleteReservationSchedule, toggleReservationSchedule, cancelReservationSchedule
} from '../services/api'

// =====================================================
// Tab 1: 즉시 예약 (Quick Reserve)
// =====================================================
function QuickReserveTab({ sites, selectedSite, setSelectedSite }) {
  const [accounts, setAccounts] = useState([])
  const [seats, setSeats] = useState({ grass: [], deck: [], crushed_stone: [] })
  const [selectedAccounts, setSelectedAccounts] = useState([])
  const [selectedSeat, setSelectedSeat] = useState(null)
  const [selectedCategory, setSelectedCategory] = useState('')
  const [reservationDate, setReservationDate] = useState('')
  const [reservationTime, setReservationTime] = useState('')
  const [serverTimeOffset, setServerTimeOffset] = useState(0)
  const [currentServerTime, setCurrentServerTime] = useState(null)

  const [reserving, setReserving] = useState(false)
  const [results, setResults] = useState([])
  const [logs, setLogs] = useState([])
  const logRef = useRef(null)

  // 캠핑장 선택 시 계정/좌석 로드
  useEffect(() => {
    if (selectedSite) {
      loadSiteData(selectedSite.id)
    }
  }, [selectedSite])

  // 서버 시간 동기화
  useEffect(() => {
    syncServerTime()
    const interval = setInterval(syncServerTime, 30000)
    return () => clearInterval(interval)
  }, [])

  // 현재 서버 시간 표시 (1초마다 업데이트)
  useEffect(() => {
    const interval = setInterval(() => {
      if (serverTimeOffset !== 0) {
        const serverNow = new Date(Date.now() + serverTimeOffset)
        setCurrentServerTime(serverNow)
      }
    }, 100)
    return () => clearInterval(interval)
  }, [serverTimeOffset])

  const syncServerTime = async () => {
    try {
      const startTime = Date.now()
      const data = await getServerTime()
      const endTime = Date.now()
      const latency = (endTime - startTime) / 2

      const serverTime = new Date(data.server_time).getTime()
      const offset = serverTime - Date.now() + latency
      setServerTimeOffset(offset)
      addLog(`서버 시간 동기화 완료 (오프셋: ${offset.toFixed(0)}ms)`)
    } catch (err) {
      addLog(`서버 시간 동기화 실패: ${err.message}`, 'error')
    }
  }

  const loadSiteData = async (siteId) => {
    try {
      const [accountsData, seatsData] = await Promise.all([
        getCampingSiteAccounts(siteId),
        getSeatsByCategory(siteId)
      ])
      setAccounts(accountsData.accounts || [])
      setSeats(seatsData)
      setSelectedAccounts(accountsData.accounts?.map(a => a.id) || [])
      addLog(`${accountsData.accounts?.length || 0}개 계정, ${seatsData.total_count || 0}개 좌석 로드됨`)
    } catch (err) {
      addLog(`데이터 로드 실패: ${err.message}`, 'error')
    }
  }

  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toLocaleTimeString('ko-KR', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    })
    setLogs(prev => [...prev.slice(-100), { timestamp, message, type }])
    setTimeout(() => {
      if (logRef.current) {
        logRef.current.scrollTop = logRef.current.scrollHeight
      }
    }, 10)
  }

  const handleAccountToggle = (accountId) => {
    setSelectedAccounts(prev =>
      prev.includes(accountId)
        ? prev.filter(id => id !== accountId)
        : [...prev, accountId]
    )
  }

  const handleSelectAllAccounts = () => {
    if (selectedAccounts.length === accounts.length) {
      setSelectedAccounts([])
    } else {
      setSelectedAccounts(accounts.map(a => a.id))
    }
  }

  const handleStartReservation = async () => {
    if (!selectedSite || !reservationDate || selectedAccounts.length === 0) {
      addLog('캠핑장, 날짜, 계정을 모두 선택해주세요', 'error')
      return
    }

    setReserving(true)
    setResults([])
    addLog('========== 예약 시작 ==========')
    addLog(`캠핑장: ${selectedSite.name}`)
    addLog(`날짜: ${reservationDate}`)
    addLog(`좌석: ${selectedSeat?.seat_name || '미지정'}`)
    addLog(`사용 계정: ${selectedAccounts.length}개`)

    try {
      const result = await createMultiAccountReservation({
        camping_site_id: selectedSite.id,
        target_date: reservationDate,
        site_name: selectedSeat?.seat_name,
        zone_code: selectedSeat?.product_group_code,
        reservation_time: reservationTime || undefined,
        server_time_offset: serverTimeOffset,
        product_code: selectedSeat?.product_code,
        product_group_code: selectedSeat?.product_group_code,
        account_ids: selectedAccounts
      })

      setResults(result.results || [])

      if (result.success) {
        addLog(`예약 성공! 예약번호: ${result.reservation_number}`, 'success')
      } else {
        addLog(`예약 실패: ${result.message}`, 'error')
      }

      result.results?.forEach(r => {
        addLog(`[${r.account_name}] ${r.status}: ${r.message || ''}`, r.status === 'success' ? 'success' : 'error')
      })

    } catch (err) {
      addLog(`예약 오류: ${err.message}`, 'error')
    } finally {
      setReserving(false)
      addLog('========== 예약 종료 ==========')
    }
  }

  const categoryLabel = { grass: '잔디', deck: '데크', crushed_stone: '파쇄석' }
  const categoryColor = { grass: 'success', deck: 'warning', crushed_stone: 'default' }

  return (
    <Box sx={{ display: 'flex', gap: 2, height: 'calc(100vh - 250px)' }}>
      {/* 왼쪽: 설정 패널 */}
      <Paper sx={{ flex: 1, p: 2, overflow: 'auto' }}>
        <Typography variant="h6" gutterBottom>예약 설정</Typography>

        {/* 캠핑장 선택 */}
        <TextField
          select
          fullWidth
          label="캠핑장"
          value={selectedSite?.id || ''}
          onChange={(e) => setSelectedSite(sites.find(s => s.id === e.target.value))}
          sx={{ mb: 2 }}
        >
          {sites.map(site => (
            <MenuItem key={site.id} value={site.id}>{site.name}</MenuItem>
          ))}
        </TextField>

        {/* 날짜 */}
        <TextField
          fullWidth
          type="date"
          label="예약 날짜"
          value={reservationDate}
          onChange={(e) => setReservationDate(e.target.value)}
          InputLabelProps={{ shrink: true }}
          sx={{ mb: 2 }}
        />

        {/* 예약 시작 시간 (옵션) */}
        <TextField
          fullWidth
          type="time"
          label="예약 시작 시간 (선택)"
          value={reservationTime}
          onChange={(e) => setReservationTime(e.target.value)}
          InputLabelProps={{ shrink: true }}
          inputProps={{ step: 1 }}
          helperText="지정 시 해당 시간까지 대기 후 시작"
          sx={{ mb: 2 }}
        />

        <Divider sx={{ my: 2 }} />

        {/* 좌석 선택 */}
        <Typography variant="subtitle2" gutterBottom>좌석 선택</Typography>
        <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
          {Object.entries(categoryLabel).map(([key, label]) => (
            <Chip
              key={key}
              label={`${label} (${seats[key]?.length || 0})`}
              color={selectedCategory === key ? categoryColor[key] : 'default'}
              variant={selectedCategory === key ? 'filled' : 'outlined'}
              onClick={() => setSelectedCategory(key)}
              size="small"
            />
          ))}
        </Box>

        {selectedCategory && (
          <TextField
            select
            fullWidth
            label="좌석"
            value={selectedSeat?.id || ''}
            onChange={(e) => setSelectedSeat(seats[selectedCategory]?.find(s => s.id === e.target.value))}
            sx={{ mb: 2 }}
            size="small"
          >
            {seats[selectedCategory]?.map(seat => (
              <MenuItem key={seat.id} value={seat.id}>
                {seat.seat_name} ({seat.product_code})
              </MenuItem>
            ))}
          </TextField>
        )}

        {selectedSeat && (
          <Alert severity="info" sx={{ mb: 2 }}>
            <strong>{selectedSeat.seat_name}</strong> - {categoryLabel[selectedSeat.seat_category]}
            <br />코드: {selectedSeat.product_code}
          </Alert>
        )}

        <Divider sx={{ my: 2 }} />

        {/* 계정 선택 */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
          <Typography variant="subtitle2">사용 계정</Typography>
          <Button size="small" onClick={handleSelectAllAccounts}>
            {selectedAccounts.length === accounts.length ? '전체 해제' : '전체 선택'}
          </Button>
        </Box>

        <List dense sx={{ maxHeight: 200, overflow: 'auto', bgcolor: 'grey.50', borderRadius: 1 }}>
          {accounts.map(account => (
            <ListItem key={account.id} dense>
              <Checkbox
                checked={selectedAccounts.includes(account.id)}
                onChange={() => handleAccountToggle(account.id)}
                size="small"
              />
              <ListItemText
                primary={account.name || account.username}
                secondary={account.username}
              />
            </ListItem>
          ))}
        </List>

        <Divider sx={{ my: 2 }} />

        {/* 서버 시간 */}
        <Box sx={{ mb: 2, p: 1, bgcolor: 'grey.100', borderRadius: 1 }}>
          <Typography variant="caption" color="text.secondary">서버 시간</Typography>
          <Typography variant="h6" sx={{ fontFamily: 'monospace' }}>
            {currentServerTime ? currentServerTime.toLocaleTimeString('ko-KR', {
              hour12: false,
              hour: '2-digit',
              minute: '2-digit',
              second: '2-digit'
            }) + '.' + String(currentServerTime.getMilliseconds()).padStart(3, '0') : '--:--:--'}
          </Typography>
          <Button size="small" startIcon={<Refresh />} onClick={syncServerTime}>동기화</Button>
        </Box>

        {/* 실행 버튼 */}
        <Button
          variant="contained"
          fullWidth
          size="large"
          startIcon={reserving ? <CircularProgress size={20} color="inherit" /> : <PlayArrow />}
          onClick={handleStartReservation}
          disabled={reserving || !selectedSite || !reservationDate || selectedAccounts.length === 0}
          color={reserving ? 'warning' : 'primary'}
        >
          {reserving ? '예약 진행 중...' : '지금 예약 시작'}
        </Button>
      </Paper>

      {/* 오른쪽: 로그 패널 */}
      <Paper sx={{ flex: 1, p: 2, display: 'flex', flexDirection: 'column' }}>
        <Typography variant="h6" gutterBottom>실시간 로그</Typography>

        {/* 결과 요약 */}
        {results.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip
                icon={<CheckCircle />}
                label={`성공: ${results.filter(r => r.status === 'success').length}`}
                color="success"
                size="small"
              />
              <Chip
                icon={<Error />}
                label={`실패: ${results.filter(r => r.status !== 'success').length}`}
                color="error"
                size="small"
              />
            </Box>
          </Box>
        )}

        {/* 로그 뷰어 */}
        <Box
          ref={logRef}
          sx={{
            flex: 1,
            overflow: 'auto',
            bgcolor: '#1e1e1e',
            color: '#d4d4d4',
            p: 1,
            borderRadius: 1,
            fontFamily: 'monospace',
            fontSize: '12px',
            lineHeight: 1.5
          }}
        >
          {logs.map((log, idx) => (
            <Box key={idx} sx={{
              color: log.type === 'error' ? '#f44336' : log.type === 'success' ? '#4caf50' : '#d4d4d4'
            }}>
              <span style={{ color: '#888' }}>[{log.timestamp}]</span> {log.message}
            </Box>
          ))}
          {logs.length === 0 && (
            <Typography color="grey.500">로그가 여기에 표시됩니다...</Typography>
          )}
        </Box>
      </Paper>
    </Box>
  )
}

// =====================================================
// Tab 2: 스케줄 예약 (Scheduled Reserve)
// =====================================================
function ScheduledReserveTab({ sites }) {
  const [schedules, setSchedules] = useState([])
  const [loading, setLoading] = useState(true)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  // 선택된 캠핑장의 계정/좌석 정보
  const [accounts, setAccounts] = useState([])
  const [seats, setSeats] = useState({ grass: [], deck: [], crushed_stone: [] })
  const [selectedAccounts, setSelectedAccounts] = useState([])
  const [selectedSeats, setSelectedSeats] = useState([]) // 다중 좌석 (우선순위 순)
  const [seatDialogOpen, setSeatDialogOpen] = useState(false) // 좌석 선택 다이얼로그

  const [newSchedule, setNewSchedule] = useState({
    camping_site_id: '',
    execute_datetime: '',
    target_date: '',
    retry_count: 3,
    retry_interval: 30,
    // 고급 설정
    wave_interval_ms: 50,
    burst_retry_count: 3,
    pre_fire_ms: 0,
    session_warmup_minutes: 5,
    dry_run: false
  })

  // 고급 설정 펼침 상태
  const [advancedOpen, setAdvancedOpen] = useState(false)

  // 스케줄 목록 로드
  useEffect(() => {
    loadSchedules()
  }, [])

  // 캠핑장 선택 시 계정/좌석 로드
  useEffect(() => {
    if (newSchedule.camping_site_id) {
      loadSiteData(newSchedule.camping_site_id)
    }
  }, [newSchedule.camping_site_id])

  const loadSchedules = async () => {
    try {
      setLoading(true)
      const data = await getReservationSchedules()
      setSchedules(data.schedules || [])
    } catch (err) {
      console.error('Failed to load schedules:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadSiteData = async (siteId) => {
    try {
      const [accountsData, seatsData] = await Promise.all([
        getCampingSiteAccounts(siteId),
        getSeatsByCategory(siteId)
      ])
      // API가 배열을 직접 반환
      const accountsList = Array.isArray(accountsData) ? accountsData : (accountsData.accounts || [])
      setAccounts(accountsList)
      setSeats(seatsData)
      // 기본값: 모든 활성 계정 선택
      setSelectedAccounts(accountsList.filter(a => a.is_active).map(a => a.id) || [])
    } catch (err) {
      console.error('Failed to load site data:', err)
    }
  }

  const handleAddSchedule = async () => {
    if (submitting) return

    try {
      setSubmitting(true)

      const payload = {
        camping_site_id: newSchedule.camping_site_id,
        execute_at: newSchedule.execute_datetime,
        target_date: newSchedule.target_date,
        // 다중 좌석 지원 (seat_ids 배열)
        seat_ids: selectedSeats.length > 0 ? selectedSeats.map(s => s.id) : null,
        account_ids: selectedAccounts.length > 0 ? selectedAccounts : null,
        retry_count: newSchedule.retry_count,
        retry_interval: newSchedule.retry_interval,
        // 고급 설정
        wave_interval_ms: newSchedule.wave_interval_ms,
        burst_retry_count: newSchedule.burst_retry_count,
        pre_fire_ms: newSchedule.pre_fire_ms,
        session_warmup_minutes: newSchedule.session_warmup_minutes,
        dry_run: newSchedule.dry_run
      }

      await createReservationSchedule(payload)
      await loadSchedules()

      setDialogOpen(false)
      resetForm()
    } catch (err) {
      console.error('Failed to create schedule:', err)
      alert('스케줄 생성 실패: ' + (err.response?.data?.error || err.message))
    } finally {
      setSubmitting(false)
    }
  }

  const resetForm = () => {
    setNewSchedule({
      camping_site_id: '',
      execute_datetime: '',
      target_date: '',
      retry_count: 3,
      retry_interval: 30,
      wave_interval_ms: 50,
      burst_retry_count: 3,
      pre_fire_ms: 0,
      session_warmup_minutes: 5,
      dry_run: false
    })
    setSelectedAccounts([])
    setSelectedSeats([])
    setAdvancedOpen(false)
    setAccounts([])
    setSeats({ grass: [], deck: [], crushed_stone: [] })
  }

  const handleSeatsSelected = (seats) => {
    setSelectedSeats(seats)
  }

  const getCategoryLabel = (category) => {
    const labels = { grass: '잔디', deck: '데크', crushed_stone: '파쇄석' }
    return labels[category] || category
  }

  const getCategoryColor = (category) => {
    const colors = { grass: 'success', deck: 'warning', crushed_stone: 'info' }
    return colors[category] || 'default'
  }

  const handleDeleteSchedule = async (id) => {
    if (!window.confirm('이 스케줄을 삭제하시겠습니까?')) return

    try {
      await deleteReservationSchedule(id)
      await loadSchedules()
    } catch (err) {
      console.error('Failed to delete schedule:', err)
      alert('스케줄 삭제 실패: ' + (err.response?.data?.error || err.message))
    }
  }

  const handleToggleSchedule = async (id) => {
    try {
      await toggleReservationSchedule(id)
      await loadSchedules()
    } catch (err) {
      console.error('Failed to toggle schedule:', err)
      alert('스케줄 상태 변경 실패: ' + (err.response?.data?.error || err.message))
    }
  }

  const handleCancelSchedule = async (id) => {
    if (!window.confirm('이 스케줄을 취소하시겠습니까?')) return

    try {
      await cancelReservationSchedule(id)
      await loadSchedules()
    } catch (err) {
      console.error('Failed to cancel schedule:', err)
      alert('스케줄 취소 실패: ' + (err.response?.data?.error || err.message))
    }
  }

  const handleAccountToggle = (accountId) => {
    setSelectedAccounts(prev =>
      prev.includes(accountId)
        ? prev.filter(id => id !== accountId)
        : [...prev, accountId]
    )
  }

  const handleSelectAllAccounts = () => {
    if (selectedAccounts.length === accounts.length) {
      setSelectedAccounts([])
    } else {
      setSelectedAccounts(accounts.map(a => a.id))
    }
  }

  const getStatusColor = (status) => {
    switch(status) {
      case 'pending': return 'warning'
      case 'warming': return 'info'
      case 'running': return 'info'
      case 'completed': return 'success'
      case 'failed': return 'error'
      case 'cancelled': return 'default'
      default: return 'default'
    }
  }

  const getStatusLabel = (status) => {
    switch(status) {
      case 'pending': return '대기 중'
      case 'warming': return '세션 워밍업 중'
      case 'running': return '실행 중'
      case 'completed': return '완료'
      case 'failed': return '실패'
      case 'cancelled': return '취소됨'
      default: return status
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6">예약 스케줄</Typography>
          <IconButton onClick={loadSchedules} size="small">
            <Refresh />
          </IconButton>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)}>
          스케줄 추가
        </Button>
      </Box>

      <Alert severity="info" sx={{ mb: 2 }}>
        지정한 시간에 자동으로 예약이 시작됩니다. 오픈런 예약에 유용합니다.
      </Alert>

      {schedules.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Schedule sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
          <Typography color="text.secondary">등록된 스케줄이 없습니다</Typography>
          <Typography variant="body2" color="text.secondary">
            "스케줄 추가" 버튼을 눌러 예약 오픈 시간에 자동 시작되도록 설정하세요
          </Typography>
        </Paper>
      ) : (
        <List>
          {schedules.map(schedule => (
            <Paper key={schedule.id} sx={{ mb: 1 }}>
              <ListItem>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                      <Typography variant="subtitle1">{schedule.camping_site_name}</Typography>
                      <Chip label={getStatusLabel(schedule.status)} color={getStatusColor(schedule.status)} size="small" />
                      {/* 다중 좌석 표시 */}
                      {schedule.seats && schedule.seats.length > 0 && (
                        <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                          {schedule.seats.map((seat, idx) => (
                            <Chip
                              key={seat.id}
                              label={`${idx + 1}. ${seat.seat_name}`}
                              size="small"
                              variant="outlined"
                              color={idx === 0 ? 'primary' : 'default'}
                            />
                          ))}
                        </Box>
                      )}
                      {/* 하위 호환성: 단일 좌석 */}
                      {!schedule.seats?.length && schedule.seat_name && (
                        <Chip label={schedule.seat_name} size="small" variant="outlined" />
                      )}
                    </Box>
                  }
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2">
                        <AccessTime sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
                        실행: {new Date(schedule.execute_at).toLocaleString('ko-KR')}
                      </Typography>
                      <Typography variant="body2">
                        <CalendarMonth sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
                        타겟: {schedule.target_date}
                      </Typography>
                      {schedule.account_ids && (
                        <Typography variant="body2" color="text.secondary">
                          사용 계정: {schedule.account_ids.length}개
                        </Typography>
                      )}
                      {/* 고급 설정 표시 */}
                      <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
                        {schedule.session_warmup_minutes > 0 && (
                          <Chip label={`워밍업 ${schedule.session_warmup_minutes}분 전`} size="small" variant="outlined" />
                        )}
                        {schedule.wave_interval_ms && (
                          <Chip label={`Wave ${schedule.wave_interval_ms}ms`} size="small" variant="outlined" />
                        )}
                        {schedule.pre_fire_ms > 0 && (
                          <Chip label={`Pre-fire ${schedule.pre_fire_ms}ms`} size="small" variant="outlined" />
                        )}
                      </Box>
                      {schedule.result && (
                        <Alert
                          severity={schedule.result.success ? 'success' : 'error'}
                          sx={{ mt: 1, py: 0 }}
                        >
                          {schedule.result.message || schedule.result.first_success?.reservation_number
                            ? `예약 성공! 번호: ${schedule.result.first_success?.reservation_number}`
                            : (schedule.result.success ? '예약 성공!' : '예약 실패')}
                        </Alert>
                      )}
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  {(schedule.status === 'pending' || schedule.status === 'warming') && (
                    <Tooltip title="취소">
                      <IconButton onClick={() => handleCancelSchedule(schedule.id)} color="warning">
                        <Stop />
                      </IconButton>
                    </Tooltip>
                  )}
                  <Tooltip title="삭제">
                    <IconButton
                      onClick={() => handleDeleteSchedule(schedule.id)}
                      disabled={schedule.status === 'running' || schedule.status === 'warming'}
                    >
                      <Delete />
                    </IconButton>
                  </Tooltip>
                </ListItemSecondaryAction>
              </ListItem>
            </Paper>
          ))}
        </List>
      )}

      {/* 스케줄 추가 다이얼로그 */}
      <Dialog open={dialogOpen} onClose={() => !submitting && setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>예약 스케줄 추가</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            {/* 캠핑장 선택 */}
            <TextField
              select
              fullWidth
              label="캠핑장"
              value={newSchedule.camping_site_id}
              onChange={(e) => setNewSchedule(prev => ({ ...prev, camping_site_id: e.target.value }))}
            >
              {sites.map(site => (
                <MenuItem key={site.id} value={site.id}>{site.name}</MenuItem>
              ))}
            </TextField>

            {/* 실행 시간 / 타겟 날짜 */}
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                fullWidth
                type="datetime-local"
                label="실행 시간 (예약 오픈 시간)"
                value={newSchedule.execute_datetime}
                onChange={(e) => setNewSchedule(prev => ({ ...prev, execute_datetime: e.target.value }))}
                InputLabelProps={{ shrink: true }}
                helperText="이 시간에 자동으로 예약이 시작됩니다"
              />
              <TextField
                fullWidth
                type="date"
                label="예약할 날짜"
                value={newSchedule.target_date}
                onChange={(e) => setNewSchedule(prev => ({ ...prev, target_date: e.target.value }))}
                InputLabelProps={{ shrink: true }}
              />
            </Box>

            {/* 좌석 선택 (다중 우선순위) */}
            {newSchedule.camping_site_id && (
              <>
                <Divider />
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="subtitle2">
                    <EventSeat sx={{ fontSize: 16, mr: 0.5, verticalAlign: 'middle' }} />
                    우선순위 좌석 선택 (선택사항)
                  </Typography>
                  <Button
                    size="small"
                    variant="outlined"
                    startIcon={<Add />}
                    onClick={() => setSeatDialogOpen(true)}
                  >
                    좌석 선택
                  </Button>
                </Box>

                {selectedSeats.length > 0 ? (
                  <Box sx={{ mt: 1 }}>
                    <Alert severity="info" sx={{ mb: 1 }}>
                      선택된 좌석 {selectedSeats.length}개 (1순위부터 순차 시도)
                    </Alert>
                    <Box sx={{ display: 'flex', gap: 0.5, flexWrap: 'wrap' }}>
                      {selectedSeats.map((seat, idx) => (
                        <Chip
                          key={seat.id}
                          label={`${idx + 1}. ${seat.seat_name}`}
                          color={idx === 0 ? 'primary' : 'default'}
                          variant={idx === 0 ? 'filled' : 'outlined'}
                          size="small"
                          onDelete={() => setSelectedSeats(prev => prev.filter(s => s.id !== seat.id))}
                        />
                      ))}
                    </Box>
                  </Box>
                ) : (
                  <Alert severity="warning" sx={{ mt: 1 }}>
                    좌석을 선택하지 않으면 빈 자리 중 아무 곳이나 시도합니다.
                  </Alert>
                )}
              </>
            )}

            {/* 계정 선택 */}
            {newSchedule.camping_site_id && accounts.length > 0 && (
              <>
                <Divider />
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography variant="subtitle2">사용 계정 ({selectedAccounts.length}/{accounts.length})</Typography>
                  <Button size="small" onClick={handleSelectAllAccounts}>
                    {selectedAccounts.length === accounts.length ? '전체 해제' : '전체 선택'}
                  </Button>
                </Box>

                <List dense sx={{ maxHeight: 150, overflow: 'auto', bgcolor: 'grey.50', borderRadius: 1 }}>
                  {accounts.map(account => (
                    <ListItem key={account.id} dense>
                      <Checkbox
                        checked={selectedAccounts.includes(account.id)}
                        onChange={() => handleAccountToggle(account.id)}
                        size="small"
                      />
                      <ListItemText
                        primary={account.nickname || account.login_username}
                        secondary={account.booker_name}
                      />
                      {!account.is_active && (
                        <Chip label="비활성" size="small" color="default" />
                      )}
                    </ListItem>
                  ))}
                </List>
              </>
            )}

            <Divider />

            {/* 재시도 설정 */}
            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                fullWidth
                type="number"
                label="재시도 횟수"
                value={newSchedule.retry_count}
                onChange={(e) => setNewSchedule(prev => ({ ...prev, retry_count: parseInt(e.target.value) || 0 }))}
                inputProps={{ min: 0, max: 10 }}
              />
              <TextField
                fullWidth
                type="number"
                label="재시도 간격(초)"
                value={newSchedule.retry_interval}
                onChange={(e) => setNewSchedule(prev => ({ ...prev, retry_interval: parseInt(e.target.value) || 30 }))}
                inputProps={{ min: 5, max: 300 }}
              />
            </Box>

            {/* 고급 설정 (접이식) */}
            <Accordion expanded={advancedOpen} onChange={() => setAdvancedOpen(!advancedOpen)}>
              <AccordionSummary expandIcon={<ExpandMore />}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Settings fontSize="small" />
                  <Typography>고급 설정</Typography>
                  {advancedOpen && (
                    <Chip label="알고리즘 최적화" size="small" color="primary" variant="outlined" />
                  )}
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  {/* 세션 워밍업 */}
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      세션 워밍업 ({newSchedule.session_warmup_minutes}분 전)
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      예약 시작 전 미리 로그인하여 세션을 준비합니다.
                    </Typography>
                    <Slider
                      value={newSchedule.session_warmup_minutes}
                      onChange={(e, v) => setNewSchedule(prev => ({ ...prev, session_warmup_minutes: v }))}
                      min={1}
                      max={10}
                      marks={[
                        { value: 1, label: '1분' },
                        { value: 5, label: '5분' },
                        { value: 10, label: '10분' }
                      ]}
                      valueLabelDisplay="auto"
                    />
                  </Box>

                  <Divider />

                  {/* Wave Attack 간격 */}
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Wave Attack 간격 ({newSchedule.wave_interval_ms}ms)
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      여러 계정이 시차를 두고 예약을 시도합니다. 간격이 짧을수록 공격적입니다.
                    </Typography>
                    <Slider
                      value={newSchedule.wave_interval_ms}
                      onChange={(e, v) => setNewSchedule(prev => ({ ...prev, wave_interval_ms: v }))}
                      min={10}
                      max={200}
                      step={10}
                      marks={[
                        { value: 10, label: '10ms' },
                        { value: 50, label: '50ms' },
                        { value: 100, label: '100ms' },
                        { value: 200, label: '200ms' }
                      ]}
                      valueLabelDisplay="auto"
                    />
                  </Box>

                  <Divider />

                  {/* Burst Retry */}
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Burst Retry 횟수 ({newSchedule.burst_retry_count}회)
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      실패 시 밀리초 단위로 즉시 재시도합니다. (50ms → 100ms → 200ms)
                    </Typography>
                    <Slider
                      value={newSchedule.burst_retry_count}
                      onChange={(e, v) => setNewSchedule(prev => ({ ...prev, burst_retry_count: v }))}
                      min={0}
                      max={5}
                      marks={[
                        { value: 0, label: '0회' },
                        { value: 3, label: '3회' },
                        { value: 5, label: '5회' }
                      ]}
                      valueLabelDisplay="auto"
                    />
                  </Box>

                  <Divider />

                  {/* Pre-fire */}
                  <Box>
                    <Typography variant="subtitle2" gutterBottom>
                      Pre-fire 시간 ({newSchedule.pre_fire_ms}ms)
                    </Typography>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      네트워크 지연(RTT)을 보상하여 서버에 정시에 도착하도록 미리 전송합니다.
                    </Typography>
                    <Slider
                      value={newSchedule.pre_fire_ms}
                      onChange={(e, v) => setNewSchedule(prev => ({ ...prev, pre_fire_ms: v }))}
                      min={0}
                      max={500}
                      step={10}
                      marks={[
                        { value: 0, label: '0ms' },
                        { value: 100, label: '100ms' },
                        { value: 300, label: '300ms' },
                        { value: 500, label: '500ms' }
                      ]}
                      valueLabelDisplay="auto"
                    />
                  </Box>

                  {/* DRY_RUN 모드 */}
                  <Box>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={newSchedule.dry_run}
                          onChange={(e) => setNewSchedule({
                            ...newSchedule,
                            dry_run: e.target.checked
                          })}
                          color="warning"
                        />
                      }
                      label={
                        <Box>
                          <Typography variant="body2" fontWeight="bold">
                            테스트 모드 (DRY RUN)
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            활성화 시 실제 예약하지 않고 테스트만 진행합니다.
                          </Typography>
                        </Box>
                      }
                    />
                  </Box>

                  <Alert severity="info" sx={{ mt: 1 }}>
                    <Typography variant="body2">
                      <strong>권장 설정:</strong> 일반적인 경우 기본값을 사용하세요.
                      경쟁이 치열한 예약에서는 Wave 간격을 줄이고 Burst Retry를 늘리세요.
                    </Typography>
                  </Alert>
                </Box>
              </AccordionDetails>
            </Accordion>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDialogOpen(false); resetForm() }} disabled={submitting}>취소</Button>
          <Button
            variant="contained"
            onClick={handleAddSchedule}
            disabled={submitting || !newSchedule.camping_site_id || !newSchedule.execute_datetime || !newSchedule.target_date}
            startIcon={submitting ? <CircularProgress size={16} /> : null}
          >
            {submitting ? '등록 중...' : '등록'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* 좌석 선택 다이얼로그 */}
      <SeatSelectionDialog
        open={seatDialogOpen}
        onClose={() => setSeatDialogOpen(false)}
        campingSite={sites.find(s => s.id === newSchedule.camping_site_id)}
        onSeatsSelected={handleSeatsSelected}
        initialSeats={selectedSeats}
      />
    </Box>
  )
}

// =====================================================
// Tab 3: 취소표 사냥 (Cancellation Hunter)
// =====================================================
function CancellationHunterTab({ sites }) {
  const [targets, setTargets] = useState([])
  const [dialogOpen, setDialogOpen] = useState(false)
  const [isHunting, setIsHunting] = useState(false)
  const [newTarget, setNewTarget] = useState({
    camping_site_id: '',
    date_from: '',
    date_to: '',
    preferred_categories: ['grass', 'deck', 'crushed_stone'],
    check_interval: 30,
    auto_reserve: true
  })

  const handleAddTarget = () => {
    const target = {
      id: Date.now(),
      ...newTarget,
      site_name: sites.find(s => s.id === newTarget.camping_site_id)?.name,
      status: 'waiting',
      found_count: 0,
      last_checked: null,
      created_at: new Date().toISOString()
    }
    setTargets(prev => [...prev, target])
    setDialogOpen(false)
  }

  const handleDeleteTarget = (id) => {
    setTargets(prev => prev.filter(t => t.id !== id))
  }

  const handleStartHunting = () => {
    setIsHunting(true)
    // TODO: 실제 모니터링 시작 API 호출
  }

  const handleStopHunting = () => {
    setIsHunting(false)
    // TODO: 모니터링 중지 API 호출
  }

  const categoryLabel = { grass: '잔디', deck: '데크', crushed_stone: '파쇄석' }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Typography variant="h6">취소표 사냥</Typography>
          {isHunting && (
            <Chip
              icon={<Search />}
              label="사냥 중..."
              color="success"
              variant="outlined"
              sx={{ animation: 'pulse 2s infinite' }}
            />
          )}
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          {isHunting ? (
            <Button variant="outlined" color="error" startIcon={<Stop />} onClick={handleStopHunting}>
              사냥 중지
            </Button>
          ) : (
            <Button
              variant="contained"
              color="success"
              startIcon={<PlayArrow />}
              onClick={handleStartHunting}
              disabled={targets.length === 0}
            >
              사냥 시작
            </Button>
          )}
          <Button variant="outlined" startIcon={<Add />} onClick={() => setDialogOpen(true)}>
            타겟 추가
          </Button>
        </Box>
      </Box>

      <Alert severity="warning" sx={{ mb: 2 }}>
        취소표가 발생하면 자동으로 예약을 시도합니다. 모니터링 간격이 너무 짧으면 차단될 수 있습니다.
      </Alert>

      {targets.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Search sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
          <Typography color="text.secondary">모니터링 타겟이 없습니다</Typography>
          <Typography variant="body2" color="text.secondary">
            "타겟 추가" 버튼을 눌러 취소표를 찾을 날짜를 설정하세요
          </Typography>
        </Paper>
      ) : (
        <List>
          {targets.map(target => (
            <Paper key={target.id} sx={{ mb: 1, border: isHunting ? '1px solid' : 'none', borderColor: 'success.main' }}>
              <ListItem>
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1">{target.site_name}</Typography>
                      <Chip
                        label={isHunting ? '검색 중' : '대기'}
                        color={isHunting ? 'success' : 'default'}
                        size="small"
                      />
                      {target.auto_reserve && (
                        <Chip label="자동예약" color="primary" size="small" variant="outlined" />
                      )}
                    </Box>
                  }
                  secondary={
                    <Box sx={{ mt: 1 }}>
                      <Typography variant="body2">
                        <CalendarMonth sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
                        기간: {target.date_from} ~ {target.date_to}
                      </Typography>
                      <Typography variant="body2">
                        <Timer sx={{ fontSize: 14, mr: 0.5, verticalAlign: 'middle' }} />
                        체크 간격: {target.check_interval}초
                      </Typography>
                      <Box sx={{ display: 'flex', gap: 0.5, mt: 0.5 }}>
                        {target.preferred_categories.map(cat => (
                          <Chip key={cat} label={categoryLabel[cat]} size="small" variant="outlined" />
                        ))}
                      </Box>
                    </Box>
                  }
                />
                <ListItemSecondaryAction>
                  <IconButton onClick={() => handleDeleteTarget(target.id)} disabled={isHunting}>
                    <Delete />
                  </IconButton>
                </ListItemSecondaryAction>
              </ListItem>
            </Paper>
          ))}
        </List>
      )}

      {/* 타겟 추가 다이얼로그 */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>모니터링 타겟 추가</DialogTitle>
        <DialogContent>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, pt: 1 }}>
            <TextField
              select
              fullWidth
              label="캠핑장"
              value={newTarget.camping_site_id}
              onChange={(e) => setNewTarget(prev => ({ ...prev, camping_site_id: e.target.value }))}
            >
              {sites.map(site => (
                <MenuItem key={site.id} value={site.id}>{site.name}</MenuItem>
              ))}
            </TextField>

            <Box sx={{ display: 'flex', gap: 2 }}>
              <TextField
                fullWidth
                type="date"
                label="시작 날짜"
                value={newTarget.date_from}
                onChange={(e) => setNewTarget(prev => ({ ...prev, date_from: e.target.value }))}
                InputLabelProps={{ shrink: true }}
              />
              <TextField
                fullWidth
                type="date"
                label="종료 날짜"
                value={newTarget.date_to}
                onChange={(e) => setNewTarget(prev => ({ ...prev, date_to: e.target.value }))}
                InputLabelProps={{ shrink: true }}
              />
            </Box>

            <Typography variant="subtitle2">선호 좌석 타입</Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              {Object.entries(categoryLabel).map(([key, label]) => (
                <Chip
                  key={key}
                  label={label}
                  color={newTarget.preferred_categories.includes(key) ? 'primary' : 'default'}
                  variant={newTarget.preferred_categories.includes(key) ? 'filled' : 'outlined'}
                  onClick={() => {
                    setNewTarget(prev => ({
                      ...prev,
                      preferred_categories: prev.preferred_categories.includes(key)
                        ? prev.preferred_categories.filter(c => c !== key)
                        : [...prev.preferred_categories, key]
                    }))
                  }}
                />
              ))}
            </Box>

            <TextField
              fullWidth
              type="number"
              label="체크 간격 (초)"
              value={newTarget.check_interval}
              onChange={(e) => setNewTarget(prev => ({ ...prev, check_interval: parseInt(e.target.value) }))}
              inputProps={{ min: 10, max: 300 }}
              helperText="너무 짧으면 차단될 수 있습니다 (최소 10초)"
            />

            <FormControlLabel
              control={
                <Switch
                  checked={newTarget.auto_reserve}
                  onChange={(e) => setNewTarget(prev => ({ ...prev, auto_reserve: e.target.checked }))}
                />
              }
              label="취소표 발견 시 자동 예약"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>취소</Button>
          <Button
            variant="contained"
            onClick={handleAddTarget}
            disabled={!newTarget.camping_site_id || !newTarget.date_from || !newTarget.date_to}
          >
            등록
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}

// =====================================================
// 메인 컴포넌트
// =====================================================
export default function AutoReservation() {
  const [tabValue, setTabValue] = useState(0)
  const [sites, setSites] = useState([])
  const [selectedSite, setSelectedSite] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadSites()
  }, [])

  const loadSites = async () => {
    try {
      const data = await getCampingSites()
      // API가 배열을 직접 반환
      const siteList = Array.isArray(data) ? data : (data.camping_sites || [])
      setSites(siteList)
      if (siteList.length > 0) {
        setSelectedSite(siteList[0])
      }
    } catch (err) {
      console.error('Failed to load sites:', err)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 400 }}>
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>자동 예약</Typography>

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tabValue} onChange={(e, v) => setTabValue(v)} variant="fullWidth">
          <Tab icon={<Speed />} label="즉시 예약" iconPosition="start" />
          <Tab icon={<Schedule />} label="스케줄 예약" iconPosition="start" />
          <Tab icon={<Search />} label="취소표 사냥" iconPosition="start" />
        </Tabs>
      </Paper>

      {tabValue === 0 && (
        <QuickReserveTab
          sites={sites}
          selectedSite={selectedSite}
          setSelectedSite={setSelectedSite}
        />
      )}
      {tabValue === 1 && <ScheduledReserveTab sites={sites} />}
      {tabValue === 2 && <CancellationHunterTab sites={sites} />}
    </Box>
  )
}
