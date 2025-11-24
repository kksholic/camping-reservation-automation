import React, { useState, useEffect } from 'react'
import {
  Box, Typography, Button, Paper, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip, TextField, Grid,
  Dialog, DialogTitle, DialogContent, DialogActions, IconButton,
  Alert, Divider, Card, CardContent
} from '@mui/material'
import AddIcon from '@mui/icons-material/Add'
import DeleteIcon from '@mui/icons-material/Delete'
import AccessTimeIcon from '@mui/icons-material/AccessTime'
import SyncIcon from '@mui/icons-material/Sync'
import { getMonitoringTargets, getSchedules, createSchedule, deleteSchedule, getServerTimeInfo } from '../services/api'

export default function Monitoring() {
  const [targets, setTargets] = useState([])
  const [schedules, setSchedules] = useState([])
  const [openScheduleDialog, setOpenScheduleDialog] = useState(false)
  const [scheduleForm, setScheduleForm] = useState({ hour: 9, minute: 0, second: 0 })
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(null)
  const [serverTimeInfo, setServerTimeInfo] = useState(null)
  const [loadingServerTime, setLoadingServerTime] = useState(false)

  useEffect(() => {
    loadTargets()
    loadSchedules()
    const interval = setInterval(() => {
      loadTargets()
      loadSchedules()
    }, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadTargets = async () => {
    try {
      const data = await getMonitoringTargets()
      setTargets(data)
    } catch (error) {
      console.error('Failed to load monitoring targets:', error)
    }
  }

  const loadSchedules = async () => {
    try {
      const data = await getSchedules()
      setSchedules(data)
    } catch (error) {
      console.error('Failed to load schedules:', error)
    }
  }

  const handleCreateSchedule = async () => {
    try {
      setError(null)
      await createSchedule(scheduleForm)
      setSuccess('스케줄이 등록되었습니다!')
      setOpenScheduleDialog(false)
      setScheduleForm({ hour: 9, minute: 0, second: 0 })
      loadSchedules()
      setTimeout(() => setSuccess(null), 3000)
    } catch (error) {
      setError(error.response?.data?.error || '스케줄 등록에 실패했습니다.')
    }
  }

  const handleDeleteSchedule = async (jobId) => {
    if (!confirm('이 스케줄을 삭제하시겠습니까?')) return

    try {
      await deleteSchedule(jobId)
      setSuccess('스케줄이 삭제되었습니다!')
      loadSchedules()
      setTimeout(() => setSuccess(null), 3000)
    } catch (error) {
      setError('스케줄 삭제에 실패했습니다.')
    }
  }

  const handleSyncServerTime = async () => {
    setLoadingServerTime(true)
    try {
      const data = await getServerTimeInfo()
      setServerTimeInfo(data)
      setSuccess('서버 시간 동기화 완료!')
      setTimeout(() => setSuccess(null), 3000)
    } catch (error) {
      setError('서버 시간 동기화에 실패했습니다.')
    } finally {
      setLoadingServerTime(false)
    }
  }

  return (
    <Box>
      {/* 알림 메시지 */}
      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {/* 모니터링 타겟 섹션 */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          모니터링 관리
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => {/* TODO: 모니터링 타겟 추가 */}}
        >
          타겟 추가
        </Button>
      </Box>

      <TableContainer component={Paper} sx={{ mb: 4 }}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>캠핑장</TableCell>
              <TableCell>목표 날짜</TableCell>
              <TableCell>상태</TableCell>
              <TableCell>마지막 확인</TableCell>
              <TableCell>알림 전송</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {targets.map((target) => (
              <TableRow key={target.id}>
                <TableCell>{target.id}</TableCell>
                <TableCell>{target.camping_site_name}</TableCell>
                <TableCell>{target.target_date}</TableCell>
                <TableCell>
                  <Chip
                    label={target.last_status || '확인 중'}
                    color={target.last_status === 'available' ? 'success' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  {target.last_checked ? new Date(target.last_checked).toLocaleString() : '-'}
                </TableCell>
                <TableCell>
                  {target.notification_sent ? '✅' : '❌'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      <Divider sx={{ my: 4 }} />

      {/* 서버 시간 동기화 섹션 */}
      <Box mb={4}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box display="flex" alignItems="center" gap={1}>
            <SyncIcon color="primary" />
            <Typography variant="h5">
              서버 시간 동기화
            </Typography>
          </Box>
          <Button
            variant="outlined"
            startIcon={<SyncIcon />}
            onClick={handleSyncServerTime}
            disabled={loadingServerTime}
          >
            {loadingServerTime ? '동기화 중...' : '서버 시간 확인'}
          </Button>
        </Box>

        {serverTimeInfo && (
          <Card>
            <CardContent>
              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    XTicket 서버 시간
                  </Typography>
                  <Typography variant="h6">
                    {new Date(serverTimeInfo.server_time).toLocaleString('ko-KR')}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    로컬 시간
                  </Typography>
                  <Typography variant="h6">
                    {new Date(serverTimeInfo.local_time).toLocaleString('ko-KR')}
                  </Typography>
                </Grid>
                <Grid item xs={12} md={4}>
                  <Typography variant="body2" color="text.secondary">
                    시간 오프셋
                  </Typography>
                  <Typography variant="h6" color={Math.abs(serverTimeInfo.offset_seconds) > 5 ? 'error' : 'success'}>
                    {serverTimeInfo.offset_seconds > 0 ? '+' : ''}{serverTimeInfo.offset_seconds?.toFixed(2)}초
                  </Typography>
                </Grid>
                <Grid item xs={12}>
                  <Alert severity={Math.abs(serverTimeInfo.offset_seconds) > 5 ? 'warning' : 'success'}>
                    {serverTimeInfo.message}
                    {Math.abs(serverTimeInfo.offset_seconds) > 5 &&
                      ' - 시간 차이가 큽니다. 스케줄 실행 시 서버 시간 기준으로 조정됩니다.'}
                  </Alert>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        )}
      </Box>

      <Divider sx={{ my: 4 }} />

      {/* 스케줄 관리 섹션 */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={1}>
          <AccessTimeIcon color="primary" />
          <Typography variant="h5">
            예약 스케줄 관리
          </Typography>
        </Box>
        <Button
          variant="contained"
          color="secondary"
          startIcon={<AddIcon />}
          onClick={() => setOpenScheduleDialog(true)}
        >
          스케줄 추가
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>스케줄 ID</TableCell>
              <TableCell>다음 실행 시간</TableCell>
              <TableCell>실행 주기</TableCell>
              <TableCell>작업</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {schedules.length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} align="center" sx={{ py: 4, color: 'text.secondary' }}>
                  등록된 스케줄이 없습니다. "스케줄 추가" 버튼을 눌러 새 스케줄을 등록하세요.
                </TableCell>
              </TableRow>
            ) : (
              schedules.map((schedule) => (
                <TableRow key={schedule.id}>
                  <TableCell>{schedule.id}</TableCell>
                  <TableCell>
                    {schedule.next_run_time
                      ? new Date(schedule.next_run_time).toLocaleString('ko-KR', {
                          year: 'numeric',
                          month: '2-digit',
                          day: '2-digit',
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit'
                        })
                      : '-'}
                  </TableCell>
                  <TableCell>
                    <Chip label={schedule.trigger} size="small" color="primary" variant="outlined" />
                  </TableCell>
                  <TableCell>
                    <IconButton
                      color="error"
                      size="small"
                      onClick={() => handleDeleteSchedule(schedule.id)}
                      title="스케줄 삭제"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 스케줄 추가 다이얼로그 */}
      <Dialog open={openScheduleDialog} onClose={() => setOpenScheduleDialog(false)}>
        <DialogTitle>새 스케줄 추가</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            매일 지정한 시간에 자동으로 예약을 시도합니다.
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={4}>
              <TextField
                fullWidth
                label="시 (Hour)"
                type="number"
                value={scheduleForm.hour}
                onChange={(e) => setScheduleForm({ ...scheduleForm, hour: parseInt(e.target.value) })}
                inputProps={{ min: 0, max: 23 }}
                helperText="0-23"
              />
            </Grid>
            <Grid item xs={4}>
              <TextField
                fullWidth
                label="분 (Minute)"
                type="number"
                value={scheduleForm.minute}
                onChange={(e) => setScheduleForm({ ...scheduleForm, minute: parseInt(e.target.value) })}
                inputProps={{ min: 0, max: 59 }}
                helperText="0-59"
              />
            </Grid>
            <Grid item xs={4}>
              <TextField
                fullWidth
                label="초 (Second)"
                type="number"
                value={scheduleForm.second}
                onChange={(e) => setScheduleForm({ ...scheduleForm, second: parseInt(e.target.value) })}
                inputProps={{ min: 0, max: 59 }}
                helperText="0-59"
              />
            </Grid>
          </Grid>
          <Box sx={{ mt: 2, p: 2, bgcolor: 'info.light', borderRadius: 1 }}>
            <Typography variant="body2">
              📅 매일 <strong>{String(scheduleForm.hour).padStart(2, '0')}:
              {String(scheduleForm.minute).padStart(2, '0')}:
              {String(scheduleForm.second).padStart(2, '0')}</strong>에 실행됩니다.
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenScheduleDialog(false)}>취소</Button>
          <Button onClick={handleCreateSchedule} variant="contained" color="primary">
            등록
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  )
}
