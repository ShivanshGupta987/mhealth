import { useQuery } from '@tanstack/react-query';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import PageHeader from '../components/PageHeader';
import StatCard from '../components/StatCard';
import LoadingState from '../components/LoadingState';
import EmptyState from '../components/EmptyState';
import { fetchConfigInfo, fetchRootInfo } from '../api/systemHealth';
import MaterialGrid from '@mui/material/Grid';
const Grid = MaterialGrid as any;

function formatBool(value?: boolean) {
  if (value === undefined) return 'Unknown';
  return value ? 'Online' : 'Check';
}

export default function SystemHealthPage() {
  const rootQuery = useQuery({ queryKey: ['system-root'], queryFn: fetchRootInfo });
  const configQuery = useQuery({ queryKey: ['system-config'], queryFn: fetchConfigInfo });

  const apiStatusOk = Boolean(rootQuery.data && rootQuery.data.status === 'operational');
  const minioOk = Boolean(configQuery.data?.minio_connected);
  const exotelConfigured = Boolean(configQuery.data?.exotel_sid && configQuery.data?.exotel_sid !== 'NOT SET');
  const webhooksReady = Boolean(configQuery.data?.webhook_urls && Object.keys(configQuery.data.webhook_urls).length > 0);

  return (
    <Box>
      <PageHeader title="Admin Dashboard" subtitle="Monitor API availability, storage, and Exotel configuration." />

      <Card 
        sx={{ 
          mb: 3,
          background: 'rgba(30, 64, 175, 0.08)',
          borderLeft: '4px solid #1e40af',
        }}
      >
        <CardContent>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="subtitle1" fontWeight={700} sx={{
              color: '#1e40af',
            }}>
              Status Overview
            </Typography>
            <Stack direction="row" spacing={1}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={() => {
                  rootQuery.refetch();
                  configQuery.refetch();
                }}
                disabled={rootQuery.isFetching || configQuery.isFetching}
              >
                Refresh
              </Button>
              <Typography variant="body2" color="text.secondary">
                Backend: {import.meta.env.VITE_API_URL || 'http://localhost:8000'}
              </Typography>
            </Stack>
          </Stack>
        </CardContent>
      </Card>

      {(rootQuery.error || configQuery.error) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load health info. {String(rootQuery.error || configQuery.error)}
        </Alert>
      )}

      {(rootQuery.isLoading || configQuery.isLoading) && <LoadingState label="Checking services…" />}

      {!rootQuery.isLoading && !configQuery.isLoading && (
        <Grid container spacing={3} mb={3}>
          <Grid xs={12} md={3}>
            <StatCard 
              label="API Status" 
              value={apiStatusOk ? 'Online' : 'Offline'} 
              helperText="Root endpoint" 
              status={apiStatusOk ? 'online' : 'offline'}
            />
          </Grid>
          <Grid xs={12} md={3}>
            <StatCard 
              label="MinIO" 
              value={minioOk ? 'Online' : 'Check'} 
              helperText="Recording storage" 
              status={minioOk ? 'online' : 'offline'}
            />
          </Grid>
          <Grid xs={12} md={3}>
            <StatCard 
              label="Exotel SID" 
              value={exotelConfigured ? 'Configured' : 'Not Set'} 
              helperText="Credentials configured" 
              status={exotelConfigured ? 'online' : 'warning'}
            />
          </Grid>
          <Grid xs={12} md={3}>
            <StatCard 
              label="Webhooks" 
              value={webhooksReady ? 'Ready' : 'Not Ready'} 
              helperText="URL generation" 
              status={webhooksReady ? 'online' : 'warning'}
            />
          </Grid>
        </Grid>
      )}

      <Grid container spacing={2}>
        <Grid xs={12} md={6}>
          <Card 
            sx={{ 
              mb: 2,
              background: 'rgba(20, 77, 99, 0.05)',
              borderLeft: '4px solid #144d63',
            }}
          >
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight={700} color="#144d63">
                Configuration Overview
              </Typography>
              {configQuery.data ? (
                <Table size="small">
                  <TableBody>
                    {Object.entries(configQuery.data)
                      .filter(([, value]) => typeof value !== 'object')
                      .map(([key, value]) => (
                        <TableRow key={key}>
                          <TableCell sx={{ fontWeight: 600 }}>{key.replaceAll('_', ' ')}</TableCell>
                          <TableCell>{String(value)}</TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              ) : (
                <EmptyState title="No data" description="Configuration endpoint unavailable." />
              )}
            </CardContent>
          </Card>
        </Grid>

        <Grid xs={12} md={6}>
          <Card 
            sx={{ 
              mb: 2,
              background: 'rgba(244, 162, 97, 0.05)',
              borderLeft: '4px solid #f4a261',
            }}
          >
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight={700} color="#f4a261">
                Webhook URLs
              </Typography>
              {configQuery.data?.webhook_urls && Object.keys(configQuery.data.webhook_urls).length > 0 ? (
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Webhook</TableCell>
                      <TableCell>URL</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(configQuery.data.webhook_urls).map(([key, value]) => (
                      <TableRow key={key}>
                        <TableCell sx={{ fontWeight: 600 }}>{key}</TableCell>
                        <TableCell>{String(value)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <EmptyState title="No webhooks" description="Webhook URLs not configured." />
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={2}>
        <Grid xs={12}>
          <Card
            sx={{
              background: 'rgba(42, 157, 143, 0.05)',
              borderLeft: '4px solid #2a9d8f',
            }}
          >
            <CardContent>
              <Typography variant="h6" gutterBottom fontWeight={700} color="#2a9d8f">
                API Root Response
              </Typography>
              {rootQuery.data ? (
                <Box sx={{ 
                  bgcolor: 'rgba(42, 157, 143, 0.1)', 
                  border: '1px solid rgba(42, 157, 143, 0.3)',
                  color: '#0a2a38', 
                  p: 2, 
                  borderRadius: 1, 
                  fontFamily: 'monospace', 
                  fontSize: 12, 
                  overflow: 'auto',
                  maxHeight: 400,
                }}>
                  {JSON.stringify(rootQuery.data, null, 2)}
                </Box>
              ) : (
                <EmptyState title="No response" description="Root endpoint unreachable." />
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}
