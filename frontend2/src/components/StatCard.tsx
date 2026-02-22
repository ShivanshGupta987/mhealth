import { Card, CardContent, Stack, Typography, Box } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';

interface StatCardProps {
  label: string;
  value: string | number;
  helperText?: string;
  status?: 'online' | 'offline' | 'warning' | 'unknown';
}

export function StatCard({ label, value, helperText, status }: StatCardProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'online':
        return {
          bg: 'rgba(46, 125, 50, 0.08)',
          border: '#2e7d32',
          icon: <CheckCircleIcon sx={{ color: '#2e7d32', fontSize: 40 }} />,
          textColor: '#2e7d32',
        };
      case 'offline':
        return {
          bg: 'rgba(211, 47, 47, 0.08)',
          border: '#d32f2f',
          icon: <ErrorIcon sx={{ color: '#d32f2f', fontSize: 40 }} />,
          textColor: '#d32f2f',
        };
      case 'warning':
        return {
          bg: 'rgba(237, 108, 2, 0.08)',
          border: '#ed6c02',
          icon: <WarningIcon sx={{ color: '#ed6c02', fontSize: 40 }} />,
          textColor: '#ed6c02',
        };
      default:
        return {
          bg: 'rgba(158, 158, 158, 0.08)',
          border: '#9e9e9e',
          icon: <WarningIcon sx={{ color: '#9e9e9e', fontSize: 40 }} />,
          textColor: '#9e9e9e',
        };
    }
  };

  const statusStyle = getStatusColor();

  return (
    <Card 
      elevation={0} 
      sx={{ 
        border: '2px solid',
        borderColor: statusStyle.border,
        background: statusStyle.bg,
        transition: 'all 0.3s ease',
        height: '100%',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: `0 8px 24px ${statusStyle.border}40`,
        },
      }}
    >
      <CardContent>
        <Stack spacing={2}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="overline" color="text.secondary" fontWeight={600}>
              {label}
            </Typography>
            {status && statusStyle.icon}
          </Stack>
          <Typography variant="h4" fontWeight={700} color={statusStyle.textColor}>
            {value}
          </Typography>
          {helperText && (
            <Typography variant="body2" color="text.secondary">
              {helperText}
            </Typography>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}

export default StatCard;
