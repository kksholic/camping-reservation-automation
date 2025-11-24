import React, { useState, useEffect } from 'react'
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom'
import { ThemeProvider, createTheme } from '@mui/material/styles'
import { CssBaseline, Box, AppBar, Toolbar, Typography, Container, IconButton, Menu, MenuItem } from '@mui/material'
import { AccountCircle } from '@mui/icons-material'
import Dashboard from './pages/Dashboard'
import CampingSites from './pages/CampingSites'
import Monitoring from './pages/Monitoring'
import Reservations from './pages/Reservations'
import SiteSelection from './pages/SiteSelection'
import Settings from './pages/Settings'
import Login from './pages/Login'
import Navigation from './components/Navigation'
import { checkAuth, logout } from './services/api'

const theme = createTheme({
  palette: {
    primary: {
      main: '#2e7d32',
    },
    secondary: {
      main: '#ff6f00',
    },
  },
})

function PrivateRoute({ children, isAuthenticated }) {
  return isAuthenticated ? children : <Navigate to="/login" />
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [username, setUsername] = useState('')
  const [loading, setLoading] = useState(true)
  const [anchorEl, setAnchorEl] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    // 페이지 로드 시 인증 상태 확인
    checkAuth()
      .then(data => {
        setIsAuthenticated(data.authenticated)
        setUsername(data.username || '')
      })
      .catch(() => {
        setIsAuthenticated(false)
      })
      .finally(() => {
        setLoading(false)
      })
  }, [])

  const handleLogin = () => {
    setIsAuthenticated(true)
    checkAuth().then(data => {
      setUsername(data.username || '')
    })
  }

  const handleUsernameChange = (newUsername) => {
    setUsername(newUsername)
  }

  const handleLogout = async () => {
    try {
      await logout()
      setIsAuthenticated(false)
      setUsername('')
      handleMenuClose()
      navigate('/login')
    } catch (error) {
      console.error('Logout failed:', error)
    }
  }

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  if (loading) {
    return null
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
        {isAuthenticated && (
          <>
            <AppBar position="static">
              <Toolbar>
                <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                  🏕️ 캠핑 예약 자동화 시스템
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Typography variant="body1" sx={{ mr: 1 }}>
                    {username}
                  </Typography>
                  <IconButton
                    size="large"
                    edge="end"
                    color="inherit"
                    onClick={handleMenuOpen}
                  >
                    <AccountCircle />
                  </IconButton>
                  <Menu
                    anchorEl={anchorEl}
                    open={Boolean(anchorEl)}
                    onClose={handleMenuClose}
                  >
                    <MenuItem onClick={handleLogout}>로그아웃</MenuItem>
                  </Menu>
                </Box>
              </Toolbar>
            </AppBar>

            <Box sx={{ display: 'flex', flexGrow: 1 }}>
              <Navigation />

              <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
                <Routes>
                  <Route path="/" element={<PrivateRoute isAuthenticated={isAuthenticated}><Dashboard /></PrivateRoute>} />
                  <Route path="/sites" element={<PrivateRoute isAuthenticated={isAuthenticated}><CampingSites /></PrivateRoute>} />
                  <Route path="/site-selection" element={<PrivateRoute isAuthenticated={isAuthenticated}><SiteSelection /></PrivateRoute>} />
                  <Route path="/monitoring" element={<PrivateRoute isAuthenticated={isAuthenticated}><Monitoring /></PrivateRoute>} />
                  <Route path="/reservations" element={<PrivateRoute isAuthenticated={isAuthenticated}><Reservations /></PrivateRoute>} />
                  <Route path="/settings" element={<PrivateRoute isAuthenticated={isAuthenticated}><Settings username={username} onUsernameChange={handleUsernameChange} /></PrivateRoute>} />
                  <Route path="/login" element={<Navigate to="/" />} />
                </Routes>
              </Container>
            </Box>
          </>
        )}

        {!isAuthenticated && (
          <Routes>
            <Route path="/login" element={<Login onLogin={handleLogin} />} />
            <Route path="*" element={<Navigate to="/login" />} />
          </Routes>
        )}
      </Box>
    </ThemeProvider>
  )
}

export default App
