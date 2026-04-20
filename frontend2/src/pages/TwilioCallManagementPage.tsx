import React, { useEffect, useMemo, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import {
  Box, Button, Card, CardContent, CircularProgress, Collapse, Divider,
  IconButton, InputAdornment, Stack, Table, TableBody, TableCell,
  Tab, TableHead, TableRow, Tabs, TextField, Tooltip, Typography,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import InfoIcon from '@mui/icons-material/InfoOutlined';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import PhoneIcon from '@mui/icons-material/Phone';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import PhoneMissedIcon from '@mui/icons-material/PhoneMissed';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import MicIcon from '@mui/icons-material/Mic';
import PageHeader from '../components/PageHeader';
import {
  fetchTwilioTargets, createTwilioTarget,
  fetchCallsForTarget, initiateCallsBulk, bulkImportTwilioTargets,
} from '../api/twilioApi';
import type { TwilioTarget, TwilioCall, TwilioTargetCreate } from '../api/twilioApi';

// ── Types ──────────────────────────────────────────────────────────────────
type SortKey = 'name' | 'roll_no' | 'department' | 'program' | 'status';
type ViewTab = 'all' | 'flagged';

type CreateFormErrors = {
  phone_no?: string;
};

// ── Status rendering ───────────────────────────────────────────────────────
const ACCENT = '#0d9488'; // teal-600

const STATUS_CONFIG: Record<string, { icon: React.ReactNode; label: string; color: string }> = {
  'Call Scheduled': { icon: <AccessTimeIcon fontSize="small" />, label: 'Scheduled', color: '#f59e0b' },
  'Call Initiated': { icon: <PhoneIcon fontSize="small" />, label: 'Initiated', color: '#6366f1' },
  'In Progress':    { icon: <PhoneIcon fontSize="small" />, label: 'In Progress', color: '#8b5cf6' },
  'Completed':      { icon: <CheckCircleIcon fontSize="small" />, label: 'Completed', color: '#10b981' },
  'No Answer':      { icon: <PhoneMissedIcon fontSize="small" />, label: 'No Answer', color: '#f97316' },
  'Busy':           { icon: <PhoneMissedIcon fontSize="small" />, label: 'Busy', color: '#f97316' },
  'Failed':         { icon: <HelpOutlineIcon fontSize="small" />, label: 'Failed', color: '#ef4444' },
  'Cancelled':      { icon: <HelpOutlineIcon fontSize="small" />, label: 'Cancelled', color: '#9ca3af' },
  'Call hungup with short communication': { icon: <CheckCircleIcon fontSize="small" />, label: 'Call hungup with short communication', color: '#8b5cf6' },
  'Call hungup with communication': { icon: <CheckCircleIcon fontSize="small" />, label: 'Call hungup with communication', color: '#10b981' },
};

// Helper to determine display status based on total_response_duration
function getDisplayStatus(status: string, totalResponseDuration: number | null | undefined): string {
  if (status === 'Completed' && totalResponseDuration !== null && totalResponseDuration !== undefined) {
    return totalResponseDuration < 180 
      ? 'Call hungup with short communication'
      : 'Call hungup with communication';
  }
  return status;
}

function StatusChip({ status, totalResponseDuration }: { status: string; totalResponseDuration?: number | null }) {
  const displayStatus = getDisplayStatus(status, totalResponseDuration);
  const cfg = STATUS_CONFIG[displayStatus] ?? { icon: <HelpOutlineIcon fontSize="small" />, label: displayStatus, color: '#9ca3af' };
  const isLongStatus = displayStatus.includes('call hungup');
  return (
    <Stack direction={isLongStatus ? 'column' : 'row'} spacing={isLongStatus ? 0.3 : 0.5} alignItems="center" sx={{ color: cfg.color, textAlign: 'center' }}>
      {cfg.icon}
      <Typography variant="body2" fontWeight={600} sx={{ color: cfg.color, maxWidth: isLongStatus ? '100px' : 'auto', fontSize: isLongStatus ? '0.75rem' : '0.875rem' }}>{cfg.label}</Typography>
    </Stack>
  );
}

function fmt(iso: string | null | undefined): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false });
}

// ── Main Component ─────────────────────────────────────────────────────────
export default function TwilioCallManagementPage() {
  const [targets, setTargets] = useState<TwilioTarget[]>([]);
  const [callsMap, setCallsMap] = useState<Record<string, TwilioCall[]>>({});
  const [loadingTargets, setLoadingTargets] = useState(false);
  const [loadingCalls, setLoadingCalls] = useState<Record<string, boolean>>({});
  const [openDetails, setOpenDetails] = useState<Record<string, boolean>>({});
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [initiating, setInitiating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Search & sort
  const [search, setSearch] = useState('');
  const [sortCol, setSortCol] = useState<SortKey | null>('name');
  const [sortAsc, setSortAsc] = useState(true);
  const [viewTab, setViewTab] = useState<ViewTab>('all');
  const [flaggedExpandedCallKey, setFlaggedExpandedCallKey] = useState<string | null>(null);

  // Add form
  const [showAdd, setShowAdd] = useState(false);
  const [addForm, setAddForm] = useState<TwilioTargetCreate>({ name: '', phone_no: '', roll_no: '', department: '', program: '' });
  const [addErrors, setAddErrors] = useState<CreateFormErrors>({});
  const [addSubmitting, setAddSubmitting] = useState(false);

  // Import
  const [importing, setImporting] = useState(false);
  const fileRef = useRef<HTMLInputElement | null>(null);

  const loadTargets = async () => {
    setError(null);
    setLoadingTargets(true);
    try {
      setTargets(await fetchTwilioTargets());
    } catch (e: any) {
      setError(e?.message || 'Failed to fetch targets');
    } finally {
      setLoadingTargets(false);
    }
  };

  useEffect(() => { loadTargets(); }, []);

  const ensureCalls = async (targetId: string) => {
    if (callsMap[targetId] || loadingCalls[targetId]) return;
    setLoadingCalls((p) => ({ ...p, [targetId]: true }));
    try {
      const calls = await fetchCallsForTarget(targetId);
      setCallsMap((p) => ({ ...p, [targetId]: calls }));
    } catch {
      setCallsMap((p) => ({ ...p, [targetId]: [] }));
    } finally {
      setLoadingCalls((p) => ({ ...p, [targetId]: false }));
    }
  };

  const loadCallsForFlaggedView = async () => {
    const missing = targets
      .map((t) => t.target_id)
      .filter((id) => !callsMap[id] && !loadingCalls[id]);

    if (!missing.length) return;

    setLoadingCalls((p) => {
      const next = { ...p };
      missing.forEach((id) => { next[id] = true; });
      return next;
    });

    try {
      const fetched = await Promise.all(
        missing.map(async (id) => {
          try {
            const calls = await fetchCallsForTarget(id);
            return [id, calls] as [string, TwilioCall[]];
          } catch {
            return [id, [] as TwilioCall[]] as [string, TwilioCall[]];
          }
        })
      );

      setCallsMap((p) => {
        const next = { ...p };
        fetched.forEach(([id, calls]) => { next[id] = calls; });
        return next;
      });
    } finally {
      setLoadingCalls((p) => {
        const next = { ...p };
        missing.forEach((id) => { next[id] = false; });
        return next;
      });
    }
  };

  useEffect(() => {
    if (viewTab === 'flagged' && targets.length > 0) {
      void loadCallsForFlaggedView();
    }
  }, [viewTab, targets, callsMap]);

  const toggleDetails = (id: string) => {
    setOpenDetails((p) => {
      const next = !p[id];
      if (next) ensureCalls(id);
      return { ...p, [id]: next };
    });
  };

  const toggleSelect = (id: string) => {
    setSelected((p) => {
      const n = new Set(p);
      n.has(id) ? n.delete(id) : n.add(id);
      return n;
    });
  };

  const handleSort = (col: SortKey) => {
    if (sortCol === col) setSortAsc((a) => !a);
    else { setSortCol(col); setSortAsc(true); }
  };

  const toggleFlaggedInlineInfo = async (targetId: string, callId: string) => {
    if (!callsMap[targetId] && !loadingCalls[targetId]) {
      await ensureCalls(targetId);
    }
    const key = `${targetId}-${callId}`;
    setFlaggedExpandedCallKey((prev) => (prev === key ? null : key));
  };

  const sortedTargets = useMemo(() => {
    const q = search.trim().toLowerCase();
    const base = targets.filter((t) => {
      if (!q) return true;
      return [t.name, t.roll_no, t.department, t.program, t.phone_no]
        .some((f) => String(f || '').toLowerCase().includes(q));
    });
    if (!sortCol) return base;
    return [...base].sort((a, b) => {
      if (sortCol === 'status') {
        const callsA = callsMap[a.target_id] ?? [];
        const callsB = callsMap[b.target_id] ?? [];
        const latestA = callsA[0];
        const latestB = callsB[0];
        const statusA = latestA ? getDisplayStatus(latestA.status, latestA.total_response_duration) : '';
        const statusB = latestB ? getDisplayStatus(latestB.status, latestB.total_response_duration) : '';
        return sortAsc ? statusA.localeCompare(statusB) : statusB.localeCompare(statusA);
      }
      const av = String((a as any)[sortCol] || '').toLowerCase();
      const bv = String((b as any)[sortCol] || '').toLowerCase();
      return sortAsc ? av.localeCompare(bv) : bv.localeCompare(av);
    });
  }, [targets, search, sortCol, sortAsc, callsMap]);

  const displayedTargets = useMemo(() => {
    if (viewTab !== 'flagged') return sortedTargets;
    return sortedTargets.filter((t) => {
      const calls = callsMap[t.target_id] ?? [];
      return calls.some((c) => c.depression_risk_probability != null && c.depression_risk_probability > 0.5);
    });
  }, [sortedTargets, viewTab, callsMap]);

  const flaggedRows = useMemo(() => {
    return displayedTargets.flatMap((t) => {
      const calls = callsMap[t.target_id] ?? [];
      return calls
        .filter((c) => c.depression_risk_probability != null && c.depression_risk_probability > 0.5)
        .map((call) => ({
          target: t,
          call,
        }));
    });
  }, [displayedTargets, callsMap]);

  const handleExportFlagged = () => {
    const headers = ['Name', 'Roll No', 'Department', 'Program', 'Call Made DateTime', 'Analysis Score'];
    const rows = flaggedRows.map(({ target, call }) => [
      target.name ?? '',
      target.roll_no ?? '',
      target.department ?? '',
      target.program ?? '',
      call.scheduled_time ?? '',
      call.depression_risk_probability != null ? call.depression_risk_probability.toFixed(3) : '',
    ]);
    const csv = [headers, ...rows]
      .map((r) => r.map((v) => `"${String(v).replace(/"/g, '""')}"`).join(','))
      .join('\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'flagged_recipients.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  // ── Add recipient ─────────────────────────────────────────────────────────
  const handleAddFieldChange = (field: keyof TwilioTargetCreate, value: string) => {
    if (field === 'phone_no') {
      let cleaned = value.replace(/[^\d+]/g, '');
      const hadPlus = cleaned.includes('+');
      cleaned = cleaned.replace(/\+/g, '');
      if (hadPlus) cleaned = '+' + cleaned;
      setAddForm((p) => ({ ...p, phone_no: cleaned }));
      setAddErrors((p) => ({
        ...p,
        phone_no: cleaned === '' || /^\+?\d+$/.test(cleaned) ? undefined : 'Only digits, optionally with a leading +',
      }));
      return;
    }
    setAddForm((p) => ({ ...p, [field]: value }));
  };

  const handleAddSubmit = async () => {
    if (addSubmitting) return;
    if (!addForm.name.trim() || !addForm.phone_no.trim()) { alert('Name and Phone No are required.'); return; }
    if (!/^\+?\d+$/.test(addForm.phone_no.trim())) {
      setAddErrors({ phone_no: 'Only digits, optionally with a leading +' });
      return;
    }
    try {
      setAddSubmitting(true);
      await createTwilioTarget({
        name: addForm.name.trim(),
        phone_no: addForm.phone_no.trim(),
        roll_no: addForm.roll_no?.trim() || undefined,
        department: addForm.department?.trim() || undefined,
        program: addForm.program?.trim() || undefined,
      });
      alert('Recipient added successfully.');
      setAddForm({ name: '', phone_no: '', roll_no: '', department: '', program: '' });
      setAddErrors({});
      setShowAdd(false);
      await loadTargets();
    } catch (e: any) {
      alert(e?.response?.data?.detail || e?.message || 'Failed to add recipient.');
    } finally {
      setAddSubmitting(false);
    }
  };

  // ── Import CSV/XLSX ───────────────────────────────────────────────────────
  const normalizeRow = (row: Record<string, string>): TwilioTargetCreate | null => {
    const name = (row['name'] || '').trim();
    const phone_no = (row['phone_no'] || '').trim();
    if (!name || !phone_no) return null;
    return {
      name,
      phone_no,
      roll_no: (row['roll_no'] || '').trim() || undefined,
      department: (row['department'] || '').trim() || undefined,
      program: (row['program'] || '').trim() || undefined,
    };
  };

  const parseCsv = async (file: File): Promise<TwilioTargetCreate[]> => {
    const text = await file.text();
    const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    if (lines.length < 2) return [];
    const rawHeaders = lines[0].split(',').map((h) => h.trim().replace(/^\ufeff/, ''));
    const headerMap: Record<string, string> = {};
    rawHeaders.forEach((h) => { headerMap[h] = h.toLowerCase(); });
    if (!Object.values(headerMap).includes('name') || !Object.values(headerMap).includes('phone_no')) {
      throw new Error('CSV must have at least Name and Phone_No columns.');
    }
    return lines.slice(1).map((line) => {
      const cells = line.split(',');
      const row: Record<string, string> = {};
      rawHeaders.forEach((h, i) => { row[headerMap[h]] = (cells[i] || '').trim(); });
      return normalizeRow(row);
    }).filter((r): r is TwilioTargetCreate => !!r);
  };

  const parseExcel = async (file: File): Promise<TwilioTargetCreate[]> => {
    const XLSX = await import('xlsx');
    const buffer = await file.arrayBuffer();
    const wb = XLSX.read(buffer, { type: 'array' });
    const sheet = wb.Sheets[wb.SheetNames[0]];
    const rows = XLSX.utils.sheet_to_json<Record<string, any>>(sheet, { defval: '' });
    return rows.map((row) => {
      const lowered: Record<string, string> = {};
      Object.keys(row).forEach((k) => { lowered[k.trim().replace(/^\ufeff/, '').toLowerCase()] = String(row[k] ?? '').trim(); });
      return normalizeRow(lowered);
    }).filter((r): r is TwilioTargetCreate => !!r);
  };

  const handleFileImport = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      setImporting(true);
      const ext = file.name.split('.').pop()?.toLowerCase();
      const rows = ext === 'csv' ? await parseCsv(file)
        : (ext === 'xlsx' || ext === 'xls') ? await parseExcel(file)
        : (() => { throw new Error('Unsupported file type. Upload CSV or Excel.'); })();
      if (!rows.length) throw new Error('No valid rows found. Required headers: Name, Phone_No');
      await bulkImportTwilioTargets(rows);
      alert(`${rows.length} recipient(s) imported.`);
      await loadTargets();
    } catch (err: any) {
      alert(err?.message || 'Failed to import file.');
    } finally {
      e.target.value = '';
      setImporting(false);
    }
  };

  // ── Initiate calls ────────────────────────────────────────────────────────
  const handleInitiateSelected = async () => {
    if (selected.size === 0) return;
    try {
      setInitiating(true);
      await initiateCallsBulk([...selected]);
      alert(`Call initiated for ${selected.size} recipient(s). Refresh call history in a moment.`);
      setSelected(new Set());
      // Invalidate cached call lists so they reload when expanded
      const cleared: Record<string, TwilioCall[]> = {};
      setCallsMap(cleared);
    } catch (e: any) {
      alert(e?.response?.data?.detail || e?.message || 'Failed to initiate calls.');
    } finally {
      setInitiating(false);
    }
  };

  // ── SortIcon helper ───────────────────────────────────────────────────────
  const SortIcon = ({ col }: { col: SortKey | 'latest' }) =>
    sortCol === col && !sortAsc ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />;

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <Box sx={{ p: { xs: 1, md: 2 } }}>
      <PageHeader
        title="Twilio Call Management"
        subtitle="Schedule calls to call recipients, view call history, analyze recordings, and track depressed recipients."
      />

      <Box sx={{ mb: 2, background: '#e9edf7', borderRadius: 1.5, p: 1.5 }}>
        <Tabs
          value={viewTab}
          onChange={(_, v) => setViewTab(v as ViewTab)}
          variant="fullWidth"
          sx={{
            minHeight: 52,
            '& .MuiTab-root': {
              fontWeight: 700,
              fontSize: '0.95rem',
              textTransform: 'none',
              color: '#4b5563',
              minHeight: 52,
              py: 0.5,
              '&.Mui-selected': { color: '#264bb5' },
            },
            '& .MuiTabs-indicator': {
              background: '#264bb5',
              height: 4,
              borderRadius: 2,
            },
          }}
        >
          <Tab label="Schedule calls to call recipients" value="all" />
          <Tab label="Call recipients flagged by AI" value="flagged" />
        </Tabs>
      </Box>

      {/* ── Inline Add Form ─────────────────────────────────────────────── */}
      {viewTab === 'all' && showAdd && (
        <Card sx={{ mb: 3, border: '2px solid', borderColor: `${ACCENT}44`, boxShadow: `0 4px 12px ${ACCENT}22` }}>
          <CardContent>
            <Typography variant="h6" fontWeight={700} mb={2} sx={{ color: ACCENT }}>Add Recipient</Typography>
            <Stack direction="row" spacing={1} alignItems="flex-start" sx={{ flexWrap: 'wrap', gap: 1 }}>
              <TextField size="small" label="Name *" value={addForm.name} onChange={(e) => handleAddFieldChange('name', e.target.value)} sx={{ minWidth: 160 }} />
              <TextField
                size="small" label="Phone No *" value={addForm.phone_no}
                onChange={(e) => handleAddFieldChange('phone_no', e.target.value)}
                error={!!addErrors.phone_no} helperText={addErrors.phone_no}
                sx={{ minWidth: 150 }}
              />
              <TextField size="small" label="Roll No" value={addForm.roll_no} onChange={(e) => handleAddFieldChange('roll_no', e.target.value)} sx={{ minWidth: 110 }} />
              <TextField size="small" label="Department" value={addForm.department} onChange={(e) => handleAddFieldChange('department', e.target.value)} sx={{ minWidth: 150 }} />
              <TextField size="small" label="Program" value={addForm.program} onChange={(e) => handleAddFieldChange('program', e.target.value)} sx={{ minWidth: 130 }} />
              <Button variant="contained" onClick={handleAddSubmit} disabled={addSubmitting} sx={{ background: ACCENT, '&:hover': { background: '#0f766e' }, alignSelf: 'flex-start' }}>
                {addSubmitting ? 'Saving…' : 'Add'}
              </Button>
              <Button variant="outlined" onClick={() => { setShowAdd(false); setAddForm({ name: '', phone_no: '', roll_no: '', department: '', program: '' }); setAddErrors({}); }} disabled={addSubmitting}
                sx={{ borderColor: `${ACCENT}88`, color: ACCENT, '&:hover': { borderColor: ACCENT, background: `${ACCENT}11` }, alignSelf: 'flex-start' }}>
                Cancel
              </Button>
            </Stack>
          </CardContent>
        </Card>
      )}

      {error && <Typography color="error" variant="body2" mb={2}>{error}</Typography>}

      {/* ── Toolbar ─────────────────────────────────────────────────────── */}
      {viewTab === 'all' && <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap', mb: 2 }}>
        <Button
          variant={showAdd ? 'contained' : 'outlined'}
          startIcon={<AddCircleOutlineIcon />}
          onClick={() => setShowAdd((s) => !s)}
          sx={showAdd
            ? { background: ACCENT, '&:hover': { background: '#0f766e' } }
            : { borderColor: `${ACCENT}88`, color: ACCENT, '&:hover': { borderColor: ACCENT, background: `${ACCENT}11` } }
          }
        >
          {showAdd ? 'Hide' : 'Add Recipient'}
        </Button>

        <Button
          variant="outlined"
          onClick={() => fileRef.current?.click()}
          disabled={importing}
          sx={{ borderColor: `${ACCENT}88`, color: ACCENT, '&:hover': { borderColor: ACCENT, background: `${ACCENT}11` } }}
        >
          {importing ? 'Importing…' : 'Import CSV / XLSX'}
        </Button>
        <Tooltip title="Required columns: Name, Phone_No. Optional: Roll_No, Department, Program." placement="right">
          <IconButton size="small" sx={{ color: ACCENT }}><InfoIcon /></IconButton>
        </Tooltip>
        <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" style={{ display: 'none' }} onChange={handleFileImport} />
      </Box>}

      {/* ── Initiate + Search row ────────────────────────────────────────── */}
      {viewTab === 'all' && <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap', mb: 2 }}>
        <Button
          variant="contained"
          startIcon={initiating ? <CircularProgress size={16} color="inherit" /> : <PlayArrowIcon />}
          disabled={selected.size === 0 || initiating}
          onClick={handleInitiateSelected}
          sx={{ background: '#059669', fontWeight: 600, boxShadow: '0 2px 8px rgba(5,150,105,0.3)', '&:hover': { background: '#047857' }, '&:disabled': { background: '#6b7280', color: '#fff' } }}
        >
          {initiating ? 'Initiating…' : `Initiate Twilio Call (${selected.size} selected)`}
        </Button>
        <TextField
          size="small"
          label="Search Recipients"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon sx={{ color: ACCENT }} /></InputAdornment> }}
          sx={{
            minWidth: 260,
            '& .MuiOutlinedInput-root': {
              '& fieldset': { borderColor: `${ACCENT}55`, borderWidth: 2 },
              '&:hover fieldset': { borderColor: `${ACCENT}99` },
              '&.Mui-focused fieldset': { borderColor: ACCENT, boxShadow: `0 0 0 3px ${ACCENT}22` },
            },
            '& .MuiInputLabel-root': { color: ACCENT, fontWeight: 600, '&.Mui-focused': { color: ACCENT } },
          }}
        />
      </Box>}

      {viewTab === 'flagged' && (
        <Card sx={{ border: '2px solid #fecaca', boxShadow: 'none', mb: 2 }}>
          <CardContent>
            <Typography variant="h6" sx={{ color: '#dc2626', fontWeight: 700, mb: 2 }}>
              Potential Cases for Investigation
            </Typography>

            <Stack direction="row" spacing={1.5} alignItems="center" sx={{ mb: 2 }}>
              <TextField
                size="small"
                label="Search Recipients"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                InputProps={{ startAdornment: <InputAdornment position="start"><SearchIcon sx={{ color: '#dc2626' }} /></InputAdornment> }}
                sx={{
                  minWidth: 300,
                  '& .MuiOutlinedInput-root': {
                    '& fieldset': { borderColor: '#fca5a5' },
                    '&:hover fieldset': { borderColor: '#f87171' },
                    '&.Mui-focused fieldset': { borderColor: '#ef4444' },
                  },
                  '& .MuiInputLabel-root': { color: '#dc2626', fontWeight: 600 },
                }}
              />
              <Button
                variant="outlined"
                onClick={handleExportFlagged}
                sx={{ borderColor: '#fca5a5', color: '#dc2626', '&:hover': { borderColor: '#ef4444', background: '#fef2f2' } }}
              >
                Export
              </Button>
            </Stack>

            <Box sx={{ overflowX: 'auto' }}>
              <Table size="small">
                <TableHead>
                  <TableRow sx={{ background: '#fef2f2', '& .MuiTableCell-head': { fontWeight: 700, color: '#1f2937' } }}>
                    <TableCell>Name</TableCell>
                    <TableCell>Roll No</TableCell>
                    <TableCell>Department</TableCell>
                    <TableCell>Program</TableCell>
                    <TableCell>Call Made DateTime</TableCell>
                    <TableCell>Analysis Score</TableCell>
                    <TableCell>Info</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loadingTargets && (
                    <TableRow>
                      <TableCell colSpan={7}>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <CircularProgress size={16} sx={{ color: '#dc2626' }} />
                          <Typography variant="body2">Loading recipients…</Typography>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  )}
                  {!loadingTargets && flaggedRows.length === 0 && (
                    <TableRow>
                      <TableCell colSpan={7}>
                        <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                          No AI-flagged recipients found (risk probability &gt; 0.5).
                        </Typography>
                      </TableCell>
                    </TableRow>
                  )}
                  {!loadingTargets && flaggedRows.map(({ target, call }) => {
                    const rowKey = `${target.target_id}-${call.call_id}`;
                    const isOpen = flaggedExpandedCallKey === rowKey;
                    return (
                      <React.Fragment key={rowKey}>
                        <TableRow hover>
                          <TableCell><Typography fontWeight={600}>{target.name || '—'}</Typography></TableCell>
                          <TableCell>{target.roll_no || '—'}</TableCell>
                          <TableCell>{target.department || '—'}</TableCell>
                          <TableCell>{target.program || '—'}</TableCell>
                          <TableCell>{fmt(call.scheduled_time)}</TableCell>
                          <TableCell>{call.depression_risk_probability != null ? call.depression_risk_probability.toFixed(3) : '—'}</TableCell>
                          <TableCell>
                            <IconButton size="small" onClick={() => toggleFlaggedInlineInfo(target.target_id, call.call_id)} sx={{ color: ACCENT }}>
                              <InfoIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell colSpan={7} sx={{ p: 0, border: 0 }}>
                            <Collapse in={isOpen} timeout="auto" unmountOnExit>
                              <Box sx={{ p: 2, bgcolor: '#f8fafc', borderRadius: 1, border: '1px solid', borderColor: 'divider', mb: 1 }}>
                                <Stack direction="column" spacing={0.5}>
                                  <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
                                    <Typography variant="body2" color="text.secondary">
                                      Scheduled: {fmt(call.scheduled_time)}
                                    </Typography>
                                    {call.started_time && (
                                      <Typography variant="body2" color="text.secondary">
                                        Answered: {fmt(call.started_time)}
                                      </Typography>
                                    )}
                                    {call.ended_time && (
                                      <Typography variant="body2" color="text.secondary">
                                        Ended: {fmt(call.ended_time)}
                                      </Typography>
                                    )}
                                    {call.overall_duration != null && (
                                      <Typography variant="body2" color="text.secondary">
                                        Overall Duration: {call.overall_duration}s
                                      </Typography>
                                    )}
                                    {call.total_response_duration != null && (
                                      <Typography variant="body2" color="text.secondary">
                                        Total Response Duration: {call.total_response_duration}s
                                      </Typography>
                                    )}
                                    <Typography variant="body2" color="text.secondary">
                                      {call.questions_answered}/{call.total_questions} answered
                                    </Typography>
                                  </Stack>
                                  <StatusChip status={call.status} totalResponseDuration={call.total_response_duration} />
                                  <Stack direction="row" spacing={1} alignItems="center">
                                    <Typography variant="body2" color="text.secondary">Risk Probability:</Typography>
                                    <Typography variant="body2" color="text.secondary" fontWeight={600}>
                                      {call.depression_risk_probability != null ? call.depression_risk_probability.toFixed(3) : '—'}
                                    </Typography>
                                  </Stack>
                                </Stack>

                                <Box sx={{ mt: 1.5 }}>
                                  {call.responses.filter((r) => !!r.recording_playback_url).length === 0 ? (
                                    <Typography variant="body2" color="text.secondary">No playable recordings available.</Typography>
                                  ) : (
                                    call.responses
                                      .filter((r) => !!r.recording_playback_url)
                                      .map((r) => (
                                        <Box key={r.response_id} sx={{ mb: 1 }}>
                                          <Stack direction="row" spacing={0.5} alignItems="flex-start">
                                            <MicIcon fontSize="small" sx={{ color: ACCENT, mt: 0.5 }} />
                                            <Box sx={{ flex: 1 }}>
                                              <Typography variant="body2" fontWeight={600} sx={{ color: ACCENT, lineHeight: 1.4 }}>
                                                Q{r.question_index + 1}:{' '}
                                                {(() => {
                                                  let text = r.question_text || '';
                                                  if (r.question_index === 0 && text.includes('Question')) {
                                                    text = text.substring(text.indexOf('Question'));
                                                  }
                                                  return text.replace(/Question\s+\d+:\s*/, '').trim();
                                                })()}
                                              </Typography>
                                            </Box>
                                          </Stack>
                                          <audio
                                            controls
                                            preload="metadata"
                                            src={r.recording_playback_url || undefined}
                                            style={{ display: 'block', maxWidth: 420, marginTop: 8 }}
                                          />
                                        </Box>
                                      ))
                                  )}
                                </Box>
                              </Box>
                            </Collapse>
                          </TableCell>
                        </TableRow>
                      </React.Fragment>
                    );
                  })}
                </TableBody>
              </Table>
            </Box>
          </CardContent>
        </Card>
      )}

      {/* ── Recipients Table ─────────────────────────────────────────────── */}
      {viewTab === 'all' && <Card sx={{ boxShadow: `0 4px 12px ${ACCENT}1a`, border: `1px solid ${ACCENT}26` }}>
        <CardContent sx={{ p: 0 }}>
          <Box sx={{ overflowX: 'auto' }}>
            <Table size="small" sx={{ minWidth: 900 }}>
              <TableHead>
                <TableRow sx={{ background: `${ACCENT}14`, '& .MuiTableCell-head': { fontWeight: 700, color: '#1f2937' } }}>
                  <TableCell>Select</TableCell>
                  {([['name', 'Name'], ['roll_no', 'Roll No'], ['department', 'Department'], ['program', 'Program']] as [SortKey, string][]).map(([col, label]) => (
                    <TableCell key={col}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        {label}
                        <IconButton size="small" onClick={() => handleSort(col)}><SortIcon col={col} /></IconButton>
                      </Box>
                    </TableCell>
                  ))}
                  <TableCell>Phone No</TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                      Latest Call
                      <IconButton size="small" onClick={() => handleSort('status')}><SortIcon col="status" /></IconButton>
                    </Box>
                  </TableCell>
                  <TableCell>History</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {loadingTargets && (
                  <TableRow>
                    <TableCell colSpan={8}>
                      <Stack direction="row" spacing={1} alignItems="center">
                        <CircularProgress size={16} sx={{ color: ACCENT }} />
                        <Typography variant="body2">Loading recipients…</Typography>
                      </Stack>
                    </TableCell>
                  </TableRow>
                )}
                {!loadingTargets && displayedTargets.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={8}>
                      <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                        No recipients found. Add one above or import a CSV/XLSX file.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
                {!loadingTargets && displayedTargets.map((t) => {
                  const isOpen = !!openDetails[t.target_id];
                  const calls = callsMap[t.target_id] ?? [];
                  const latestCall = calls[0];

                  return (
                    <React.Fragment key={t.target_id}>
                      <TableRow hover sx={{ '&:hover': { background: `${ACCENT}08` } }}>
                        <TableCell>
                          <IconButton size="small" onClick={() => toggleSelect(t.target_id)}>
                            {selected.has(t.target_id) ? <CheckBoxIcon sx={{ color: ACCENT }} /> : <CheckBoxOutlineBlankIcon />}
                          </IconButton>
                        </TableCell>
                        <TableCell><Typography fontWeight={600}>{t.name || '—'}</Typography></TableCell>
                        <TableCell>{t.roll_no || '—'}</TableCell>
                        <TableCell>{t.department || '—'}</TableCell>
                        <TableCell>{t.program || '—'}</TableCell>
                        <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>{t.phone_no}</TableCell>
                        <TableCell>
                          {latestCall
                            ? <StatusChip status={latestCall.status} totalResponseDuration={latestCall.total_response_duration} />
                            : <Typography variant="body2" color="text.secondary">No calls yet</Typography>
                          }
                        </TableCell>
                        <TableCell>
                          <IconButton size="small" onClick={() => toggleDetails(t.target_id)} sx={{ color: ACCENT }}>
                            <InfoIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>

                      {/* ── Call History Expandable ───────────────────────── */}
                      <TableRow>
                        <TableCell colSpan={8} sx={{ p: 0, border: 0 }}>
                          <Collapse in={isOpen} timeout="auto" unmountOnExit>
                            <Box sx={{ p: 2, bgcolor: '#f8fafc', borderRadius: 1, border: '1px solid', borderColor: 'divider', mb: 1 }}>
                              <Typography variant="subtitle2" mb={1} fontWeight={700}>
                                {t.name} — Call History
                              </Typography>

                              {loadingCalls[t.target_id] && (
                                <Stack direction="row" spacing={1} alignItems="center">
                                  <CircularProgress size={14} sx={{ color: ACCENT }} />
                                  <Typography variant="body2">Loading…</Typography>
                                </Stack>
                              )}

                              {!loadingCalls[t.target_id] && calls.length === 0 && (
                                <Typography variant="body2" color="text.secondary">No calls yet for this recipient.</Typography>
                              )}

                              {!loadingCalls[t.target_id] && calls.map((call) => (
                                <Box key={call.call_id} sx={{ mb: 2 }}>
                                  <Stack direction="column" spacing={0.5}>
                                    <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
                                      <Typography variant="body2" color="text.secondary">
                                        Scheduled: {fmt(call.scheduled_time)}
                                      </Typography>
                                      {call.started_time && (
                                        <Typography variant="body2" color="text.secondary">
                                          Answered: {fmt(call.started_time)}
                                        </Typography>
                                      )}
                                      {call.ended_time && (
                                        <Typography variant="body2" color="text.secondary">
                                          Ended: {fmt(call.ended_time)}
                                        </Typography>
                                      )}
                                      {call.overall_duration != null && (
                                        <Typography variant="body2" color="text.secondary">
                                          Overall Duration: {call.overall_duration}s
                                        </Typography>
                                      )}
                                      {call.total_response_duration != null && (
                                        <Typography variant="body2" color="text.secondary">
                                          Total Response Duration: {call.total_response_duration}s
                                        </Typography>
                                      )}
                                      <Typography variant="body2" color="text.secondary">
                                        {call.questions_answered}/{call.total_questions} answered
                                      </Typography>
                                    </Stack>
                                    <StatusChip status={call.status} totalResponseDuration={call.total_response_duration} />
                                    <Stack direction="row" spacing={1} alignItems="center">
                                      <Typography variant="body2" color="text.secondary">
                                        Risk Probability:
                                      </Typography>
                                      {call.depression_risk_probability != null ? (
                                        <Typography variant="body2" color="text.secondary" fontWeight={500}>
                                          {call.depression_risk_probability.toFixed(3)}
                                        </Typography>
                                      ) : (
                                        <Tooltip title="Depression risk analysis not yet available">
                                          <HelpOutlineIcon sx={{ color: '#ef4444', fontSize: '0.9rem' }} />
                                        </Tooltip>
                                      )}
                                    </Stack>
                                  </Stack>

                                  {call.responses.length > 0 && (
                                    <Box sx={{ ml: 2, mt: 1 }}>
                                      {call.responses.map((r) => (
                                        <Box key={r.response_id} sx={{ mb: 1 }}>
                                          <Stack direction="row" spacing={0.5} alignItems="flex-start">
                                            <MicIcon fontSize="small" sx={{ color: ACCENT, mt: 0.5 }} />
                                            <Box sx={{ flex: 1 }}>
                                              <Typography variant="body2" fontWeight={600} sx={{ color: ACCENT, lineHeight: 1.4 }}>
                                                Q{r.question_index + 1}:{' '}
                                                {(() => {
                                                  let text = r.question_text || '';
                                                  // For Q1, trim greeting message
                                                  if (r.question_index === 0 && text.includes('Question')) {
                                                    text = text.substring(text.indexOf('Question'));
                                                  }
                                                  // Remove "Question N:" pattern
                                                  return text.replace(/Question\s+\d+:\s*/, '').trim();
                                                })()}
                                              </Typography>
                                            </Box>
                                          </Stack>
                                          {r.recording_playback_url ? (
                                            <audio
                                              controls
                                              preload="metadata"
                                              src={r.recording_playback_url}
                                              style={{ display: 'block', maxWidth: 280, marginTop: 8 }}
                                            />
                                          ) : (
                                            <Typography variant="body2" color="text.secondary" sx={{ ml: 3, mt: 1 }}>No playable recording URL</Typography>
                                          )}
                                          {r.analysis_score != null && (
                                            <Typography variant="body2" sx={{ ml: 3, mt: 1, color: '#6b7280' }}>
                                              Analysis Score: {r.analysis_score.toFixed(3)}
                                            </Typography>
                                          )}
                                        </Box>
                                      ))}
                                    </Box>
                                  )}
                                  <Divider sx={{ mt: 1 }} />
                                </Box>
                              ))}
                            </Box>
                          </Collapse>
                        </TableCell>
                      </TableRow>
                    </React.Fragment>
                  );
                })}
              </TableBody>
            </Table>
          </Box>
        </CardContent>
      </Card>}
    </Box>
  );
}
