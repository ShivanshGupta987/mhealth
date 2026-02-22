import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
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
} from '@mui/material';
import { resetPassword, verifyResetToken } from '../api/auth';

export default function ResetPasswordWithTokenPage() {
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [email, setEmail] = useState('');
  const navigate = useNavigate();
  const { token } = useParams<{ token: string }>();

  useEffect(() => {
    const verifyToken = async () => {
      if (!token) {
        setError('Invalid reset link');
        setVerifying(false);
        return;
      }

      try {
        const result = await verifyResetToken(token);
        if (result.valid) {
          setTokenValid(true);
          setEmail(result.email || '');
        } else {
          setError(result.message || 'Invalid or expired reset link');
        }
      } catch (err: any) {
        setError('Failed to verify reset link');
      } finally {
        setVerifying(false);
      }
    };

    verifyToken();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    // Validation
    if (newPassword.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (!token) {
      setError('Invalid reset link');
      return;
    }

    setLoading(true);

    try {
      await resetPassword({
        token,
        new_password: newPassword,
      });

      setSuccess('Password reset successfully! Redirecting to login...');
      
      // Clear form
      setNewPassword('');
      setConfirmPassword('');

      // Redirect to login after 2 seconds
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  if (verifying) {
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
        <CircularProgress sx={{ color: '#1e40af' }} />
      </Box>
    );
  }

  if (!tokenValid) {
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
          }}
        >
          <CardContent sx={{ p: 4 }}>
            <Typography variant="h4" component="h1" gutterBottom fontWeight={700} color="error">
              Invalid Reset Link
            </Typography>
            <Alert severity="error" sx={{ mb: 3 }}>
              {error || 'This password reset link is invalid or has expired.'}
            </Alert>
            <Button
              variant="contained"
              fullWidth
              onClick={() => navigate('/forgot-password')}
            >
              Request New Reset Link
            </Button>
          </CardContent>
        </Card>
      </Box>
    );
  }

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
            Reset Password
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={1}>
            Email: <strong>{email}</strong>
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Enter your new password below
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
                label="New Password"
                type="password"
                fullWidth
                required
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                disabled={loading}
                helperText="Must be at least 6 characters"
                sx={{
                  '& .MuiOutlinedInput-root': {
                    background: 'rgba(248, 250, 252, 0.8)',
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
                  '& .MuiInputLabel-root.Mui-focused': {
                    color: '#1e40af',
                  },
                }}
              />
              <TextField
                label="Confirm New Password"
                type="password"
                fullWidth
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                disabled={loading}
                sx={{
                  '& .MuiOutlinedInput-root': {
                    background: 'rgba(248, 250, 252, 0.8)',
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
                  '& .MuiInputLabel-root.Mui-focused': {
                    color: '#1e40af',
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
                {loading ? <CircularProgress size={24} /> : 'Reset Password'}
              </Button>
            </Stack>
          </form>
        </CardContent>
      </Card>
    </Box>
  );
}
