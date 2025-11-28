import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, Toolbar, Divider } from '@mui/material'
import DashboardIcon from '@mui/icons-material/Dashboard'
import CampingIcon from '@mui/icons-material/Forest'
import AutoIcon from '@mui/icons-material/SmartToy'
import BookingIcon from '@mui/icons-material/BookOnline'
import SettingsIcon from '@mui/icons-material/Settings'

const drawerWidth = 240

const menuItems = [
  { text: '대시보드', icon: <DashboardIcon />, path: '/' },
  { text: '캠핑장 관리', icon: <CampingIcon />, path: '/sites' },
  { text: '자동 예약', icon: <AutoIcon />, path: '/auto-reservation' },
  { text: '예약 내역', icon: <BookingIcon />, path: '/reservations' },
]

const settingsItems = [
  { text: '설정', icon: <SettingsIcon />, path: '/settings' },
]

export default function Navigation() {
  const location = useLocation()

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: drawerWidth,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: drawerWidth,
          boxSizing: 'border-box',
        },
      }}
    >
      <Toolbar />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Divider />
      <List>
        {settingsItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              component={Link}
              to={item.path}
              selected={location.pathname === item.path}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Drawer>
  )
}
