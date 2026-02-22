import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Card,
  CardContent,
  TextField,
  Typography,
  Alert,
  Stack,
  CircularProgress,
  Link,
} from '@mui/material';
import { login } from '../api/auth';
import { useAuth } from '../contexts/AuthContext';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { login: authLogin } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await login({ email, password });
      // Store email for password reset functionality
      localStorage.setItem('userEmail', email);
      authLogin(response.access_token, response.admin_id);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box
      sx={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'rgba(30, 64, 175, 0.05)',
      }}
    >
      <Card 
        sx={{ 
          maxWidth: 400, 
          width: '100%', 
          mx: 2,
          background: '#ffffff',
          border: '1px solid',
          borderColor: 'rgba(30, 64, 175, 0.1)',
          boxShadow: '0 8px 32px rgba(30, 64, 175, 0.12)',
          transition: 'all 0.3s ease',
          '&:hover': {
            boxShadow: '0 12px 48px rgba(30, 64, 175, 0.18)',
            transform: 'translateY(-4px)',
          },
        }}
      >
        <CardContent sx={{ p: 4 }}>
          <Typography 
            variant="h4" 
            component="h1" 
            gutterBottom 
            align="center" 
            fontWeight={700}
            sx={{
              color: '#1e40af',
              mb: 1,
            }}
          >
            MHealth Admin
          </Typography>
          <Typography variant="body2" color="text.secondary" align="center" mb={3}>
            Sign in to access the dashboard
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <form onSubmit={handleSubmit}>
            <Stack spacing={2}>
              <TextField
                label="Email"
                type="email"
                fullWidth
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={loading}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    background: 'rgba(248, 250, 252, 0.8)',
                    borderRadius: 1,
                    '& fieldset': {
                      borderColor: 'rgba(30, 64, 175, 0.2)',
                      borderWidth: '1.5px',
                    },
                    '&:hover fieldset': {
                      borderColor: 'rgba(30, 64, 175, 0.4)',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#1e40af',
                      boxShadow: '0 0 0 3px rgba(30, 64, 175, 0.08)',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    fontWeight: 600,
                    '&.Mui-focused': {
                      color: '#1e40af',
                    },
                  },
                }}
              />
              <TextField
                label="Password"
                type="password"
                fullWidth
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    background: 'rgba(248, 250, 252, 0.8)',
                    borderRadius: 1,
                    '& fieldset': {
                      borderColor: 'rgba(30, 64, 175, 0.2)',
                      borderWidth: '1.5px',
                    },
                    '&:hover fieldset': {
                      borderColor: 'rgba(30, 64, 175, 0.4)',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#1e40af',
                      boxShadow: '0 0 0 3px rgba(30, 64, 175, 0.08)',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    fontWeight: 600,
                    '&.Mui-focused': {
                      color: '#1e40af',
                    },
                  },
                }}
              />
              <Button
                type="submit"
                variant="contained"
                fullWidth
                size="large"
                disabled={loading}
                sx={{ 
                  mt: 2,
                  background: '#1e40af',
                  fontWeight: 600,
                  fontSize: '1rem',
                  py: 1.5,
                  boxShadow: '0 4px 14px rgba(30, 64, 175, 0.25)',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    background: '#1e3a8a',
                    boxShadow: '0 6px 20px rgba(30, 64, 175, 0.35)',
                    transform: 'translateY(-2px)',
                  },
                  '&:disabled': {
                    background: 'rgba(30, 64, 175, 0.4)',
                  },
                }}
              >
                {loading ? <CircularProgress size={24} sx={{ color: 'white' }} /> : 'Sign In'}
              </Button>
            </Stack>
          </form>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Link
              component="button"
              variant="body2"
              onClick={() => navigate('/forgot-password')}
              sx={{ 
                cursor: 'pointer',
                fontWeight: 600,
                color: '#1e40af',
                textDecoration: 'none',
                '&:hover': {
                  textDecoration: 'underline',
                },
              }}
            >
              Forgot password?
            </Link>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
