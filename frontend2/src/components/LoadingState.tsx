import { CircularProgress, Stack, Typography } from '@mui/material';

interface LoadingStateProps {
  label?: string;
}

export function LoadingState({ label = 'Loading data…' }: LoadingStateProps) {
  return (
    <Stack direction="row" spacing={2} alignItems="center" justifyContent="center" py={8}>
      <CircularProgress size={28} />
      <Typography variant="body1" color="text.secondary">
        {label}
      </Typography>
    </Stack>
  );
}

export default LoadingState;
