import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Box,
  Typography,
  Chip,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Paper,
  Divider,
  Tooltip
} from '@mui/material'
import {
  EventSeat as SeatIcon,
  Delete as DeleteIcon,
  ArrowUpward as ArrowUpIcon,
  ArrowDownward as ArrowDownIcon,
  Add as AddIcon
} from '@mui/icons-material'
import { getSeatsByCategory } from '../services/api'

/**
 * 다중 좌석 선택 다이얼로그 (우선순위 설정 포함)
 * 잔디/데크/파쇄석 카테고리별로 좌석을 표시하고 여러 좌석을 우선순위 순으로 선택
 */
function SeatSelectionDialog({ open, onClose, campingSite, onSeatsSelected, initialSeats = [] }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [seats, setSeats] = useState({ grass: [], deck: [], crushed_stone: [] })
  const [selectedSeats, setSelectedSeats] = useState([]) // 우선순위 순 선택된 좌석 배열
  const [selectedCategory, setSelectedCategory] = useState('')
  const [seatToAdd, setSeatToAdd] = useState(null)

  useEffect(() => {
    if (open && campingSite) {
      loadSeats()
    }
  }, [open, campingSite])

  // 초기 좌석 설정
  useEffect(() => {
    if (initialSeats && initialSeats.length > 0) {
      setSelectedSeats(initialSeats)
    }
  }, [initialSeats, open])

  const loadSeats = async () => {
    setLoading(true)
    setError('')
    try {
      const data = await getSeatsByCategory(campingSite.id)
      setSeats(data)
    } catch (err) {
      console.error('Failed to load seats:', err)
      setError('좌석 정보를 불러오는데 실패했습니다')
    } finally {
      setLoading(false)
    }
  }

  const handleCategoryChange = (event) => {
    setSelectedCategory(event.target.value)
    setSeatToAdd(null)
  }

  const handleSeatChange = (event) => {
    const seatId = event.target.value
    const allSeats = [...seats.grass, ...seats.deck, ...seats.crushed_stone]
    const seat = allSeats.find(s => s.id === seatId)
    setSeatToAdd(seat)
  }

  const handleAddSeat = () => {
    if (seatToAdd && !selectedSeats.find(s => s.id === seatToAdd.id)) {
      setSelectedSeats([...selectedSeats, seatToAdd])
      setSeatToAdd(null)
      setSelectedCategory('')
    }
  }

  const handleRemoveSeat = (seatId) => {
    setSelectedSeats(selectedSeats.filter(s => s.id !== seatId))
  }

  const handleMoveUp = (index) => {
    if (index === 0) return
    const newSeats = [...selectedSeats]
    const temp = newSeats[index - 1]
    newSeats[index - 1] = newSeats[index]
    newSeats[index] = temp
    setSelectedSeats(newSeats)
  }

  const handleMoveDown = (index) => {
    if (index === selectedSeats.length - 1) return
    const newSeats = [...selectedSeats]
    const temp = newSeats[index + 1]
    newSeats[index + 1] = newSeats[index]
    newSeats[index] = temp
    setSelectedSeats(newSeats)
  }

  const handleConfirm = () => {
    onSeatsSelected(selectedSeats)
    onClose()
  }

  const getCategoryLabel = (category) => {
    const labels = {
      grass: '잔디사이트',
      deck: '데크사이트',
      crushed_stone: '파쇄석사이트'
    }
    return labels[category] || category
  }

  const getCategoryColor = (category) => {
    const colors = {
      grass: 'success',
      deck: 'warning',
      crushed_stone: 'info'
    }
    return colors[category] || 'default'
  }

  const getAvailableSeats = () => {
    if (!selectedCategory) return []
    const categorySeats = seats[selectedCategory] || []
    // 이미 선택된 좌석은 제외
    return categorySeats.filter(seat => !selectedSeats.find(s => s.id === seat.id))
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <SeatIcon sx={{ mr: 1 }} />
          우선순위 좌석 선택 - {campingSite?.name}
        </Box>
      </DialogTitle>

      <DialogContent>
        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Alert severity="error">{error}</Alert>
        ) : (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {/* 카테고리 정보 */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                사용 가능한 좌석 수
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                <Chip
                  label={`잔디사이트: ${seats.grass.length}개`}
                  color="success"
                  size="small"
                />
                <Chip
                  label={`데크사이트: ${seats.deck.length}개`}
                  color="warning"
                  size="small"
                />
                <Chip
                  label={`파쇄석사이트: ${seats.crushed_stone.length}개`}
                  color="info"
                  size="small"
                />
              </Box>
            </Box>

            <Divider />

            {/* 좌석 추가 섹션 */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                좌석 추가
              </Typography>
              <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
                {/* 카테고리 선택 */}
                <FormControl sx={{ minWidth: 150 }}>
                  <InputLabel size="small">카테고리</InputLabel>
                  <Select
                    size="small"
                    value={selectedCategory}
                    label="카테고리"
                    onChange={handleCategoryChange}
                  >
                    <MenuItem value="">
                      <em>선택</em>
                    </MenuItem>
                    {seats.grass.length > 0 && (
                      <MenuItem value="grass">잔디 ({seats.grass.length})</MenuItem>
                    )}
                    {seats.deck.length > 0 && (
                      <MenuItem value="deck">데크 ({seats.deck.length})</MenuItem>
                    )}
                    {seats.crushed_stone.length > 0 && (
                      <MenuItem value="crushed_stone">파쇄석 ({seats.crushed_stone.length})</MenuItem>
                    )}
                  </Select>
                </FormControl>

                {/* 좌석 선택 */}
                <FormControl sx={{ minWidth: 200, flex: 1 }}>
                  <InputLabel size="small">좌석</InputLabel>
                  <Select
                    size="small"
                    value={seatToAdd?.id || ''}
                    label="좌석"
                    onChange={handleSeatChange}
                    disabled={!selectedCategory}
                  >
                    <MenuItem value="">
                      <em>선택</em>
                    </MenuItem>
                    {getAvailableSeats().map((seat) => (
                      <MenuItem key={seat.id} value={seat.id}>
                        {seat.seat_name} ({seat.product_code})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>

                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={handleAddSeat}
                  disabled={!seatToAdd}
                  size="small"
                >
                  추가
                </Button>
              </Box>
            </Box>

            <Divider />

            {/* 선택된 좌석 목록 (우선순위 순) */}
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                선택된 좌석 ({selectedSeats.length}개) - 위에서부터 우선순위 높음
              </Typography>

              {selectedSeats.length === 0 ? (
                <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">
                    좌석을 추가해주세요. 첫 번째 좌석이 가장 높은 우선순위입니다.
                  </Typography>
                </Paper>
              ) : (
                <List sx={{ p: 0 }}>
                  {selectedSeats.map((seat, index) => (
                    <Paper
                      key={seat.id}
                      variant="outlined"
                      sx={{
                        mb: 1,
                        backgroundColor: index === 0 ? 'action.selected' : 'background.paper'
                      }}
                    >
                      <ListItem>
                        <Box
                          sx={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            width: 32,
                            height: 32,
                            borderRadius: '50%',
                            backgroundColor: index === 0 ? 'primary.main' : 'grey.300',
                            color: index === 0 ? 'white' : 'text.primary',
                            mr: 2,
                            fontWeight: 'bold'
                          }}
                        >
                          {index + 1}
                        </Box>
                        <ListItemText
                          primary={
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Typography variant="body1" fontWeight="bold">
                                {seat.seat_name}
                              </Typography>
                              <Chip
                                label={getCategoryLabel(seat.seat_category)}
                                color={getCategoryColor(seat.seat_category)}
                                size="small"
                              />
                              {index === 0 && (
                                <Chip label="1순위" color="primary" size="small" />
                              )}
                            </Box>
                          }
                          secondary={`상품 코드: ${seat.product_code}`}
                        />
                        <ListItemSecondaryAction>
                          <Tooltip title="위로 이동">
                            <span>
                              <IconButton
                                size="small"
                                onClick={() => handleMoveUp(index)}
                                disabled={index === 0}
                              >
                                <ArrowUpIcon />
                              </IconButton>
                            </span>
                          </Tooltip>
                          <Tooltip title="아래로 이동">
                            <span>
                              <IconButton
                                size="small"
                                onClick={() => handleMoveDown(index)}
                                disabled={index === selectedSeats.length - 1}
                              >
                                <ArrowDownIcon />
                              </IconButton>
                            </span>
                          </Tooltip>
                          <Tooltip title="삭제">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={() => handleRemoveSeat(seat.id)}
                            >
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
                        </ListItemSecondaryAction>
                      </ListItem>
                    </Paper>
                  ))}
                </List>
              )}
            </Box>

            <Alert severity="info">
              <strong>우선순위 좌석 풀 안내</strong>
              <Typography variant="body2">
                • 1순위 좌석 예약 실패 시 자동으로 2순위, 3순위 순으로 시도합니다.
              </Typography>
              <Typography variant="body2">
                • 위/아래 화살표로 우선순위를 조정할 수 있습니다.
              </Typography>
              <Typography variant="body2">
                • 여러 좌석을 추가하면 예약 성공 확률이 높아집니다.
              </Typography>
            </Alert>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>취소</Button>
        <Button
          onClick={handleConfirm}
          variant="contained"
          disabled={selectedSeats.length === 0}
        >
          좌석 선택 완료 ({selectedSeats.length}개)
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default SeatSelectionDialog
