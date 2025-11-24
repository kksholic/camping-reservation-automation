import React, { useState, useEffect } from 'react'
import { Grid, Paper, Typography, Box, Button } from '@mui/material'
import { getStatistics, getMonitoringStatus } from '../services/api'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'
import StopIcon from '@mui/icons-material/Stop'

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [monitoringStatus, setMonitoringStatus] = useState(null)

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 5000)
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const [statsData, statusData] = await Promise.all([
        getStatistics(),
        getMonitoringStatus()
      ])
      setStats(statsData)
      setMonitoringStatus(statusData)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    }
  }

  if (!stats || !monitoringStatus) {
    return <Typography>로딩 중...</Typography>
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        대시보드
      </Typography>

      <Grid container spacing={3}>
        {/* 통계 카드 */}
        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography color="textSecondary" gutterBottom>
              등록된 캠핑장
            </Typography>
            <Typography variant="h4">
              {stats.total_sites}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography color="textSecondary" gutterBottom>
              활성 모니터링
            </Typography>
            <Typography variant="h4">
              {stats.active_monitoring}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography color="textSecondary" gutterBottom>
              성공한 예약
            </Typography>
            <Typography variant="h4" color="success.main">
              {stats.successful_reservations}
            </Typography>
          </Paper>
        </Grid>

        <Grid item xs={12} md={3}>
          <Paper sx={{ p: 2 }}>
            <Typography color="textSecondary" gutterBottom>
              실패한 예약
            </Typography>
            <Typography variant="h4" color="error.main">
              {stats.failed_reservations}
            </Typography>
          </Paper>
        </Grid>

        {/* 모니터링 상태 */}
        <Grid item xs={12}>
          <Paper sx={{ p: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Box>
                <Typography variant="h6" gutterBottom>
                  모니터링 상태
                </Typography>
                <Typography color="textSecondary">
                  상태: {monitoringStatus.is_running ? '실행 중' : '중지됨'}
                </Typography>
                <Typography color="textSecondary">
                  활성 타겟: {monitoringStatus.active_targets}개
                </Typography>
              </Box>
              <Box>
                {monitoringStatus.is_running ? (
                  <Button
                    variant="contained"
                    color="error"
                    startIcon={<StopIcon />}
                    onClick={() => {/* TODO: 모니터링 중지 */}}
                  >
                    모니터링 중지
                  </Button>
                ) : (
                  <Button
                    variant="contained"
                    color="primary"
                    startIcon={<PlayArrowIcon />}
                    onClick={() => {/* TODO: 모니터링 시작 */}}
                  >
                    모니터링 시작
                  </Button>
                )}
              </Box>
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  )
}
