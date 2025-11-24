import React, { useState, useEffect } from 'react'
import {
  Box, Typography, Paper, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, Chip
} from '@mui/material'
import { getReservations } from '../services/api'

export default function Reservations() {
  const [reservations, setReservations] = useState([])

  useEffect(() => {
    loadReservations()
  }, [])

  const loadReservations = async () => {
    try {
      const data = await getReservations()
      setReservations(data)
    } catch (error) {
      console.error('Failed to load reservations:', error)
    }
  }

  const getStatusColor = (status) => {
    const colors = {
      'reserved': 'success',
      'monitoring': 'info',
      'available': 'warning',
      'failed': 'error',
      'processing': 'default'
    }
    return colors[status] || 'default'
  }

  const getStatusLabel = (status) => {
    const labels = {
      'reserved': '예약 완료',
      'monitoring': '모니터링 중',
      'available': '예약 가능',
      'failed': '실패',
      'processing': '처리 중'
    }
    return labels[status] || status
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        예약 내역
      </Typography>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>캠핑장</TableCell>
              <TableCell>체크인</TableCell>
              <TableCell>체크아웃</TableCell>
              <TableCell>상태</TableCell>
              <TableCell>예약번호</TableCell>
              <TableCell>등록일</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {reservations.map((reservation) => (
              <TableRow key={reservation.id}>
                <TableCell>{reservation.id}</TableCell>
                <TableCell>{reservation.camping_site_name}</TableCell>
                <TableCell>{reservation.check_in_date}</TableCell>
                <TableCell>{reservation.check_out_date}</TableCell>
                <TableCell>
                  <Chip
                    label={getStatusLabel(reservation.status)}
                    color={getStatusColor(reservation.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>{reservation.reservation_number || '-'}</TableCell>
                <TableCell>
                  {new Date(reservation.created_at).toLocaleDateString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  )
}
