import React, { useState, useEffect } from 'react'
import {
  Box, Typography, Button, Paper, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, IconButton, Chip, Alert,
  Dialog, DialogTitle, DialogContent, List, ListItem, ListItemText,
  ListItemSecondaryAction, Badge, Tooltip
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import EditIcon from '@mui/icons-material/Edit'
import AddIcon from '@mui/icons-material/Add'
import PeopleIcon from '@mui/icons-material/People'
import ToggleOnIcon from '@mui/icons-material/ToggleOn'
import ToggleOffIcon from '@mui/icons-material/ToggleOff'
import { getCampingSites, createCampingSite, updateCampingSite, deleteCampingSite, getSiteAccounts, createSiteAccount, updateSiteAccount, deleteSiteAccount, toggleSiteAccount } from '../services/api'
import CampingSiteDialog from '../components/CampingSiteDialog'
import CampingSiteAccountDialog from '../components/CampingSiteAccountDialog'

export default function CampingSites() {
  const [sites, setSites] = useState([])
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedSite, setSelectedSite] = useState(null)
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')

  // 계정 관리 관련 상태
  const [accountsDialogOpen, setAccountsDialogOpen] = useState(false)
  const [selectedSiteForAccounts, setSelectedSiteForAccounts] = useState(null)
  const [accounts, setAccounts] = useState([])
  const [accountDialogOpen, setAccountDialogOpen] = useState(false)
  const [selectedAccount, setSelectedAccount] = useState(null)

  useEffect(() => {
    loadSites()
  }, [])

  const loadSites = async () => {
    try {
      const data = await getCampingSites()
      setSites(data)
    } catch (error) {
      console.error('Failed to load camping sites:', error)
      setError('캠핑장 목록을 불러오는데 실패했습니다')
    }
  }

  const handleAdd = () => {
    setSelectedSite(null)
    setDialogOpen(true)
  }

  const handleEdit = (site) => {
    setSelectedSite(site)
    setDialogOpen(true)
  }

  const handleSave = async (formData) => {
    try {
      if (selectedSite) {
        await updateCampingSite(selectedSite.id, formData)
        setSuccess('캠핑장 정보가 수정되었습니다')
      } else {
        await createCampingSite(formData)
        setSuccess('캠핑장이 추가되었습니다')
      }
      setDialogOpen(false)
      loadSites()
    } catch (error) {
      console.error('Failed to save camping site:', error)
      setError('캠핑장 저장에 실패했습니다')
    }
  }

  const handleDelete = async (id, name) => {
    if (window.confirm(`"${name}" 캠핑장을 삭제하시겠습니까?`)) {
      try {
        await deleteCampingSite(id)
        setSuccess('캠핑장이 삭제되었습니다')
        loadSites()
      } catch (error) {
        console.error('Failed to delete camping site:', error)
        setError('캠핑장 삭제에 실패했습니다')
      }
    }
  }

  // 계정 관리 함수들
  const handleManageAccounts = async (site) => {
    setSelectedSiteForAccounts(site)
    setAccountsDialogOpen(true)
    await loadAccounts(site.id)
  }

  const loadAccounts = async (siteId) => {
    try {
      const data = await getSiteAccounts(siteId)
      setAccounts(data)
    } catch (error) {
      console.error('Failed to load accounts:', error)
      setError('계정 목록을 불러오는데 실패했습니다')
    }
  }

  const handleAddAccount = () => {
    setSelectedAccount(null)
    setAccountDialogOpen(true)
  }

  const handleEditAccount = (account) => {
    setSelectedAccount(account)
    setAccountDialogOpen(true)
  }

  const handleSaveAccount = async (formData) => {
    try {
      if (selectedAccount) {
        await updateSiteAccount(selectedSiteForAccounts.id, selectedAccount.id, formData)
        setSuccess('계정 정보가 수정되었습니다')
      } else {
        await createSiteAccount(selectedSiteForAccounts.id, formData)
        setSuccess('계정이 추가되었습니다')
      }
      setAccountDialogOpen(false)
      await loadAccounts(selectedSiteForAccounts.id)
    } catch (error) {
      console.error('Failed to save account:', error)
      setError(error.response?.data?.message || '계정 저장에 실패했습니다')
    }
  }

  const handleDeleteAccount = async (accountId, username) => {
    if (window.confirm(`"${username}" 계정을 삭제하시겠습니까?`)) {
      try {
        await deleteSiteAccount(selectedSiteForAccounts.id, accountId)
        setSuccess('계정이 삭제되었습니다')
        await loadAccounts(selectedSiteForAccounts.id)
        loadSites() // 메인 테이블의 계정 수 업데이트
      } catch (error) {
        console.error('Failed to delete account:', error)
        setError('계정 삭제에 실패했습니다')
      }
    }
  }

  const handleToggleAccount = async (accountId) => {
    try {
      const result = await toggleSiteAccount(selectedSiteForAccounts.id, accountId)
      setSuccess(result.message)
      await loadAccounts(selectedSiteForAccounts.id)
    } catch (error) {
      console.error('Failed to toggle account:', error)
      setError('계정 활성화 토글에 실패했습니다')
    }
  }

  const getStatusChip = (site) => {
    const hasLogin = site.login_username && site.login_password
    const hasBooker = site.booker_name && site.booker_phone

    if (hasLogin && hasBooker) {
      return <Chip label="완료" color="success" size="small" />
    } else if (hasLogin || hasBooker) {
      return <Chip label="부분" color="warning" size="small" />
    } else {
      return <Chip label="미설정" color="default" size="small" />
    }
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">
          캠핑장 관리
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAdd}
        >
          캠핑장 추가
        </Button>
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

      <Alert severity="info" sx={{ mb: 2 }}>
        캠핑장과 예약에 사용할 계정을 등록하세요. 예약은 "자동 예약" 메뉴에서 진행합니다.
      </Alert>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>ID</TableCell>
              <TableCell>캠핑장 이름</TableCell>
              <TableCell>URL</TableCell>
              <TableCell>설정 상태</TableCell>
              <TableCell>계정 수</TableCell>
              <TableCell>로그인 ID</TableCell>
              <TableCell>예약자 이름</TableCell>
              <TableCell>전화번호</TableCell>
              <TableCell>차량번호</TableCell>
              <TableCell>등록일</TableCell>
              <TableCell align="right">작업</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sites.length === 0 ? (
              <TableRow>
                <TableCell colSpan={11} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 4 }}>
                    등록된 캠핑장이 없습니다. "캠핑장 추가" 버튼을 눌러 추가하세요.
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              sites.map((site) => (
                <TableRow key={site.id} hover>
                  <TableCell>{site.id}</TableCell>
                  <TableCell>
                    <Typography variant="body2" fontWeight="bold">
                      {site.name}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2" sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {site.url}
                    </Typography>
                  </TableCell>
                  <TableCell>{getStatusChip(site)}</TableCell>
                  <TableCell>
                    <Tooltip title="계정 관리">
                      <Badge badgeContent={site.accounts_count || 0} color="primary">
                        <IconButton
                          onClick={() => handleManageAccounts(site)}
                          color="info"
                          size="small"
                        >
                          <PeopleIcon />
                        </IconButton>
                      </Badge>
                    </Tooltip>
                  </TableCell>
                  <TableCell>{site.login_username || '-'}</TableCell>
                  <TableCell>{site.booker_name || '-'}</TableCell>
                  <TableCell>{site.booker_phone || '-'}</TableCell>
                  <TableCell>{site.booker_car_number || '-'}</TableCell>
                  <TableCell>{new Date(site.created_at).toLocaleDateString()}</TableCell>
                  <TableCell align="right">
                    <IconButton onClick={() => handleEdit(site)} color="primary" size="small">
                      <EditIcon />
                    </IconButton>
                    <IconButton onClick={() => handleDelete(site.id, site.name)} color="error" size="small">
                      <DeleteIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 캠핑장 추가/수정 다이얼로그 */}
      <CampingSiteDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSave={handleSave}
        site={selectedSite}
      />

      {/* 계정 목록 다이얼로그 */}
      <Dialog
        open={accountsDialogOpen}
        onClose={() => setAccountsDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" justifyContent="space-between" alignItems="center">
            <span>{selectedSiteForAccounts?.name} - 계정 관리</span>
            <Button
              variant="contained"
              size="small"
              startIcon={<AddIcon />}
              onClick={handleAddAccount}
            >
              계정 추가
            </Button>
          </Box>
        </DialogTitle>
        <DialogContent>
          {accounts.length === 0 ? (
            <Box py={4} textAlign="center">
              <Typography variant="body2" color="text.secondary">
                등록된 계정이 없습니다. "계정 추가" 버튼을 눌러 추가하세요.
              </Typography>
            </Box>
          ) : (
            <List>
              {accounts.map((account) => (
                <ListItem
                  key={account.id}
                  sx={{
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 1,
                    backgroundColor: account.is_active ? 'background.paper' : 'action.disabledBackground'
                  }}
                >
                  <ListItemText
                    primary={
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="body1" fontWeight="bold">
                          {account.nickname || `계정 ${account.id}`}
                        </Typography>
                        <Chip
                          label={`우선순위: ${account.priority}`}
                          size="small"
                          variant="outlined"
                        />
                        <Chip
                          label={account.is_active ? '활성' : '비활성'}
                          size="small"
                          color={account.is_active ? 'success' : 'default'}
                        />
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2">
                          로그인: {account.login_username}
                        </Typography>
                        <Typography variant="body2">
                          예약자: {account.booker_name} / {account.booker_phone}
                          {account.booker_car_number && ` / 차량: ${account.booker_car_number}`}
                        </Typography>
                      </Box>
                    }
                  />
                  <ListItemSecondaryAction>
                    <Tooltip title={account.is_active ? '비활성화' : '활성화'}>
                      <IconButton
                        onClick={() => handleToggleAccount(account.id)}
                        color={account.is_active ? 'success' : 'default'}
                        size="small"
                      >
                        {account.is_active ? <ToggleOnIcon /> : <ToggleOffIcon />}
                      </IconButton>
                    </Tooltip>
                    <IconButton
                      onClick={() => handleEditAccount(account)}
                      color="primary"
                      size="small"
                    >
                      <EditIcon />
                    </IconButton>
                    <IconButton
                      onClick={() => handleDeleteAccount(account.id, account.login_username)}
                      color="error"
                      size="small"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          )}

          <Alert severity="info" sx={{ mt: 2 }}>
            계정 등록 후 "자동 예약" 메뉴에서 예약을 진행하세요.
          </Alert>
        </DialogContent>
      </Dialog>

      {/* 계정 추가/수정 다이얼로그 */}
      <CampingSiteAccountDialog
        open={accountDialogOpen}
        onClose={() => setAccountDialogOpen(false)}
        onSave={handleSaveAccount}
        account={selectedAccount}
        siteName={selectedSiteForAccounts?.name}
      />
    </Box>
  )
}
