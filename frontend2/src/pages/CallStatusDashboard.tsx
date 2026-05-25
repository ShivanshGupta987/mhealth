import { useMemo } from 'react';
import { Alert, Box, Card, CardContent, Grid, Stack, Typography } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import PageHeader from '../components/PageHeader';
import LoadingState from '../components/LoadingState';
import { twilioDB_listTargets, twilioDB_listCalls, type TwilioDbTarget, type TwilioDbCall } from '../api/twilioDatabase';

function Stat({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <Card sx={{ height: '100%', background: '#ffffff', borderLeft: `4px solid ${color || '#144d63'}` }}>
      <CardContent>
        <Stack spacing={1}>
          <Typography variant="body2" color="text.secondary" fontWeight={600}>
            {label}
          </Typography>
          <Typography variant="h4" fontWeight={700} color={color || 'primary.main'}>
            {value}
          </Typography>
        </Stack>
      </CardContent>
    </Card>
  );
}

// Display groups derived from Twilio DB statuses + call duration logic
const STATUS_GROUPS = [
  'Call Scheduled',
  'Call Initiated',
  'In Progress',
  'Call made but not picked',
  'Call hungup with short communication',
  'Call hungup with communication',
  'Call failed',
];

const STATUS_COLORS: Record<string, string> = {
  'Call Scheduled':                       '#f59e0b',
  'Call Initiated':                       '#3b82f6',
  'In Progress':                          '#6366f1',
  'Call made but not picked':             '#ef4444',
  'Call hungup with short communication': '#8b5cf6',
  'Call hungup with communication':       '#10b981',
  'Call failed':                          '#dc2626',
};

// total_response_duration is in seconds; 3 min = 180s
function groupStatus(status: string, totalResponseDuration: number | null): string {
  const s = (status || '').trim();
  if (s === 'No Answer' || s === 'Busy')   return 'Call made but not picked';
  if (s === 'Completed') {
    return (totalResponseDuration ?? 0) >= 180
      ? 'Call hungup with communication'
      : 'Call hungup with short communication';
  }
  if (s === 'Failed')    return 'Call failed';
  if (s === 'Cancelled') return '';   // hidden
  return s;
}

export default function CallStatusDashboard() {
  const targetsQuery = useQuery<TwilioDbTarget[]>({
    queryKey: ['twilio-targets'],
    queryFn: twilioDB_listTargets,
  });
  const callsQuery = useQuery<TwilioDbCall[]>({
    queryKey: ['twilio-calls'],
    queryFn: twilioDB_listCalls,
  });

  const now = Date.now();
  const since24h = now - 24 * 60 * 60 * 1000;

  const parseDate = (value?: string | null) => {
    if (!value) return null;
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? null : d.getTime();
  };

  const targetStats = useMemo(() => ({
    total: (targetsQuery.data ?? []).length,
  }), [targetsQuery.data]);

  const flaggedStats = useMemo(() => {
    const rows = callsQuery.data ?? [];
    const depressedAll = new Set<string>();
    const depressed24h = new Set<string>();
    rows.forEach((c) => {
      if (c.depression_risk === 1 && c.target_id) {
        depressedAll.add(c.target_id);
        const ts = parseDate(c.depression_analysis_timestamp ?? c.scheduled_time);
        if (ts && ts >= since24h) depressed24h.add(c.target_id);
      }
    });
    return { total: depressedAll.size, last24h: depressed24h.size };
  }, [callsQuery.data, since24h]);

  const callStats = useMemo(() => {
    const rows = callsQuery.data ?? [];
    const grouped: Record<string, number> = {};
    STATUS_GROUPS.forEach((g) => { grouped[g] = 0; });
    let last24h = 0;
    rows.forEach((c) => {
      const group = groupStatus(c.status, c.total_response_duration);
      if (group) grouped[group] = (grouped[group] ?? 0) + 1;
      const ts = parseDate(c.started_time ?? c.scheduled_time);
      if (ts && ts >= since24h) last24h += 1;
    });
    return { total: rows.length, grouped, last24h };
  }, [callsQuery.data, since24h]);

  const isLoading = targetsQuery.isLoading || callsQuery.isLoading;
  const hasError   = targetsQuery.error   || callsQuery.error;

  return (
    <Box>
      <PageHeader title="Call Status Dashboard" subtitle="Quick overview of call recipients and calls." />

      {hasError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load metrics. Please refresh.
        </Alert>
      )}

      {isLoading && <LoadingState label="Loading metrics…" />}

      {!isLoading && (
        <Grid container spacing={3}>
          <Grid size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={700} gutterBottom sx={{ mb: 2 }}>
                  Recipients Metrics
                </Typography>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <Stat label="Total call recipients" value={targetStats.total} color="#144d63" />
                  </Grid>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <Stat label="Predicted as depressed by ML model" value={flaggedStats.total} color="#f4a261" />
                  </Grid>
                  <Grid size={{ xs: 12, md: 4 }}>
                    <Stat label="Predicted as depressed (Last 24h)" value={flaggedStats.last24h} color="#e76f51" />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={700} gutterBottom sx={{ mb: 2 }}>
                  Calls Metrics
                </Typography>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Stat label="Total calls made" value={callStats.total} color="#144d63" />
                  </Grid>
                  <Grid size={{ xs: 12, md: 6 }}>
                    <Stat label="Calls made (Last 24h)" value={callStats.last24h} color="#2a9d8f" />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={700} gutterBottom sx={{ mb: 2 }}>
                  Calls by Status
                </Typography>
                <Grid container spacing={2}>
                  {STATUS_GROUPS.map((g) => (
                    <Grid size={{ xs: 12, sm: 6, md: 4, lg: 2.4 }} key={g}>
                      <Stat label={g} value={callStats.grouped[g] ?? 0} color={STATUS_COLORS[g]} />
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
}
