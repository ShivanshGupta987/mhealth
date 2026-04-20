import { useMemo, useState } from 'react';
import type { ReactNode } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
} from '@mui/material';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import PageHeader from '../components/PageHeader';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
  twilioDB_listTargets,
  twilioDB_createTarget,
  twilioDB_deleteTarget,
  twilioDB_listCalls,
  twilioDB_deleteCall,
  twilioDB_listResponses,
  twilioDB_deleteResponse,
} from '../api/twilioDatabase';
import type { TwilioDbTarget, TwilioDbCall, TwilioDbResponse } from '../api/twilioDatabase';

// ── Accent colour matching TwilioCallManagementPage ───────────────────────
const ACCENT = '#0d9488';

// ── Generic sortable table ─────────────────────────────────────────────────
function SimpleTable<T extends Record<string, unknown>>(props: {
  rows: T[];
  columns: { key: keyof T; label: string }[];
  getRowId?: (row: T, index: number) => string;
  actions?: (row: T) => ReactNode;
}) {
  const { rows, columns, getRowId, actions } = props;
  const [sortKey, setSortKey] = useState<keyof T | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');

  const sortedRows = useMemo(() => {
    if (!sortKey) return rows;
    return [...rows].sort((a, b) => {
      const av = a[sortKey];
      const bv = b[sortKey];
      if (av == null && bv == null) return 0;
      if (av == null) return 1;
      if (bv == null) return -1;
      if (typeof av === 'number' && typeof bv === 'number')
        return sortDir === 'asc' ? av - bv : bv - av;
      const as = String(av).toLowerCase();
      const bs = String(bv).toLowerCase();
      if (as < bs) return sortDir === 'asc' ? -1 : 1;
      if (as > bs) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [rows, sortKey, sortDir]);

  const handleSort = (key: keyof T) => {
    if (sortKey === key) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('asc'); }
  };

  return (
    <Box sx={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
        <thead>
          <tr style={{ background: `${ACCENT}14` }}>
            {columns.map((col) => {
              const active = sortKey === col.key;
              return (
                <th
                  key={String(col.key)}
                  onClick={() => handleSort(col.key)}
                  style={{ textAlign: 'left', padding: '8px 10px', borderBottom: '2px solid #e2e8f0', cursor: 'pointer', userSelect: 'none', fontWeight: 700, color: '#1f2937' }}
                >
                  <Stack direction="row" spacing={0.5} alignItems="center">
                    <span>{col.label}</span>
                    {active
                      ? (sortDir === 'asc' ? <ArrowUpwardIcon sx={{ fontSize: 14 }} /> : <ArrowDownwardIcon sx={{ fontSize: 14 }} />)
                      : <ArrowUpwardIcon sx={{ fontSize: 14, opacity: 0.3 }} />
                    }
                  </Stack>
                </th>
              );
            })}
            {actions && <th style={{ width: 80, padding: '8px 10px', fontWeight: 700, color: '#1f2937' }}>Actions</th>}
          </tr>
        </thead>
        <tbody>
          {sortedRows.length === 0 && (
            <tr>
              <td colSpan={columns.length + (actions ? 1 : 0)} style={{ padding: '20px', textAlign: 'center', color: '#9ca3af' }}>
                No records found.
              </td>
            </tr>
          )}
          {sortedRows.map((row, index) => {
            const id = getRowId ? getRowId(row, index) : String((row as any).id ?? index);
            return (
              <tr key={id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                {columns.map((col) => (
                  <td key={String(col.key)} style={{ padding: '7px 10px', maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {String(row[col.key] ?? '—')}
                  </td>
                ))}
                {actions && <td style={{ padding: '7px 10px' }}>{actions(row)}</td>}
              </tr>
            );
          })}
        </tbody>
      </table>
    </Box>
  );
}

// ── Helper ─────────────────────────────────────────────────────────────────
function QueryStatus({ isLoading, error }: { isLoading: boolean; error: unknown }) {
  if (isLoading) return <Stack direction="row" spacing={1} alignItems="center" sx={{ py: 3, pl: 1 }}><CircularProgress size={18} sx={{ color: ACCENT }} /><Typography variant="body2">Loading…</Typography></Stack>;
  if (error) return <Alert severity="error" sx={{ my: 1 }}>{String((error as any)?.message ?? error)}</Alert>;
  return null;
}

// ── Main page ──────────────────────────────────────────────────────────────
type TabKey = 'targets' | 'calls' | 'responses';

type TargetForm = { name: string; phone_no: string; roll_no: string; department: string; program: string };

export default function TwilioDatabasePage() {
  const qc = useQueryClient();
  const [tab, setTab] = useState<TabKey>('targets');
  const [actionError, setActionError] = useState<string | null>(null);

  // ── Targets ──────────────────────────────────────────────────────────────
  const targetsQ = useQuery<TwilioDbTarget[]>({ queryKey: ['twilio-db-targets'], queryFn: twilioDB_listTargets });

  const [openTarget, setOpenTarget] = useState(false);
  const [targetForm, setTargetForm] = useState<TargetForm>({ name: '', phone_no: '', roll_no: '', department: '', program: '' });
  const [savingTarget, setSavingTarget] = useState(false);

  const handleSaveTarget = async () => {
    setActionError(null);
    if (!targetForm.name.trim() || !targetForm.phone_no.trim()) {
      setActionError('Name and Phone No are required.');
      return;
    }
    setSavingTarget(true);
    try {
      await twilioDB_createTarget({
        name: targetForm.name.trim(),
        phone_no: targetForm.phone_no.trim(),
        roll_no: targetForm.roll_no.trim() || undefined,
        department: targetForm.department.trim() || undefined,
        program: targetForm.program.trim() || undefined,
      });
      setOpenTarget(false);
      setTargetForm({ name: '', phone_no: '', roll_no: '', department: '', program: '' });
      await qc.invalidateQueries({ queryKey: ['twilio-db-targets'] });
    } catch (e: any) {
      setActionError(e?.response?.data?.detail || e?.message || 'Failed to save.');
    } finally {
      setSavingTarget(false);
    }
  };

  const handleDeleteTarget = async (id: string) => {
    if (!confirm('Delete this target and all their call history?')) return;
    setActionError(null);
    try {
      await twilioDB_deleteTarget(id);
      await qc.invalidateQueries({ queryKey: ['twilio-db-targets'] });
    } catch (e: any) {
      setActionError(e?.response?.data?.detail || e?.message || 'Failed to delete.');
    }
  };

  // ── Calls ─────────────────────────────────────────────────────────────────
  const callsQ = useQuery<TwilioDbCall[]>({ queryKey: ['twilio-db-calls'], queryFn: twilioDB_listCalls });

  const handleDeleteCall = async (id: string) => {
    if (!confirm('Delete this call and all its responses?')) return;
    setActionError(null);
    try {
      await twilioDB_deleteCall(id);
      await qc.invalidateQueries({ queryKey: ['twilio-db-calls'] });
      await qc.invalidateQueries({ queryKey: ['twilio-db-responses'] });
    } catch (e: any) {
      setActionError(e?.response?.data?.detail || e?.message || 'Failed to delete.');
    }
  };

  // ── Responses ─────────────────────────────────────────────────────────────
  const responsesQ = useQuery<TwilioDbResponse[]>({ queryKey: ['twilio-db-responses'], queryFn: twilioDB_listResponses });

  const handleDeleteResponse = async (id: string) => {
    if (!confirm('Delete this response record?')) return;
    setActionError(null);
    try {
      await twilioDB_deleteResponse(id);
      await qc.invalidateQueries({ queryKey: ['twilio-db-responses'] });
    } catch (e: any) {
      setActionError(e?.response?.data?.detail || e?.message || 'Failed to delete.');
    }
  };

  // ── Tab styles ────────────────────────────────────────────────────────────
  const tabSx = {
    '& .MuiTab-root': {
      fontWeight: 700,
      fontSize: '0.9rem',
      '&.Mui-selected': { color: ACCENT },
    },
    '& .MuiTabs-indicator': { background: ACCENT },
  };

  return (
    <Box sx={{ p: { xs: 1, md: 2 } }}>
      <PageHeader
        title="Twilio Database"
        subtitle="Inspect and manage the standalone Twilio service tables: Targets, Calls, and Responses."
      />

      {actionError && (
        <Alert severity="error" onClose={() => setActionError(null)} sx={{ mb: 2 }}>
          {actionError}
        </Alert>
      )}

      <Box sx={{ mb: 2, background: `${ACCENT}12`, borderRadius: 2, p: 1.5 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)} sx={tabSx}>
          <Tab label={`Targets${targetsQ.data ? ` (${targetsQ.data.length})` : ''}`} value="targets" />
          <Tab label={`Calls${callsQ.data ? ` (${callsQ.data.length})` : ''}`} value="calls" />
          <Tab label={`Responses${responsesQ.data ? ` (${responsesQ.data.length})` : ''}`} value="responses" />
        </Tabs>
      </Box>

      {/* ── Targets tab ───────────────────────────────────────────────────── */}
      {tab === 'targets' && (
        <Card sx={{ boxShadow: `0 4px 12px ${ACCENT}1a`, border: `1px solid ${ACCENT}26` }}>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6" fontWeight={700} sx={{ color: ACCENT }}>Targets</Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                size="small"
                onClick={() => { setOpenTarget(true); setActionError(null); }}
                sx={{ background: ACCENT, '&:hover': { background: '#0f766e' } }}
              >
                Add Target
              </Button>
            </Stack>

            <QueryStatus isLoading={targetsQ.isLoading} error={targetsQ.error} />

            {!targetsQ.isLoading && targetsQ.data && (
              <SimpleTable<Record<string, unknown>>
                rows={targetsQ.data as unknown as Record<string, unknown>[]}
                getRowId={(row) => String(row.target_id)}
                columns={[
                  { key: 'target_id', label: 'Target ID' },
                  { key: 'name', label: 'Name' },
                  { key: 'phone_no', label: 'Phone No' },
                  { key: 'roll_no', label: 'Roll No' },
                  { key: 'department', label: 'Department' },
                  { key: 'program', label: 'Program' },
                  { key: 'created_at', label: 'Created At' },
                ]}
                actions={(row) => (
                  <Button
                    size="small"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => handleDeleteTarget(String(row.target_id))}
                  >
                    Delete
                  </Button>
                )}
              />
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Calls tab ─────────────────────────────────────────────────────── */}
      {tab === 'calls' && (
        <Card sx={{ boxShadow: `0 4px 12px ${ACCENT}1a`, border: `1px solid ${ACCENT}26` }}>
          <CardContent>
            <Typography variant="h6" fontWeight={700} sx={{ color: ACCENT, mb: 2 }}>Twilio Calls</Typography>

            <QueryStatus isLoading={callsQ.isLoading} error={callsQ.error} />

            {!callsQ.isLoading && callsQ.data && (
              <SimpleTable<Record<string, unknown>>
                rows={callsQ.data as unknown as Record<string, unknown>[]}
                getRowId={(row) => String(row.call_id)}
                columns={[
                  { key: 'call_id', label: 'Call ID' },
                  { key: 'twilio_call_sid', label: 'Twilio SID' },
                  { key: 'target_id', label: 'Target ID' },
                  { key: 'status', label: 'Status' },
                  { key: 'scheduled_time', label: 'Scheduled' },
                  { key: 'started_time', label: 'Started' },
                  { key: 'ended_time', label: 'Ended' },
                  { key: 'overall_duration', label: 'Overall Duration (s)' },
                  { key: 'total_response_duration', label: 'Total Response Duration (s)' },
                  { key: 'questions_answered', label: 'Q Answered' },
                  { key: 'depression_risk', label: 'Depression Risk' },
                  { key: 'depression_risk_probability', label: 'Risk Probability' },
                  { key: 'depression_risk_level', label: 'Risk Level' },
                  { key: 'depression_risk_confidence', label: 'Risk Confidence' },
                  { key: 'depression_analysis_timestamp', label: 'Analysis Timestamp' },
                ]}
                actions={(row) => (
                  <Button
                    size="small"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => handleDeleteCall(String(row.call_id))}
                  >
                    Delete
                  </Button>
                )}
              />
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Responses tab ─────────────────────────────────────────────────── */}
      {tab === 'responses' && (
        <Card sx={{ boxShadow: `0 4px 12px ${ACCENT}1a`, border: `1px solid ${ACCENT}26` }}>
          <CardContent>
            <Typography variant="h6" fontWeight={700} sx={{ color: ACCENT, mb: 2 }}>Twilio Responses</Typography>

            <QueryStatus isLoading={responsesQ.isLoading} error={responsesQ.error} />

            {!responsesQ.isLoading && responsesQ.data && (
              <SimpleTable<Record<string, unknown>>
                rows={responsesQ.data as unknown as Record<string, unknown>[]}
                getRowId={(row) => String(row.response_id)}
                columns={[
                  { key: 'response_id', label: 'Response ID' },
                  { key: 'call_id', label: 'Call ID' },
                  { key: 'question_index', label: 'Q#' },
                  { key: 'question_text', label: 'Question' },
                  { key: 'response_type', label: 'Type' },
                  { key: 'response_value', label: 'Response Value' },
                  { key: 'twilio_recording_url', label: 'Twilio Recording URL' },
                  { key: 'minio_recording_url', label: 'MinIO Recording URL' },
                  { key: 'recording_playback_url', label: 'Playback URL' },
                  { key: 'recording_sid', label: 'Recording SID' },
                  { key: 'recording_duration', label: 'Duration (s)' },
                  { key: 'analysis_score', label: 'Analysis Score' },
                  { key: 'responded_at', label: 'Responded At' },
                ]}
                actions={(row) => (
                  <Button
                    size="small"
                    color="error"
                    startIcon={<DeleteIcon />}
                    onClick={() => handleDeleteResponse(String(row.response_id))}
                  >
                    Delete
                  </Button>
                )}
              />
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Add Target dialog ─────────────────────────────────────────────── */}
      <Dialog open={openTarget} onClose={() => setOpenTarget(false)} fullWidth maxWidth="sm">
        <DialogTitle sx={{ color: ACCENT, fontWeight: 700 }}>Add Target</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ mt: 1 }}>
            <TextField label="Name *" size="small" fullWidth value={targetForm.name} onChange={(e) => setTargetForm((p) => ({ ...p, name: e.target.value }))} />
            <TextField label="Phone No *" size="small" fullWidth value={targetForm.phone_no} onChange={(e) => setTargetForm((p) => ({ ...p, phone_no: e.target.value }))} helperText="E.164 or 10-digit Indian format" />
            <TextField label="Roll No" size="small" fullWidth value={targetForm.roll_no} onChange={(e) => setTargetForm((p) => ({ ...p, roll_no: e.target.value }))} />
            <TextField label="Department" size="small" fullWidth value={targetForm.department} onChange={(e) => setTargetForm((p) => ({ ...p, department: e.target.value }))} />
            <TextField label="Program" size="small" fullWidth value={targetForm.program} onChange={(e) => setTargetForm((p) => ({ ...p, program: e.target.value }))} />
            {actionError && <Alert severity="error">{actionError}</Alert>}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenTarget(false)} disabled={savingTarget}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSaveTarget}
            disabled={savingTarget}
            sx={{ background: ACCENT, '&:hover': { background: '#0f766e' } }}
          >
            {savingTarget ? 'Saving…' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
