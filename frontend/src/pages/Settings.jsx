import { useState } from 'react'
import {
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Typography,
  Alert,
  Container,
  Grid,
  Divider
} from '@mui/material'
import { Settings as SettingsIcon, Key as KeyIcon, Person as PersonIcon } from '@mui/icons-material'
import { changeCredentials } from '../services/api'

function Settings({ username, onUsernameChange }) {
  const [newUsername, setNewUsername] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleUsernameChange = async (e) => {
    e.preventDefault()

    if (!newUsername) {
      setError('새 아이디를 입력해주세요')
      return
    }

    setError('')
    setSuccess('')
    setLoading(true)

    try {
      const response = await changeCredentials({
        new_username: newUsername
      })

      if (response.success) {
        setSuccess(response.message)
        setNewUsername('')
        // 부모 컴포넌트에 사용자 이름 변경 알림
        if (onUsernameChange) {
          onUsernameChange(newUsername)
        }
      } else {
        setError(response.message || '아이디 변경에 실패했습니다')
      }
    } catch (err) {
      setError(err.response?.data?.message || '아이디 변경 중 오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  const handlePasswordChange = async (e) => {
    e.preventDefault()

    if (!currentPassword || !newPassword || !confirmPassword) {
      setError('모든 비밀번호 필드를 입력해주세요')
      return
    }

    if (newPassword !== confirmPassword) {
      setError('새 비밀번호가 일치하지 않습니다')
      return
    }

    if (newPassword.length < 6) {
      setError('비밀번호는 최소 6자 이상이어야 합니다')
      return
    }

    setError('')
    setSuccess('')
    setLoading(true)

    try {
      const response = await changeCredentials({
        current_password: currentPassword,
        new_password: newPassword
      })

      if (response.success) {
        setSuccess(response.message)
        setCurrentPassword('')
        setNewPassword('')
        setConfirmPassword('')
      } else {
        setError(response.message || '비밀번호 변경에 실패했습니다')
      }
    } catch (err) {
      setError(err.response?.data?.message || '비밀번호 변경 중 오류가 발생했습니다')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <SettingsIcon sx={{ fontSize: 32, mr: 2 }} />
        <Typography variant="h4">
          관리자 설정
        </Typography>
      </Box>

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* 현재 정보 */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                현재 계정 정보
              </Typography>
              <Typography variant="body1" color="text.secondary">
                아이디: <strong>{username}</strong>
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* 아이디 변경 */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <PersonIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">
                  아이디 변경
                </Typography>
              </Box>

              <form onSubmit={handleUsernameChange}>
                <TextField
                  fullWidth
                  label="새 아이디"
                  value={newUsername}
                  onChange={(e) => setNewUsername(e.target.value)}
                  margin="normal"
                  placeholder="새로운 아이디를 입력하세요"
                  disabled={loading}
                />
                <Button
                  type="submit"
                  variant="contained"
                  sx={{ mt: 2 }}
                  disabled={loading}
                >
                  {loading ? '변경 중...' : '아이디 변경'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </Grid>

        {/* 비밀번호 변경 */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <KeyIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">
                  비밀번호 변경
                </Typography>
              </Box>

              <form onSubmit={handlePasswordChange}>
                <TextField
                  fullWidth
                  type="password"
                  label="현재 비밀번호"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  margin="normal"
                  disabled={loading}
                />
                <Divider sx={{ my: 2 }} />
                <TextField
                  fullWidth
                  type="password"
                  label="새 비밀번호"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  margin="normal"
                  helperText="최소 6자 이상"
                  disabled={loading}
                />
                <TextField
                  fullWidth
                  type="password"
                  label="새 비밀번호 확인"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  margin="normal"
                  disabled={loading}
                />
                <Button
                  type="submit"
                  variant="contained"
                  color="secondary"
                  sx={{ mt: 2 }}
                  disabled={loading}
                >
                  {loading ? '변경 중...' : '비밀번호 변경'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  )
}

export default Settings
