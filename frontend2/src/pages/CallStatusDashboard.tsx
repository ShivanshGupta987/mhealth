import { useMemo } from 'react';
import { Alert, Box, Card, CardContent, Grid, Stack, Typography, Chip } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import PageHeader from '../components/PageHeader';
import LoadingState from '../components/LoadingState';
import { listTargets, listCalls, listFlaggedTargetsRaw, type TargetRecord, type CallRecord, type FlaggedTargetRecord } from '../api/database';

function Stat({ label, value, color }: { label: string; value: string | number; color?: string }) {
  return (
    <Card
      sx={{
        height: '100%',
        background: '#ffffff',
        borderLeft: `4px solid ${color || '#144d63'}`,
      }}
    >
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

export default function MetricsPage() {
  const targetsQuery = useQuery<TargetRecord[]>({ queryKey: ['db-targets'], queryFn: listTargets });
  const callsQuery = useQuery<CallRecord[]>({ queryKey: ['db-calls'], queryFn: listCalls });
  const flaggedQuery = useQuery<FlaggedTargetRecord[]>({ queryKey: ['db-flagged'], queryFn: listFlaggedTargetsRaw });

  const now = Date.now();
  const since24h = now - 24 * 60 * 60 * 1000;
  const parseDate = (value?: string | null) => {
    if (!value) return null;
    const d = new Date(value);
    return Number.isNaN(d.getTime()) ? null : d.getTime();
  };

  const targetStats = useMemo(() => {
    const rows = targetsQuery.data ?? [];
    return {
      total: rows.length,
    };
  }, [targetsQuery.data]);

  const flaggedStats = useMemo(() => {
    const rows = flaggedQuery.data ?? [];
    const flaggedLast24h = rows.reduce((acc, row) => {
      const ts = parseDate((row as any).Call_Scheduled_DateTime);
      return ts && ts >= since24h ? acc + 1 : acc;
    }, 0);
    return {
      total: rows.length,
      last24h: flaggedLast24h,
    };
  }, [flaggedQuery.data, since24h]);

  // Groups to show on metrics (match Entry Dashboard labels)
  const STATUS_GROUPS = [
    'Call Scheduled',
    'Call Made But Not Picked',
    'Call hungup with short communication',
    'Call hungup with communication',
    'Call Failed',
  ];

  const hiddenStatuses = ['awaiting schedule'];

  const callStats = useMemo(() => {
    const rows = callsQuery.data ?? [];
    const statuses: Record<string, number> = {};
    const grouped: Record<string, number> = {};
    STATUS_GROUPS.forEach((g) => { grouped[g] = 0; });
    const targets = new Set<string>();
    const models = new Set<string>();
    let last24h = 0;
    rows.forEach((c) => {
      const rawStatus = (c.Status || 'unknown').toString().trim();
      const statusKey = rawStatus.toLowerCase();
      statuses[statusKey] = (statuses[statusKey] || 0) + 1;
      // map raw status to grouped label used in EntryDashboard
      const s = statusKey;
      let group = '';
      if (s.includes('scheduled')) group = 'Call Scheduled';
      else if (s === 'busy' || s === 'no-answer' || s.includes('not picked')) group = 'Call Made But Not Picked';
      else if (s.includes('not conveyed')) group = 'Call hungup with short communication';
      else if (s.includes('conveyed') || s.includes('processed') || s.includes('message conveyed')) group = 'Call hungup with communication';
      else if (s.includes('failed') || s.includes('processing failed')) group = 'Call Failed';
      else group = statusKey;
      if (grouped[group] === undefined) grouped[group] = 0;
      grouped[group] += 1;
      if (c.Target_Id) targets.add(c.Target_Id);
      if (c.Model_Id) models.add(c.Model_Id);
      const ts = parseDate((c as any).Started_Time || c.Scheduled_Time as any);
      if (ts && ts >= since24h) last24h += 1;
    });

    // no-op: ensure objects exist (grouped already initialized above)

    return {
      total: rows.length,
      statuses,
      grouped,
      targets: targets.size,
      models: models.size,
      last24h,
    };
  }, [callsQuery.data, since24h]);

  const formatStatusLabel = (label: string) => {
    if (label.toLowerCase() === 'message not conveyed') return 'Message not conveyed';
    return label;
  };

  const isLoading = targetsQuery.isLoading || callsQuery.isLoading || flaggedQuery.isLoading;
  const hasError = targetsQuery.error || callsQuery.error || flaggedQuery.error;

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
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={700} gutterBottom sx={{ mb: 2 }}>
                  Recipients Metrics
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={4}>
                    <Stat label="Total call recipients" value={targetStats.total} color="#144d63" />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Stat label="Predicted as depressed by ML model" value={flaggedStats.total} color="#f4a261" />
                  </Grid>
                  <Grid item xs={12} md={4}>
                    <Stat label="Predicted as depressed (Last 24h)" value={flaggedStats.last24h} color="#e76f51" />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={700} gutterBottom sx={{ mb: 2 }}>
                  Calls Metrics
                </Typography>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Stat label="Total calls made" value={callStats.total} color="#144d63" />
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Stat label="Calls made (Last 24h)" value={callStats.last24h} color="#2a9d8f" />
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" fontWeight={700} gutterBottom sx={{ mb: 2 }}>
                  Calls by Status
                </Typography>
                <Grid container spacing={2}>
                  {(() => {
                    const grouped = callStats.grouped || {};
                    const extra = Object.keys(grouped).filter((k) => !STATUS_GROUPS.includes(k) && !hiddenStatuses.includes(k));
                    const keys = [...STATUS_GROUPS, ...extra];
                    const statusColors: Record<string, string> = {
                      'Call Scheduled': '#f59e0b',
                      'Call Made But Not Picked': '#ef4444',
                      'Call hungup with short communication': '#8b5cf6',
                      'Call hungup with communication': '#10b981',
                      'Call Failed': '#dc2626',
                    };
                    return keys.map((g) => (
                      <Grid item xs={12} sm={6} md={4} lg={2.4} key={g}>
                        <Stat label={g} value={grouped[g] ?? 0} color={statusColors[g] || '#6b7280'} />
                      </Grid>
                    ));
                  })()}
                </Grid>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
}
