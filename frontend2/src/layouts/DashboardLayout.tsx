import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
  AppBar,
  Box,
  Button,
  CssBaseline,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  Toolbar,
  Typography,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import LogoutIcon from '@mui/icons-material/Logout';
import { useAuth } from '../contexts/AuthContext';

const drawerWidth = 240;

const navItems = [
  { label: 'About', path: '/' },
  // { label: 'Database', path: '/database'},
  { label: 'Twilio Call Management', path: '/twilio-call-management' },
  { label: 'Twilio Database', path: '/twilio-database' },
  // { label: 'Call Management Demo Page', path: '/entry-dashboard-demo' },
  { label: 'Call Status Dashboard', path: '/call-status-dashboard' },
  { label: 'Admin Dashboard', path: '/admin-dashboard' },
];

export default function DashboardLayout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const { logout } = useAuth();
  const navigate = useNavigate();

  const handleDrawerToggle = () => {
    setMobileOpen((prev) => !prev);
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const drawer = (
    <div>
      <Toolbar
        sx={{
          background: '#1e40af',
          minHeight: '64px !important',
        }}
      >
        <Typography
          variant="h6"
          fontWeight={700}
          sx={{
            color: '#ffffff',
            textShadow: '0 2px 4px rgba(0,0,0,0.2)',
          }}
        >
          mHealth Admin
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {navItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              component={NavLink}
              to={item.path}
              end={item.path === '/'}
              onClick={() => setMobileOpen(false)}
              sx={{
                borderRadius: 1,
                mx: 1,
                my: 0.5,
                transition: 'all 0.3s ease',
                '&:hover': {
                  bgcolor: 'rgba(30, 64, 175, 0.08)',
                  transform: 'translateX(4px)',
                },
                '&.active': {
                  background: '#1e40af',
                  color: '#ffffff',
                  boxShadow: '0 2px 8px rgba(30, 64, 175, 0.3)',
                  '&:hover': {
                    background: '#1e3a8a',
                  },
                },
              }}
            >
              <ListItemText
                primary={item.label}
                primaryTypographyProps={{ fontWeight: 600 }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
      <Box sx={{ flexGrow: 1 }} />
      <Divider />
      <Box sx={{ p: 2 }}>
        <Button
          fullWidth
          variant="contained"
          startIcon={<LogoutIcon />}
          onClick={handleLogout}
          sx={{
            background: '#dc2626',
            color: '#ffffff',
            fontWeight: 600,
            boxShadow: '0 2px 8px rgba(239, 68, 68, 0.3)',
            '&:hover': {
              background: '#b91c1c',
              boxShadow: '0 4px 12px rgba(239, 68, 68, 0.4)',
            },
          }}
        >
          Logout
        </Button>
      </Box>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          background: '#1e40af',
          boxShadow: '0 4px 20px rgba(30, 64, 175, 0.15)',
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{
              fontWeight: 700,
              letterSpacing: '0.5px',
              textShadow: '0 2px 4px rgba(0,0,0,0.2)',
            }}
          >
            MHealth Platform
          </Typography>
        </Toolbar>
      </AppBar>
      <Box component="nav" sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', md: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: { xs: 3, md: 4 },
          width: { md: `calc(100% - ${drawerWidth}px)` },
          minHeight: '100vh',
          background: '#f8fafc',
        }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
