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
  Alert
} from '@mui/material'

export default function CampingSiteDialog({ open, onClose, onSave, site = null }) {
  const [formData, setFormData] = useState({
    name: '',
    site_type: 'custom',
    url: '',
    login_username: '',
    login_password: '',
    booker_name: '',
    booker_phone: '',
    booker_car_number: ''
  })
  const [error, setError] = useState('')

  useEffect(() => {
    if (site) {
      setFormData({
        name: site.name || '',
        site_type: site.site_type || 'custom',
        url: site.url || '',
        login_username: site.login_username || '',
        login_password: site.login_password || '',
        booker_name: site.booker_name || '',
        booker_phone: site.booker_phone || '',
        booker_car_number: site.booker_car_number || ''
      })
    } else {
      setFormData({
        name: '',
        site_type: 'custom',
        url: '',
        login_username: '',
        login_password: '',
        booker_name: '',
        booker_phone: '',
        booker_car_number: ''
      })
    }
    setError('')
  }, [site, open])

  const handleChange = (field) => (event) => {
    setFormData({
      ...formData,
      [field]: event.target.value
    })
  }

  const handleSubmit = () => {
    // 필수 필드 검증
    if (!formData.name || !formData.url) {
      setError('캠핑장 이름과 URL은 필수입니다')
      return
    }

    onSave(formData)
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {site ? '캠핑장 정보 수정' : '캠핑장 추가'}
      </DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mt: 2 }}>
          <Typography variant="h6" gutterBottom>
            기본 정보
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="캠핑장 이름"
                value={formData.name}
                onChange={handleChange('name')}
                required
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="캠핑장 URL"
                value={formData.url}
                onChange={handleChange('url')}
                placeholder="https://example.com"
                required
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

          <Typography variant="h6" gutterBottom>
            로그인 정보
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            캠핑장 사이트에 로그인할 때 사용하는 계정 정보
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="아이디"
                value={formData.login_username}
                onChange={handleChange('login_username')}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                type="password"
                label="비밀번호"
                value={formData.login_password}
                onChange={handleChange('login_password')}
              />
            </Grid>
          </Grid>

          <Divider sx={{ my: 3 }} />

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
                label="이름"
                value={formData.booker_name}
                onChange={handleChange('booker_name')}
              />
            </Grid>
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="전화번호"
                value={formData.booker_phone}
                onChange={handleChange('booker_phone')}
                placeholder="010-1234-5678"
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
          {site ? '수정' : '추가'}
        </Button>
      </DialogActions>
    </Dialog>
  )
}
