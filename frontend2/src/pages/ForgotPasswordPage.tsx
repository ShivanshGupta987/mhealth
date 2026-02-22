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
import { forgotPassword } from '../api/auth';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');
    setLoading(true);

    try {
      await forgotPassword({ email });
      setSuccess('Password reset link has been sent to your email. Please check your inbox and spam folder.');
      setEmail('');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send reset email');
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
          maxWidth: 500, 
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
            fontWeight={700}
            sx={{
              color: '#1e40af',
              mb: 1,
            }}
          >
            Forgot Password
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Enter your email address and we'll send you a link to reset your password
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {success && (
            <Alert severity="success" sx={{ mb: 2 }}>
              {success}
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
                placeholder="Enter your email address"
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
                {loading ? <CircularProgress size={24} sx={{ color: 'white' }} /> : 'Send Reset Link'}
              </Button>
            </Stack>
          </form>

          <Box sx={{ mt: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Remember your password?{' '}
              <Link
                component="button"
                variant="body2"
                onClick={() => navigate('/login')}
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
                Back to Login
              </Link>
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
