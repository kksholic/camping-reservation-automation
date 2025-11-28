import { useState, useEffect } from 'react'
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
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Chip,
  Tooltip,
  CircularProgress,
  FormControlLabel,
  Switch
} from '@mui/material'
import { Settings as SettingsIcon, Key as KeyIcon, Person as PersonIcon, Telegram as TelegramIcon, ContentCopy as CopyIcon, Refresh as RefreshIcon, Check as CheckIcon } from '@mui/icons-material'
import { changeCredentials, getSettings, updateTelegramSettings, testTelegram, getTelegramChats } from '../services/api'

function Settings({ username, onUsernameChange }) {
  const [newUsername, setNewUsername] = useState('')
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  // 텔레그램 설정
  const [telegramBotToken, setTelegramBotToken] = useState('')
  const [telegramChatId, setTelegramChatId] = useState('')
  const [telegramLoading, setTelegramLoading] = useState(false)

  // 텔레그램 대화자 목록
  const [telegramChats, setTelegramChats] = useState([])
  const [chatsLoading, setChatsLoading] = useState(false)
  const [copiedId, setCopiedId] = useState(null)

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const settings = await getSettings()
      setTelegramBotToken(settings.telegram_bot_token || '')
      setTelegramChatId(settings.telegram_chat_id || '')

      // 봇 토큰이 있으면 대화자 목록도 로드
      if (settings.telegram_bot_token) {
        loadTelegramChats()
      }
    } catch (err) {
      console.error('Failed to load settings:', err)
    }
  }

  const loadTelegramChats = async () => {
    setChatsLoading(true)
    try {
      const response = await getTelegramChats()
      if (response.success) {
        setTelegramChats(response.chats || [])
      }
    } catch (err) {
      console.error('Failed to load telegram chats:', err)
    } finally {
      setChatsLoading(false)
    }
  }

  const handleCopyChatId = async (chatId) => {
    try {
      await navigator.clipboard.writeText(chatId)
      setCopiedId(chatId)
      setTimeout(() => setCopiedId(null), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  const handleSelectChat = (chatId) => {
    setTelegramChatId(chatId)
  }

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

  const handleTelegramSettingsSave = async (e) => {
    e.preventDefault()

    setError('')
    setSuccess('')
    setTelegramLoading(true)

    try {
      const response = await updateTelegramSettings({
        telegram_bot_token: telegramBotToken,
        telegram_chat_id: telegramChatId
      })

      if (response.success) {
        setSuccess(response.message)
      } else {
        setError(response.message || '텔레그램 설정 저장에 실패했습니다')
      }
    } catch (err) {
      setError(err.response?.data?.message || '텔레그램 설정 저장 중 오류가 발생했습니다')
    } finally {
      setTelegramLoading(false)
    }
  }

  const handleTestTelegram = async () => {
    if (!telegramBotToken || !telegramChatId) {
      setError('텔레그램 봇 토큰과 채팅방 ID를 모두 입력해주세요')
      return
    }

    setError('')
    setSuccess('')
    setTelegramLoading(true)

    try {
      const response = await testTelegram()

      if (response.success) {
        setSuccess(response.message)
      } else {
        setError(response.message || '테스트 알림 전송에 실패했습니다')
      }
    } catch (err) {
      setError(err.response?.data?.message || '테스트 알림 전송 중 오류가 발생했습니다')
    } finally {
      setTelegramLoading(false)
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

        {/* 텔레그램 알림 설정 */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <TelegramIcon sx={{ mr: 1, color: 'primary.main' }} />
                <Typography variant="h6">
                  텔레그램 알림 설정
                </Typography>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                예약 성공, 실패 등의 알림을 텔레그램으로 받을 수 있습니다.
              </Typography>

              <form onSubmit={handleTelegramSettingsSave}>
                <TextField
                  fullWidth
                  label="텔레그램 봇 토큰"
                  value={telegramBotToken}
                  onChange={(e) => setTelegramBotToken(e.target.value)}
                  margin="normal"
                  placeholder="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
                  disabled={telegramLoading}
                  helperText="BotFather에서 발급받은 봇 토큰"
                />
                <TextField
                  fullWidth
                  label="텔레그램 채팅방 ID"
                  value={telegramChatId}
                  onChange={(e) => setTelegramChatId(e.target.value)}
                  margin="normal"
                  placeholder="123456789"
                  disabled={telegramLoading}
                  helperText="알림을 받을 채팅방 또는 사용자 ID (아래 목록에서 선택 가능)"
                />
                <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                  <Button
                    type="submit"
                    variant="contained"
                    disabled={telegramLoading}
                  >
                    {telegramLoading ? '저장 중...' : '설정 저장'}
                  </Button>
                  <Button
                    variant="outlined"
                    onClick={handleTestTelegram}
                    disabled={telegramLoading}
                  >
                    테스트 알림 전송
                  </Button>
                </Box>
              </form>

              {/* 대화자 목록 */}
              <Divider sx={{ my: 3 }} />

              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="subtitle1" fontWeight="bold">
                  봇에 대화한 사용자/채팅방 목록
                </Typography>
                <Tooltip title="목록 새로고침">
                  <IconButton
                    onClick={loadTelegramChats}
                    disabled={chatsLoading || !telegramBotToken}
                    size="small"
                  >
                    {chatsLoading ? <CircularProgress size={20} /> : <RefreshIcon />}
                  </IconButton>
                </Tooltip>
              </Box>

              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                봇에게 메시지를 보낸 사용자/채팅방이 표시됩니다. 클릭하여 선택하거나 ID를 복사할 수 있습니다.
              </Typography>

              {!telegramBotToken ? (
                <Alert severity="info" sx={{ mt: 1 }}>
                  봇 토큰을 먼저 입력하고 저장해주세요.
                </Alert>
              ) : telegramChats.length === 0 && !chatsLoading ? (
                <Alert severity="info" sx={{ mt: 1 }}>
                  아직 봇에게 대화한 사용자가 없습니다. 텔레그램에서 봇에게 아무 메시지나 보내보세요.
                </Alert>
              ) : (
                <List sx={{ bgcolor: 'background.paper', borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
                  {telegramChats.map((chat, index) => (
                    <ListItem
                      key={chat.chat_id}
                      divider={index < telegramChats.length - 1}
                      sx={{
                        cursor: 'pointer',
                        bgcolor: chat.chat_id === telegramChatId ? 'action.selected' : 'inherit',
                        '&:hover': { bgcolor: 'action.hover' }
                      }}
                      onClick={() => handleSelectChat(chat.chat_id)}
                    >
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            <Typography variant="body1" fontWeight={chat.is_current ? 'bold' : 'normal'}>
                              {chat.name}
                            </Typography>
                            {chat.username && (
                              <Typography variant="body2" color="text.secondary">
                                @{chat.username}
                              </Typography>
                            )}
                            <Chip
                              label={chat.type === 'private' ? '개인' : chat.type === 'group' || chat.type === 'supergroup' ? '그룹' : '채널'}
                              size="small"
                              color={chat.type === 'private' ? 'primary' : 'default'}
                              variant="outlined"
                            />
                            {chat.is_current && (
                              <Chip label="현재 선택됨" size="small" color="success" />
                            )}
                          </Box>
                        }
                        secondary={
                          <Typography variant="body2" color="text.secondary" component="span" sx={{ fontFamily: 'monospace' }}>
                            Chat ID: {chat.chat_id}
                          </Typography>
                        }
                      />
                      <ListItemSecondaryAction>
                        <Tooltip title={copiedId === chat.chat_id ? '복사됨!' : 'Chat ID 복사'}>
                          <IconButton
                            edge="end"
                            onClick={(e) => {
                              e.stopPropagation()
                              handleCopyChatId(chat.chat_id)
                            }}
                            color={copiedId === chat.chat_id ? 'success' : 'default'}
                          >
                            {copiedId === chat.chat_id ? <CheckIcon /> : <CopyIcon />}
                          </IconButton>
                        </Tooltip>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  )
}

export default Settings
