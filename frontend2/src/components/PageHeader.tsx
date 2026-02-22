import { Box, Stack, Typography } from '@mui/material';
import type { TypographyProps } from '@mui/material';
import type { ReactNode } from 'react';

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  titleProps?: TypographyProps;
}

export function PageHeader({ title, subtitle, action, titleProps }: PageHeaderProps) {
  return (
    <Box
      sx={{
        mb: 4,
        pb: 3,
        borderBottom: '3px solid #1e40af',
        background: 'rgba(30, 64, 175, 0.05)',
        borderRadius: 2,
        p: 3,
        position: 'relative',
        overflow: 'hidden',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: '4px',
          backgroundColor: '#1e40af',
        },
      }}
    >
      <Stack direction={{ xs: 'column', sm: 'row' }} alignItems={{ xs: 'flex-start', sm: 'center' }} justifyContent="space-between" spacing={2}>
        <Stack spacing={0.5}>
          <Typography 
            variant="h4" 
            fontWeight={800}
            sx={{
              color: '#1e40af',
              letterSpacing: '-0.5px',
            }}
            {...titleProps}
          >
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="subtitle1" color="text.secondary" sx={{ fontWeight: 500 }}>
              {subtitle}
            </Typography>
          )}
        </Stack>
        {action}
      </Stack>
    </Box>
  );
}

export default PageHeader;
