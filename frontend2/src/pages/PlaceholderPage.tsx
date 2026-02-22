import { Box, Typography } from '@mui/material';

interface PlaceholderPageProps {
  title: string;
  description?: string;
}

export function PlaceholderPage({ title, description = 'This view is under construction.' }: PlaceholderPageProps) {
  return (
    <Box textAlign="center" py={8}>
      <Typography variant="h4" gutterBottom>
        {title}
      </Typography>
      <Typography variant="body1" color="text.secondary">
        {description}
      </Typography>
    </Box>
  );
}

export default PlaceholderPage;
