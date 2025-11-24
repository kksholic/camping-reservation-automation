import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Button,
  Grid,
  Typography,
  Box,
  Divider,
  Alert,
  FormControlLabel,
  Checkbox
} from '@mui/material'

export default function CampingSiteAccountDialog({ open, onClose, onSave, account = null, siteName }) {
  const [formData, setFormData] = useState({
    login_username: '',
    login_password: '',
    booker_name: '',
    booker_phone: '',
    booker_car_number: '',
    nickname: '',
    is_active: true,
    priority: 0
  })
  const [error, setError] = useState('')

  useEffect(() => {
    if (account) {
      setFormData({
        login_username: account.login_username || '',
        login_password: account.login_password || '',
        booker_name: account.booker_name || '',
        booker_phone: account.booker_phone || '',
        booker_car_number: account.booker_car_number || '',
        nickname: account.nickname || '',
        is_active: account.is_active !== undefined ? account.is_active : true,
        priority: account.priority || 0
      })
    } else {
      setFormData({
        login_username: '',
        login_password: '',
        booker_name: '',
        booker_phone: '',
        booker_car_number: '',
        nickname: '',
        is_active: true,
        priority: 0
      })
    }
    setError('')
  }, [account, open])

  const handleChange = (field) => (event) => {
    const value = field === 'is_active' ? event.target.checked : event.target.value
    setFormData({
      ...formData,
      [field]: value
    })
  }

  const handleSubmit = () => {
    // 필수 필드 검증
    if (!formData.login_username || !formData.login_password || !formData.booker_name || !formData.booker_phone) {
      setError('로그인 아이디, 비밀번호, 예약자 이름, 전화번호는 필수입니다')
      return
    }

    onSave(formData)
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {account ? '계정 정보 수정' : '계정 추가'} - {siteName}
      </DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mt: 2 }}>
          {/* 기본 정보 */}
          <Typography variant="h6" gutterBottom>
            계정 정보
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            여러 계정을 등록하면 동시에 예약을 시도합니다
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="계정 별칭"
                value={formData.nickname}
                onChange={handleChange('nickname')}
                placeholder="예: 내 계정, 엄마 계정"
                helperText="계정 구분을 위한 별칭 (선택)"
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="number"
                label="우선순위"
                value={formData.priority}
                onChange={handleChange('priority')}
                helperText="낮을수록 먼저 시도 (0이 가장 높음)"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.is_active}
                    onChange={handleChange('is_active')}
                  />
                }
                label="활성화 (비활성화하면 예약 시도하지 않음)"
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          {/* 로그인 정보 */}
          <Typography variant="h6" gutterBottom>
            캠핑장 로그인 정보
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            캠핑장 사이트에 로그인할 때 사용하는 계정 정보
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="로그인 아이디"
                value={formData.login_username}
                onChange={handleChange('login_username')}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="password"
                label="로그인 비밀번호"
                value={formData.login_password}
                onChange={handleChange('login_password')}
                required
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          {/* 예약자 정보 */}
          <Typography variant="h6" gutterBottom>
            예약자 정보
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            예약 시 기재될 정보
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="예약자 이름"
                value={formData.booker_name}
                onChange={handleChange('booker_name')}
                required
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="전화번호"
                value={formData.booker_phone}
                onChange={handleChange('booker_phone')}
                placeholder="010-1234-5678"
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="차량번호"
                value={formData.booker_car_number}
                onChange={handleChange('booker_car_number')}
                placeholder="12가3456"
              />
            </Grid>
          </Grid>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>취소</Button>
        <Button onClick={handleSubmit} variant="contained" color="primary">
          {account ? '수정' : '추가'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
