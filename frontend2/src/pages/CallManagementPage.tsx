import React, { ChangeEvent, useEffect, useMemo, useRef, useState } from 'react';
// Error state for create form validation
type CreateFormErrors = {
  Roll_No?: string;
  Phone_No?: string;
};
import { Box, Button, Card, CardContent, CircularProgress, Collapse, Dialog, DialogActions, DialogContent, DialogTitle, Divider, IconButton, InputAdornment, Menu, MenuItem, Stack, Table, TableBody, TableCell, TableHead, TableRow, Tabs, Tab, TextField, Tooltip, Typography } from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import InfoIcon from '@mui/icons-material/InfoOutlined';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';
// Status to icon and label mapping (from demo page)
const STATUS_ICON_MAP: Record<string, { icon: JSX.Element; label: string }> = {
  'Call Scheduled': { icon: <AccessTimeIcon sx={{ color: '#f59e0b' }} fontSize="small" />, label: 'Call Scheduled' },
  'busy': { icon: <PhoneMissedIcon color="error" />, label: 'Call made but not picked (busy)' },
  'no-answer': { icon: <PhoneMissedIcon color="error" />, label: 'Call made but not picked (no-answer)' },
  'Message Not Conveyed': {
    icon: (
      <Stack direction="row" spacing={0.5} alignItems="center">
        <PhoneInTalkIcon sx={{ color: '#8e24aa' }} fontSize="small" />
        <AccessTimeIcon sx={{ color: '#8e24aa' }} fontSize="small" />
      </Stack>
    ),
    label: 'Call hungup with short communication',
  },
  'Message Conveyed But Not Processed': {
    icon: (
      <Stack direction="row" spacing={0.5} alignItems="center">
        <PhoneInTalkIcon sx={{ color: '#8e24aa' }} fontSize="small" />
        <CheckCircleIcon sx={{ color: '#2e7d32' }} fontSize="small" />
      </Stack>
    ),
    label: 'Call hungup with communication',
  },
  'Message Conveyed And Processed': {
    icon: (
      <Stack direction="row" spacing={0.5} alignItems="center">
        <PhoneInTalkIcon sx={{ color: '#8e24aa' }} fontSize="small" />
        <CheckCircleIcon sx={{ color: '#2e7d32' }} fontSize="small" />
      </Stack>
    ),
    label: 'Call hungup with communication',
  },
  'failed': {
    icon: (
      <Stack direction="row" spacing={0.5} alignItems="center">
        <PhoneAndroidOutlinedIcon sx={{ color: '#d32f2f' }} fontSize="small" />
        <CloseIcon sx={{ color: '#d32f2f' }} fontSize="small" />
      </Stack>
    ),
    label: 'Call Failed (most likely because the phone number was non-existent)',
  },
};

// Group calls by status category
function groupCallsByStatus(calls: TargetWithLatest[], detailsMap: Record<string, TargetDetails>) {
  const groups: Record<string, TargetWithLatest[]> = {};
  calls.forEach(call => {
    const details = detailsMap[call.Target_Id];
    const latestCall = details?.Call_History?.[0];
    let status = latestCall?.Status || call.Latest_Status || '';
    // For busy/no-answer, group under 'Call Made But Not Picked'
    if (status === 'busy' || status === 'no-answer') {
      status = 'Call made but not picked';
    }
    if (!groups[status]) groups[status] = [];
    groups[status].push(call);
  });
  return groups;
}
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CallEndIcon from '@mui/icons-material/CallEnd';
import PhoneAndroidOutlinedIcon from '@mui/icons-material/PhoneAndroidOutlined';
import PhoneMissedIcon from '@mui/icons-material/PhoneMissed';
import PhoneInTalkIcon from '@mui/icons-material/PhoneInTalk';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CloseIcon from '@mui/icons-material/Close';
import PageHeader from '../components/PageHeader';
import { bulkImportTargets, createTarget, fetchFlaggedTargetsCounsellor, fetchPotentialCasesExport, fetchTargetDetails, fetchTargetsWithLatest, triggerCallSchedule } from '../api/counsellor';
import type { FlaggedCounsellorTarget, PotentialCaseExportRow, TargetDetails, TargetWithLatest, CreateTargetPayload } from '../api/counsellor';

type TargetSortKey = 'Name' | 'Roll_No' | 'Department_Name' | 'Program' | 'Latest_Status' | 'Latest_Emotion' | 'Has_Recording';
type FlaggedSortKey = 'Name' | 'Roll_No' | 'Department_Name' | 'Program' | 'Call_Scheduled_DateTime';

type Snapshot = {
  status: string;
  emotion: string;
  recordingUrl?: string;
};

const STATUS_ICON_MAP_BACKEND: Record<string, { left: React.ReactNode; right?: React.ReactNode }> = {
  awaiting: { left: <AccessTimeIcon sx={{ color: '#6b7280' }} fontSize="small" /> },
  not_conveyed: { left: <PhoneMissedIcon sx={{ color: '#d32f2f' }} fontSize="small" /> },
  not_processed: {
    left: <PhoneInTalkIcon sx={{ color: '#8e24aa' }} fontSize="small" />,
    right: <AccessTimeIcon sx={{ color: '#5e35b1' }} fontSize="small" />,
  },
  processed: {
    left: <PhoneInTalkIcon sx={{ color: '#8e24aa' }} fontSize="small" />,
    right: <CheckCircleIcon sx={{ color: '#2e7d32' }} fontSize="small" />,
  },
  failed: { 
    left: <PhoneAndroidOutlinedIcon sx={{ color: '#d32f2f' }} fontSize="small" />,
    right: <CloseIcon sx={{ color: '#d32f2f' }} fontSize="small" />
 },
};

const renderBackendStatusIcons = (statusRaw?: string | null, iconOnly = false) => {
  const status = (statusRaw || '').toLowerCase();
  if (status.includes('processing failed')) return renderStatusPair('failed', iconOnly);
  if (status.includes('processed')) return renderStatusPair('processed', iconOnly);
  if (status.includes('not processed')) return renderStatusPair('not_processed', iconOnly);
  if (status.includes('not conveyed')) return renderStatusPair('not_conveyed', iconOnly);
  if (status.includes('awaiting')) return renderStatusPair('awaiting', iconOnly);
  return <HelpOutlineIcon sx={{ color: '#9ca3af' }} fontSize="small" />;
};

const renderStatusPair = (key: keyof typeof STATUS_ICON_MAP_BACKEND, iconOnly = false) => {
  const icons = STATUS_ICON_MAP_BACKEND[key];
  if (iconOnly) {
    return (
      <Stack direction="row" spacing={0.75} alignItems="center" flexWrap="nowrap">
        {icons.left}
        {icons.right}
      </Stack>
    );
  }
  return (
    <Stack direction="row" spacing={0.75} alignItems="center" flexWrap="nowrap">
      {icons.left}
      {icons.right}
    </Stack>
  );
};

const renderEmotionLabel = (emotionRaw?: string | null) => {
  const emo = (emotionRaw || '').toLowerCase();
  if (!emo || emo.includes('not available') || emo.includes('not analyzed')) {
    return (
      <HelpOutlineIcon sx={{ color: '#d32f2f', fontSize: 18, verticalAlign: 'middle' }} />
    );
  }
  if (emo.includes('high')) return <Typography component="span" sx={{ color: '#d32f2f', fontWeight: 700 }}>High (Potential Case)</Typography>;
  if (emo.includes('moderate')) return <Typography component="span" sx={{ color: '#ed6c02', fontWeight: 600 }}>Moderate</Typography>;
  if (emo.includes('low')) return <Typography component="span" sx={{ color: '#2e7d32', fontWeight: 600 }}>Low</Typography>;
  return <Typography component="span" sx={{ color: '#6b7280', fontWeight: 500 }}>{emotionRaw}</Typography>;
};

export default function CounsellorPage() {
  const [createFormErrors, setCreateFormErrors] = useState<CreateFormErrors>({});
  const [activeTab, setActiveTab] = useState<'targets' | 'flagged'>('targets');
  const [targets, setTargets] = useState<TargetWithLatest[]>([]);
  const [flaggedTargets, setFlaggedTargets] = useState<FlaggedCounsellorTarget[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [openDetails, setOpenDetails] = useState<Record<string, boolean>>({});
  const [flaggedOpenDetails, setFlaggedOpenDetails] = useState<Record<string, boolean>>({});
  const [flaggedDetailTab, setFlaggedDetailTab] = useState<Record<string, 'low' | 'moderate' | 'high'>>({});
  const [sortColumn, setSortColumn] = useState<TargetSortKey | null>(null);
  const [sortAscending, setSortAscending] = useState(true);
  const [flaggedSortColumn, setFlaggedSortColumn] = useState<FlaggedSortKey | null>('Call_Scheduled_DateTime');
  const [flaggedSortAscending, setFlaggedSortAscending] = useState(false);
  const [flaggedSearch, setFlaggedSearch] = useState('');
  const [targetSearch, setTargetSearch] = useState('');
  const [loadingTargets, setLoadingTargets] = useState(false);
  const [loadingFlagged, setLoadingFlagged] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState<Record<string, boolean>>({});
  const [detailsMap, setDetailsMap] = useState<Record<string, TargetDetails>>({});
  const [error, setError] = useState<string | null>(null);
  const [exportAnchor, setExportAnchor] = useState<null | HTMLElement>(null);
  const [exportingPotential, setExportingPotential] = useState(false);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [showCreateInline, setShowCreateInline] = useState(false);
  const [createSubmitting, setCreateSubmitting] = useState(false);
  const [createForm, setCreateForm] = useState<CreateTargetPayload>({ Name: '', Roll_No: '', Phone_No: '', Department_Name: '', Program: '' });
  const [importing, setImporting] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  // render status using demo mapping first, fallback to backend status icons
  const renderStatusDisplay = (statusRaw?: string | null, iconOnly = false) => {
    const status = (statusRaw || '').toString();
    if (!status) return <HelpOutlineIcon sx={{ color: '#9ca3af' }} fontSize="small" />;
    const mapped = STATUS_ICON_MAP[status];
    if (mapped) {
      if (iconOnly) {
        return mapped.icon;
      }
      return (
        <Stack direction="row" spacing={1} alignItems="center">
          {mapped.icon}
          <Typography variant="body2">{mapped.label}</Typography>
        </Stack>
      );
    }
    return renderBackendStatusIcons(statusRaw, iconOnly);
  };

  useEffect(() => {
    loadData();
  }, []);

  // detect "Call hungup with communication" style statuses
  const isCommunicationStatus = (statusRaw?: string | null) => {
    const status = (statusRaw || '').toLowerCase();
    return status.includes('conveyed') || status.includes('processed') || status.includes('communication');
  };

  const resolveRecordingUrl = (url?: string | null) => {
    if (!url) return undefined;
    if (url.startsWith('http://') || url.startsWith('https://')) return url;
    const base = import.meta.env.VITE_API_URL || 'http://localhost:8000';
    return `${base}${url.startsWith('/') ? url : `/${url}`}`;
  };

  // Only play audio when a recording exists and the status is expected to have one
  const hasInlineRecording = (statusRaw?: string | null, url?: string | null) => {
    if (!url) return false;
    const s = (statusRaw || '').toLowerCase();
    if (s.includes('scheduled')) return false;
    if (s.includes('failed')) return false;
    if (s === 'busy' || s === 'no-answer' || s.includes('not picked')) return false;
    return true;
  };

  const loadData = async () => {
    setError(null);
    setLoadingTargets(true);
    setLoadingFlagged(true);
    try {
      const [targetsResp, flaggedResp] = await Promise.all([
        fetchTargetsWithLatest(),
        fetchFlaggedTargetsCounsellor(),
      ]);
      setTargets(targetsResp);
      setFlaggedTargets(flaggedResp);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch dashboard data');
    } finally {
      setLoadingTargets(false);
      setLoadingFlagged(false);
    }
  };

  const getSnapshot = (target: TargetWithLatest): Snapshot => {
    const details = detailsMap[target.Target_Id];
    const latestCall = details?.Call_History?.[0];
    const recordingUrl = latestCall?.Recording_Proxy_Url || latestCall?.Recording_Url || undefined;
    return {
      status: latestCall?.Status || target.Latest_Status || 'Not available',
      emotion: latestCall?.Emotion || target.Latest_Emotion || 'Not available',
      recordingUrl,
    };
  };

  const toggleSelect = (targetId: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(targetId)) next.delete(targetId);
      else next.add(targetId);
      return next;
    });
  };

  const ensureDetails = async (targetId: string | undefined | null) => {
    if (!targetId || detailsMap[targetId] || loadingDetails[targetId]) return;
    setLoadingDetails((prev) => ({ ...prev, [targetId]: true }));
    try {
      const details = await fetchTargetDetails(targetId);
      setDetailsMap((prev) => ({ ...prev, [targetId]: details }));
    } catch (err) {
      setError('Failed to fetch call history.');
    } finally {
      setLoadingDetails((prev) => ({ ...prev, [targetId]: false }));
    }
  };

  const toggleDetails = (targetId: string) => {
    setOpenDetails((prev) => {
      const nextOpen = !prev[targetId];
      if (nextOpen) ensureDetails(targetId);
      return { ...prev, [targetId]: nextOpen };
    });
  };

  const toggleFlaggedDetails = (targetId?: string | null) => {
    if (!targetId) return;
    setFlaggedOpenDetails((prev) => {
      const nextOpen = !prev[targetId];
      if (nextOpen) ensureDetails(targetId);
      return { ...prev, [targetId]: nextOpen };
    });
  };

  const handleExportClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setExportAnchor(event.currentTarget);
  };

  const handleExportClose = () => setExportAnchor(null);

  const handleExportRange = async (range: '24h' | '7d' | '30d') => {
    setExportAnchor(null);
    try {
      setExportingPotential(true);
      const data = await fetchPotentialCasesExport({ range });
      if (!data.length) {
        alert('No data available for export.');
        return;
      }

      const XLSX = await import('xlsx');
      const headers = ['Name', 'Roll_No', 'Phone_No', 'Department_Name', 'Program', 'Call_Made_DateTime'];
      const rows = data.map((row: PotentialCaseExportRow) => ({
        Name: row?.Name || '',
        Roll_No: row?.Roll_No || '',
        Phone_No: row?.Phone_No || '',
        Department_Name: row?.Department_Name || '',
        Program: row?.Program || '',
        Call_Made_DateTime: row?.Call_Made_DateTime || '',
      }));

      const worksheet = XLSX.utils.json_to_sheet(rows, { header: headers });
      const workbook = XLSX.utils.book_new();
      XLSX.utils.book_append_sheet(workbook, worksheet, 'PotentialCases');

      const suffix = range === '24h' ? 'last24h' : range === '7d' ? 'last7days' : 'last30days';
      XLSX.writeFile(workbook, `potential_cases_${suffix}.xlsx`);
    } catch (err: any) {
      alert(err?.message || 'Failed to export potential cases.');
    } finally {
      setExportingPotential(false);
    }
  };

  const handleCreateFieldChange = (field: keyof CreateTargetPayload, value: string) => {
    // Enforce input formats for Roll_No and Phone_No
    if (field === 'Roll_No') {
      const cleaned = value.replace(/\D/g, '');
      setCreateForm((prev) => ({ ...prev, [field]: cleaned }));
      setCreateFormErrors((prev) => ({ ...prev, Roll_No: cleaned === '' || /^\d+$/.test(cleaned) ? undefined : 'Roll No must contain digits only.' }));
      return;
    }
    if (field === 'Phone_No') {
      let cleaned = value.replace(/[^\d+]/g, '');
      const hadPlus = cleaned.includes('+');
      cleaned = cleaned.replace(/\+/g, '');
      if (hadPlus) cleaned = '+' + cleaned;
      setCreateForm((prev) => ({ ...prev, [field]: cleaned }));
      setCreateFormErrors((prev) => ({ ...prev, Phone_No: cleaned === '' || /^\+?\d+$/.test(cleaned) ? undefined : 'Phone No must contain only digits, optionally with a single leading +.' }));
      return;
    }
    setCreateForm((prev) => ({ ...prev, [field]: value }));
  };

  const handleOpenCreate = () => {
    setCreateDialogOpen(true);
  };

  const handleCloseCreate = () => {
    if (createSubmitting) return;
    setShowCreateInline(false);
    setCreateForm({ Name: '', Roll_No: '', Phone_No: '', Department_Name: '', Program: '' });
    setCreateFormErrors({});
  };

  const handleCreateSubmit = async () => {
    if (createSubmitting) return;
    const { Name, Roll_No, Phone_No, Department_Name, Program } = createForm;
    let errors: CreateFormErrors = {};
    if (!Name.trim() || !Roll_No.trim() || !Phone_No.trim() || !Department_Name.trim() || !Program.trim()) {
      alert('All fields are required.');
      return;
    }
    if (!/^\d+$/.test(Roll_No.trim())) {
      errors.Roll_No = 'Roll No must contain digits only.';
    }
    if (!/^\+?\d+$/.test(Phone_No.trim())) {
      errors.Phone_No = 'Phone No must contain only digits, optionally with a single leading +.';
    }
    setCreateFormErrors(errors);
    if (Object.keys(errors).length > 0) return;
    try {
      setCreateSubmitting(true);
      await createTarget({ Name: Name.trim(), Roll_No: Roll_No.trim(), Phone_No: Phone_No.trim(), Department_Name: Department_Name.trim(), Program: Program.trim() });
      alert('Recipient added successfully.');
      handleCloseCreate();
      await loadData();
    } catch (err: any) {
      alert(err?.message || 'Failed to add recipient.');
    } finally {
      setCreateSubmitting(false);
    }
  };

  const normalizeRow = (row: Record<string, string>): CreateTargetPayload | null => {
    const Name = (row['name'] || '').trim();
    const Roll_No = (row['roll_no'] || '').trim();
    const Phone_No = (row['phone_no'] || '').trim();
    const Department_Name = (row['department_name'] || '').trim();
    const Program = (row['program'] || '').trim();

    if (!Name || !Roll_No || !Phone_No) return null;

    return {
      Name,
      Roll_No,
      Phone_No,
      Department_Name,
      Program,
    };
  };

  const parseCsv = async (file: File): Promise<CreateTargetPayload[]> => {
    const text = await file.text();
    const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    if (lines.length < 2) return [];

    const rawHeaders = lines[0].split(',').map((h) => h.trim().replace(/^\ufeff/, ''));
    const required = ['name', 'roll_no', 'phone_no', 'department_name', 'program'];
    const headerMap: Record<string, string> = {};
    rawHeaders.forEach((h) => {
      const key = h.toLowerCase();
      if (required.includes(key)) headerMap[h] = key;
    });
    const hasAll = required.every((key) => Object.values(headerMap).includes(key));
    if (!hasAll) {
      throw new Error('Headers must be Name, Roll_No, Phone_No, Department_Name, Program (case-insensitive).');
    }
    return lines.slice(1).map((line) => {
      const cells = line.split(',');
      const row: Record<string, string> = {};
      rawHeaders.forEach((h, idx) => {
        const canonical = headerMap[h];
        if (canonical) row[canonical] = (cells[idx] || '').trim();
      });
      return normalizeRow(row);
    }).filter((r): r is CreateTargetPayload => !!r);
  };

  const parseExcel = async (file: File): Promise<CreateTargetPayload[]> => {
    try {
      const XLSX = await import('xlsx');
      const buffer = await file.arrayBuffer();
      const workbook = XLSX.read(buffer, { type: 'array' });
      const sheet = workbook.Sheets[workbook.SheetNames[0]];
      const rows = XLSX.utils.sheet_to_json<Record<string, any>>(sheet, { defval: '' });
      // Validate headers from the first row keys if available
      const firstRow = rows[0] || {};
      const rawHeaders = Object.keys(firstRow).map((k) => String(k).trim().replace(/^\ufeff/, ''));
      const required = ['name', 'roll_no', 'phone_no', 'department_name', 'program'];
      const headerMap: Record<string, string> = {};
      rawHeaders.forEach((h) => {
        const key = h.toLowerCase();
        if (required.includes(key)) headerMap[h] = key;
      });
      const hasAll = required.every((key) => Object.values(headerMap).includes(key));
      if (!hasAll) {
        throw new Error('Headers must be Name, Roll_No, Phone_No, Department_Name, Program (case-insensitive).');
      }
      return rows
        .map((row) => {
          const lowered: Record<string, string> = {};
          Object.keys(row).forEach((k) => {
            const rawKey = String(k).trim().replace(/^\ufeff/, '');
            const canonical = headerMap[rawKey];
            if (canonical) lowered[canonical] = String(row[k] ?? '').trim();
          });
          return normalizeRow(lowered);
        })
        .filter((r): r is CreateTargetPayload => !!r);
    } catch (err) {
      throw new Error('Unable to parse Excel. Please ensure the xlsx package is installed.');
    }
  };

  const handleFileImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      setImporting(true);
      const ext = file.name.split('.').pop()?.toLowerCase();
      let imported: CreateTargetPayload[] = [];
      if (ext === 'csv') {
        imported = await parseCsv(file);
      } else if (ext === 'xlsx' || ext === 'xls') {
        imported = await parseExcel(file);
      } else {
        throw new Error('Unsupported file type. Upload CSV or Excel.');
      }

      if (!imported.length) {
        throw new Error('No valid rows found. Required headers (case-insensitive): Name, Roll_No, Phone_No, Department_Name, Program.');
      }

      await bulkImportTargets(imported as Array<Record<string, unknown>>);
      alert('Recipients imported successfully.');
      await loadData();
    } catch (error: any) {
      alert(error?.message || 'Failed to import file.');
    } finally {
      event.target.value = '';
      setImporting(false);
    }
  };

  const handleSort = (column: TargetSortKey) => {
    if (sortColumn === column) {
      setSortAscending(!sortAscending);
    } else {
      setSortColumn(column);
      setSortAscending(true);
    }
  };

  const handleFlaggedSort = (column: FlaggedSortKey) => {
    if (flaggedSortColumn === column) {
      setFlaggedSortAscending(!flaggedSortAscending);
    } else {
      setFlaggedSortColumn(column);
      setFlaggedSortAscending(true);
    }
  };

  const sortedTargets = useMemo(() => {
    const query = targetSearch.trim().toLowerCase();
    const base = targets.filter((t) => {
      if (!query) return true;
      const snapshot = getSnapshot(t);
      const fields = [t.Name, t.Roll_No, t.Department_Name, t.Program, t.Phone_No, snapshot.status, snapshot.emotion];
      return fields.some((f) => String(f || '').toLowerCase().includes(query));
    });

    if (!sortColumn) return base;
    const sorted = [...base];

    sorted.sort((a, b) => {
      if (sortColumn === 'Has_Recording') {
        const aHas = !!getSnapshot(a).recordingUrl;
        const bHas = !!getSnapshot(b).recordingUrl;
        return sortAscending ? Number(bHas) - Number(aHas) : Number(aHas) - Number(bHas);
      }

      const aVal = sortColumn === 'Latest_Status' || sortColumn === 'Latest_Emotion'
        ? getSnapshot(a)[sortColumn === 'Latest_Status' ? 'status' : 'emotion']
        : (a as any)[sortColumn];
      const bVal = sortColumn === 'Latest_Status' || sortColumn === 'Latest_Emotion'
        ? getSnapshot(b)[sortColumn === 'Latest_Status' ? 'status' : 'emotion']
        : (b as any)[sortColumn];

      const aStr = String(aVal || '').toLowerCase();
      const bStr = String(bVal || '').toLowerCase();
      if (aStr < bStr) return sortAscending ? -1 : 1;
      if (aStr > bStr) return sortAscending ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [targets, targetSearch, sortColumn, sortAscending, detailsMap]);

  const sortedFlagged = useMemo(() => {
    const query = flaggedSearch.trim().toLowerCase();
    const base = flaggedTargets
      .filter((c) => {
        // Only include targets whose latest/flagged analysis is high
        const emo = String((c as any).Latest_Emotion || (c as any).Emotion || '').toLowerCase();
        if (!emo.includes('high')) return false;
        if (!query) return true;
        const fields = [c.Name, c.Roll_No, c.Department_Name, c.Program, c.Call_Scheduled_DateTime];
        return fields.some((f) => String(f || '').toLowerCase().includes(query));
      });

    if (!flaggedSortColumn) return base;
    const sorted = [...base];

    sorted.sort((a, b) => {
      const aVal = (a as any)[flaggedSortColumn || 'Call_Scheduled_DateTime'];
      const bVal = (b as any)[flaggedSortColumn || 'Call_Scheduled_DateTime'];

      // If sorting by datetime, compare by Date
      if (flaggedSortColumn === 'Call_Scheduled_DateTime' || !flaggedSortColumn) {
        const aDate = aVal ? new Date(aVal) : new Date(0);
        const bDate = bVal ? new Date(bVal) : new Date(0);
        return flaggedSortAscending ? aDate.getTime() - bDate.getTime() : bDate.getTime() - aDate.getTime();
      }

      const aStr = String(aVal || '').toLowerCase();
      const bStr = String(bVal || '').toLowerCase();
      if (aStr < bStr) return flaggedSortAscending ? -1 : 1;
      if (aStr > bStr) return flaggedSortAscending ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [flaggedTargets, flaggedSearch, flaggedSortColumn, flaggedSortAscending]);

  const handleScheduleSelected = async () => {
    try {
      await triggerCallSchedule();
      alert('Call scheduling triggered for selected recipients');
    } catch (err: any) {
      alert(err?.message || 'Failed to schedule calls');
    }
  };

  return (
    <Box sx={{ p: { xs: 1, md: 2 } }}>
      <PageHeader 
        title="Call Management" 
        subtitle="Schedule calls to call recipients, view call history, analyze recordings, and track depressed recipients"
      />

      {/* Inline Add Recipient Form (toggleable) */}
      {showCreateInline && (
        <Card
          sx={{
            mb: 3,
            width: '100%',
            background: 'rgba(30, 64, 175, 0.05)',
            border: '2px solid',
            borderColor: 'rgba(30, 64, 175, 0.2)',
            boxShadow: '0 4px 12px rgba(30, 64, 175, 0.15)',
          }}
        >
          <CardContent>
            <Typography
              variant="h6"
              fontWeight={700}
              mb={2}
              sx={{
                color: '#1e40af',
              }}
            >
              Add Recipient
            </Typography>
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mt: 1, flexWrap: 'nowrap', overflowX: 'auto' }}>
              <TextField
                size="small"
                label="Name"
                value={createForm.Name}
                onChange={(e) => handleCreateFieldChange('Name', e.target.value)}
                required
                sx={{ minWidth: 180 }}
              />
              <TextField
                size="small"
                label="Roll No"
                value={createForm.Roll_No}
                onChange={(e) => handleCreateFieldChange('Roll_No', e.target.value)}
                required
                error={!!createFormErrors.Roll_No}
                helperText={createFormErrors.Roll_No}
                sx={{ minWidth: 120 }}
              />
              <TextField
                size="small"
                label="Phone No"
                value={createForm.Phone_No}
                onChange={(e) => handleCreateFieldChange('Phone_No', e.target.value)}
                required
                error={!!createFormErrors.Phone_No}
                helperText={createFormErrors.Phone_No}
                sx={{ minWidth: 140 }}
              />
              <TextField
                size="small"
                label="Department"
                value={createForm.Department_Name}
                onChange={(e) => handleCreateFieldChange('Department_Name', e.target.value)}
                required
                sx={{ minWidth: 160 }}
              />
              <TextField
                size="small"
                label="Program"
                value={createForm.Program}
                onChange={(e) => handleCreateFieldChange('Program', e.target.value)}
                required
                sx={{ minWidth: 140 }}
              />
              <Button
                onClick={handleCreateSubmit}
                variant="contained"
                disabled={createSubmitting}
                sx={{
                  ml: 1,
                  background: '#1e40af',
                  '&:hover': {
                    background: '#1e3a8a',
                  },
                }}
              >
                {createSubmitting ? 'Saving...' : 'Add'}
              </Button>
              <Button
                onClick={handleCloseCreate}
                disabled={createSubmitting}
                variant="outlined"
                sx={{
                  ml: 1,
                  borderColor: 'rgba(30, 64, 175, 0.5)',
                  color: '#1e40af',
                  '&:hover': {
                    borderColor: '#1e40af',
                    background: 'rgba(30, 64, 175, 0.05)',
                  },
                }}
              >
                Clear
              </Button>
            </Stack>
          </CardContent>
        </Card>
      )}

      {error && (
        <Typography color="error" variant="body2" mb={2}>{error}</Typography>
      )}

      <Box 
        sx={{ 
          mb: 3,
          background: 'rgba(30, 64, 175, 0.08)',
          borderRadius: 2,
          p: 2,
        }}
      >
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          variant="fullWidth"
          sx={{
            '& .MuiTab-root': {
              color: '#556070',
              fontWeight: 700,
              fontSize: '0.95rem',
              transition: 'all 0.3s ease',
              '&:hover': {
                background: 'rgba(30, 64, 175, 0.15)',
              },
              '&.Mui-selected': {
                color: '#1e40af',
                borderRadius: '8px 8px 0 0',
              },
            },
            '& .MuiTabs-indicator': {
              height: 4,
              background: '#1e40af',
              borderRadius: '4px 4px 0 0',
            },
          }}
        >
          <Tab label="Schedule calls to call recipients" value="targets" />
          <Tab label="Call recipients are predicted as depressed by the machine learning model" value="flagged" />
        </Tabs>
      </Box>

      {activeTab === 'targets' && (
        <React.Fragment>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap', mb: 2 }}>
            <Button
              variant={showCreateInline ? 'contained' : 'outlined'}
              startIcon={<AddCircleOutlineIcon />}
              onClick={() => setShowCreateInline((s) => !s)}
              sx={{
                ...(showCreateInline
                  ? {
                      background: '#1e40af',
                      '&:hover': {
                        background: '#1e3a8a',
                      },
                    }
                  : {
                      borderColor: 'rgba(30, 64, 175, 0.5)',
                      color: '#1e40af',
                      '&:hover': {
                        borderColor: '#1e40af',
                        background: 'rgba(30, 64, 175, 0.05)',
                      },
                    }),
              }}
            >
              {showCreateInline ? 'Hide' : 'Add Call Recipient'}
            </Button>
            <Button
              variant="outlined"
              onClick={() => fileInputRef.current?.click()}
              disabled={importing}
              sx={{
                borderColor: 'rgba(30, 64, 175, 0.5)',
                color: '#1e40af',
                '&:hover': {
                  borderColor: '#1e40af',
                  background: 'rgba(30, 64, 175, 0.05)',
                },
              }}
            >
              Import Call Recipients (CSV/XLSX)
            </Button>
            <Tooltip
              title="Instruction while importing CSV/XLSX file -> Required fields: (Name, Roll_No, Phone_No, Department_Name, Program). Use these exact column headers in CSV/XLSX file while importing recipients."
              placement="right"
            >
              <IconButton size="small" color="primary" aria-label="Import instructions">
                <InfoIcon />
              </IconButton>
            </Tooltip>
            <input
              ref={fileInputRef}
              type="file"
              accept=".csv, application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
              style={{ display: 'none' }}
              onChange={handleFileImport}
            />
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 2, flexWrap: 'wrap', mb: 2 }}>
            <Button
              variant="contained"
              startIcon={<PlayArrowIcon />}
              disabled={selected.size === 0}
              onClick={handleScheduleSelected}
              sx={{
                background: '#059669',
                fontWeight: 600,
                boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)',
                '&:hover': {
                  background: '#047857',
                  boxShadow: '0 4px 12px rgba(16, 185, 129, 0.4)',
                },
                '&:disabled': {
                  background: '#6b7280',
                  color: '#ffffff',
                },
              }}
            >
              Schedule Call to Selected Call Recipients
            </Button>
            <TextField
              size="small"
              label="Search Call Recipients"
              placeholder="Search"
              value={targetSearch}
              onChange={(e) => setTargetSearch(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ color: '#1e40af' }} />
                  </InputAdornment>
                ),
              }}
              sx={{
                minWidth: 260,
                '& .MuiOutlinedInput-root': {
                  background: 'rgba(30, 64, 175, 0.03)',
                  transition: 'all 0.3s ease',
                  '& fieldset': {
                    borderColor: 'rgba(30, 64, 175, 0.3)',
                    borderWidth: '2px',
                  },
                  '&:hover fieldset': {
                    borderColor: 'rgba(30, 64, 175, 0.6)',
                  },
                  '&.Mui-focused fieldset': {
                    borderColor: '#1e40af',
                    borderWidth: '2px',
                    boxShadow: '0 0 0 3px rgba(30, 64, 175, 0.1)',
                  },
                },
                '& .MuiInputLabel-root': {
                  color: '#1e40af',
                  fontWeight: 600,
                  '&.Mui-focused': {
                    color: '#1e40af',
                  },
                },
              }}
            />
          </Box>

          <Card
            sx={{
              boxShadow: '0 4px 12px rgba(30, 64, 175, 0.1)',
              border: '1px solid rgba(30, 64, 175, 0.15)',
            }}
          >
            <CardContent>
              <Box sx={{ overflowX: 'auto' }}>
                <Table size="small" sx={{ minWidth: 1100 }}>
                  <TableHead>
                    <TableRow
                      sx={{
                        background: 'rgba(30, 64, 175, 0.08)',
                        '& .MuiTableCell-head': {
                          fontWeight: 700,
                          color: '#1f2937',
                        },
                      }}
                    >
                      <TableCell>Schedule</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          Name
                          <IconButton size="small" onClick={() => handleSort('Name')}>
                            {sortColumn === 'Name' && !sortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          Roll No
                          <IconButton size="small" onClick={() => handleSort('Roll_No')}>
                            {sortColumn === 'Roll_No' && !sortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          Department
                          <IconButton size="small" onClick={() => handleSort('Department_Name')}>
                            {sortColumn === 'Department_Name' && !sortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          Program
                          <IconButton size="small" onClick={() => handleSort('Program')}>
                            {sortColumn === 'Program' && !sortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          Last Call Status
                          <IconButton size="small" onClick={() => handleSort('Latest_Status')}>
                            {sortColumn === 'Latest_Status' && !sortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          Last Call Analysis
                          <IconButton size="small" onClick={() => handleSort('Latest_Emotion')}>
                            {sortColumn === 'Latest_Emotion' && !sortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          Last Call Recording
                          <IconButton size="small" onClick={() => handleSort('Has_Recording')}>
                            {sortColumn === 'Has_Recording' && !sortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>Info</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {loadingTargets && (
                      <TableRow>
                        <TableCell colSpan={9}>
                          <Stack direction="row" spacing={1} alignItems="center">
                            <CircularProgress size={16} />
                            <Typography variant="body2">Loading recipients...</Typography>
                          </Stack>
                        </TableCell>
                      </TableRow>
                    )}
                    {!loadingTargets && sortedTargets.map((t) => {
                      const isOpen = !!openDetails[t.Target_Id];
                      const snapshot = getSnapshot(t);
                      const details = detailsMap[t.Target_Id];

                      return (
                        <React.Fragment key={t.Target_Id}>
                          <TableRow
                            hover
                            sx={{
                              '&:hover': {
                                background: 'rgba(30, 64, 175, 0.03)',
                              },
                            }}
                          >
                            <TableCell>
                              <IconButton size="small" onClick={() => toggleSelect(t.Target_Id)}>
                                {selected.has(t.Target_Id) ? <CheckBoxIcon color="primary" /> : <CheckBoxOutlineBlankIcon />}
                              </IconButton>
                            </TableCell>
                            <TableCell><Typography fontWeight={600}>{t.Name || '—'}</Typography></TableCell>
                            <TableCell>{t.Roll_No || '—'}</TableCell>
                            <TableCell>{t.Department_Name || '—'}</TableCell>
                            <TableCell>{t.Program || '—'}</TableCell>
                            <TableCell>{renderStatusDisplay(snapshot.status, true)}</TableCell>
                            <TableCell>
                              <Tooltip title={snapshot.emotion || 'Not analyzed'}>
                                <span>
                                  {snapshot.emotion && snapshot.emotion.toLowerCase() !== 'not available' ? (
                                    <CheckCircleIcon sx={{ color: '#2e7d32' }} />
                                  ) : (
                                    <HelpOutlineIcon sx={{ color: '#d32f2f' }} />
                                  )}
                                </span>
                              </Tooltip>
                            </TableCell>
                            <TableCell>
                              <Stack direction="row" spacing={1} alignItems="center">
                                {snapshot.recordingUrl ? (
                                  <Tooltip title={isCommunicationStatus(snapshot.status) ? 'Recording available (hungup with communication)' : 'Recording available'}>
                                    <CheckCircleIcon sx={{ color: isCommunicationStatus(snapshot.status) ? '#2e7d32' : 'action.active' }} />
                                  </Tooltip>
                                ) : (
                                  <Typography variant="body2" color="text.secondary">—</Typography>
                                )}
                              </Stack>
                            </TableCell>
                            <TableCell>
                              <IconButton size="small" onClick={() => toggleDetails(t.Target_Id)}>
                                <InfoIcon />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell colSpan={9} sx={{ p: 0, border: 0 }}>
                              <Collapse in={isOpen} timeout="auto" unmountOnExit>
                                <Box sx={{ p: 2, bgcolor: '#f9fafb', borderRadius: 1, border: '1px solid', borderColor: 'divider', mb: 1 }}>
                                  <Typography variant="subtitle2" mb={1}>
                                    {t.Name || 'Recipient'} — {t.Program || 'Program'} — Roll No {t.Roll_No || 'N/A'} — Phone No {t.Phone_No || 'N/A'}
                                  </Typography>
                                  {loadingDetails[t.Target_Id] && (
                                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                                      <CircularProgress size={16} />
                                      <Typography variant="body2">Loading call history...</Typography>
                                    </Stack>
                                  )}
                                  {!loadingDetails[t.Target_Id] && (!details || details.Call_History.length === 0) && (
                                    <Typography variant="body2">No call history available.</Typography>
                                  )}
                                  {!loadingDetails[t.Target_Id] && details?.Call_History.map((call) => {
                                    const isCommStatus = isCommunicationStatus(call.Status);
                                    
                                    // Calculate hangup time (Started_Time + Duration)
                                    const calculateHangupTime = () => {
                                      if (!call.Started_Time || !call.Duration) return call.Started_Time || call.Scheduled_Time || '—';
                                      try {
                                        // Parse the datetime string (format: DD-MM-YYYY HH:MM:SS.ff)
                                        const [datePart, timePart] = call.Started_Time.split(' ');
                                        const [day, month, year] = datePart.split('-');
                                        const [time, fraction] = timePart.split('.');
                                        const [hours, minutes, seconds] = time.split(':');
                                        
                                        // Create date object
                                        const startDate = new Date(
                                          parseInt(year),
                                          parseInt(month) - 1,
                                          parseInt(day),
                                          parseInt(hours),
                                          parseInt(minutes),
                                          parseInt(seconds)
                                        );
                                        
                                        // Add duration (in seconds)
                                        const endDate = new Date(startDate.getTime() + call.Duration * 1000);
                                        
                                        // Format back to DD-MM-YYYY HH:MM:SS.ff
                                        const pad = (n: number) => n.toString().padStart(2, '0');
                                        const formatted = `${pad(endDate.getDate())}-${pad(endDate.getMonth() + 1)}-${endDate.getFullYear()} ${pad(endDate.getHours())}:${pad(endDate.getMinutes())}:${pad(endDate.getSeconds())}.${fraction || '00'}`;
                                        return formatted;
                                      } catch (e) {
                                        return call.Started_Time || call.Scheduled_Time || '—';
                                      }
                                    };
                                    
                                    return (
                                      <Box key={call.Call_Id} sx={{ mb: 1.5 }}>
                                        {/* For communication statuses, show Call made time */}
                                        {isCommStatus && call.Scheduled_Time && (
                                          <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 0.5, flexWrap: 'wrap' }}>
                                            <Typography variant="body2" sx={{ minWidth: 180, whiteSpace: 'nowrap' }}>{call.Scheduled_Time}</Typography>
                                            <Stack direction="row" spacing={1} alignItems="center" flexWrap="nowrap">
                                              <PhoneInTalkIcon sx={{ color: '#8e24aa' }} fontSize="small" />
                                              <Typography variant="body2" sx={{ whiteSpace: 'nowrap' }}>Call made</Typography>
                                            </Stack>
                                          </Stack>
                                        )}
                                        {/* For communication statuses, show Call picked time */}
                                        {isCommStatus && call.Started_Time && (
                                          <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 0.5, flexWrap: 'wrap' }}>
                                            <Typography variant="body2" sx={{ minWidth: 180, whiteSpace: 'nowrap' }}>{call.Started_Time}</Typography>
                                            <Stack direction="row" spacing={1} alignItems="center" flexWrap="nowrap">
                                              <PhoneInTalkIcon sx={{ color: '#8e24aa' }} fontSize="small" />
                                              <Typography variant="body2" sx={{ whiteSpace: 'nowrap' }}>Call picked</Typography>
                                            </Stack>
                                          </Stack>
                                        )}
                                        {/* Show the final status with timestamp */}
                                        <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 0.5, flexWrap: 'wrap' }}>
                                          <Typography variant="body2" sx={{ minWidth: 180, whiteSpace: 'nowrap' }}>
                                            {isCommStatus ? calculateHangupTime() : (call.Started_Time || call.Scheduled_Time || '—')}
                                          </Typography>
                                          <Stack direction="row" spacing={1} alignItems="center" flexWrap="nowrap">
                                            {renderStatusDisplay(call.Status)}
                                          </Stack>
                                          {/* {call.Duration !== null && call.Duration !== undefined && (
                                            <Typography variant="body2" sx={{ whiteSpace: 'nowrap' }}>Duration: {call.Duration}s</Typography>
                                          )} */}
                                          {call.Emotion && (
                                            <Typography variant="body2" sx={{ whiteSpace: 'nowrap' }}>Analysis: {call.Emotion}</Typography>
                                          )}
                                        </Stack>
                                        <Stack direction="row" spacing={2} alignItems="center" sx={{ mt: 0.5, flexWrap: 'wrap' }}>
                                          <Typography variant="body2" fontWeight={600}>
                                            Analysis: {renderEmotionLabel(call.Emotion)}
                                          </Typography>
                                          {hasInlineRecording(call.Status, call.Recording_Proxy_Url || call.Recording_Url) ? (
                                            <audio
                                              controls
                                              preload="metadata"
                                              src={resolveRecordingUrl(call.Recording_Proxy_Url || call.Recording_Url)}
                                              style={{ maxWidth: 240 }}
                                            />
                                          ) : (
                                            <Typography variant="body2" color="text.secondary">No recording</Typography>
                                          )}
                                        </Stack>
                                        <Divider sx={{ mt: 1 }} />
                                      </Box>
                                    );
                                  })}
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
        </React.Fragment>
      )}

      {activeTab === 'flagged' && (
        <Card
          sx={{
            boxShadow: '0 4px 12px rgba(211, 47, 47, 0.1)',
            border: '2px solid rgba(211, 47, 47, 0.2)',
          }}
        >
          <CardContent>
            <Typography
              variant="h6"
              fontWeight={700}
              mb={2}
              sx={{
                color: '#dc2626',
              }}
            >
              Potential Cases for Investigation
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap', mb: 2 }}>
              <TextField
                size="small"
                label="Search Recipients"
                placeholder="Search"
                value={flaggedSearch}
                onChange={(e) => setFlaggedSearch(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon sx={{ color: '#dc2626' }} />
                    </InputAdornment>
                  ),
                }}
                sx={{
                  minWidth: 260,
                  '& .MuiOutlinedInput-root': {
                    background: 'rgba(239, 68, 68, 0.03)',
                    transition: 'all 0.3s ease',
                    '& fieldset': {
                      borderColor: 'rgba(211, 47, 47, 0.3)',
                      borderWidth: '2px',
                    },
                    '&:hover fieldset': {
                      borderColor: 'rgba(211, 47, 47, 0.6)',
                    },
                    '&.Mui-focused fieldset': {
                      borderColor: '#dc2626',
                      borderWidth: '2px',
                      boxShadow: '0 0 0 3px rgba(220, 38, 38, 0.1)',
                    },
                  },
                  '& .MuiInputLabel-root': {
                    color: '#dc2626',
                    fontWeight: 600,
                    '&.Mui-focused': {
                      color: '#dc2626',
                    },
                  },
                }}
              />
              <Button
                variant="outlined"
                onClick={handleExportClick}
                disabled={exportingPotential}
                sx={{
                  borderColor: 'rgba(211, 47, 47, 0.5)',
                  color: '#dc2626',
                  fontWeight: 600,
                  '&:hover': {
                    borderColor: '#dc2626',
                    background: 'rgba(211, 47, 47, 0.05)',
                  },
                }}
              >
                {exportingPotential ? 'Exporting...' : 'Export'}
              </Button>
              <Menu anchorEl={exportAnchor} open={Boolean(exportAnchor)} onClose={handleExportClose}>
                <MenuItem onClick={() => handleExportRange('24h')}>Last 24 hours</MenuItem>
                <MenuItem onClick={() => handleExportRange('7d')}>Last 7 days</MenuItem>
                <MenuItem onClick={() => handleExportRange('30d')}>Last 30 days</MenuItem>
              </Menu>
            </Box>
            <Box sx={{ overflowX: 'auto' }}>
              <Table size="small" sx={{ minWidth: 900 }}>
                <TableHead>
                  <TableRow
                    sx={{
                      background: 'rgba(239, 68, 68, 0.08)',
                      '& .MuiTableCell-head': {
                        fontWeight: 700,
                        color: '#1f2937',
                      },
                    }}
                  >
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        Name
                        <IconButton size="small" onClick={() => handleFlaggedSort('Name')}>
                          {flaggedSortColumn === 'Name' && !flaggedSortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                        </IconButton>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        Roll No
                        <IconButton size="small" onClick={() => handleFlaggedSort('Roll_No')}>
                          {flaggedSortColumn === 'Roll_No' && !flaggedSortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                        </IconButton>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        Department
                        <IconButton size="small" onClick={() => handleFlaggedSort('Department_Name')}>
                          {flaggedSortColumn === 'Department_Name' && !flaggedSortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                        </IconButton>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        Program
                        <IconButton size="small" onClick={() => handleFlaggedSort('Program')}>
                          {flaggedSortColumn === 'Program' && !flaggedSortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                        </IconButton>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        Call Made DateTime
                        <IconButton size="small" onClick={() => handleFlaggedSort('Call_Scheduled_DateTime')}>
                          {flaggedSortColumn === 'Call_Scheduled_DateTime' && !flaggedSortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                        </IconButton>
                      </Box>
                    </TableCell>
                    <TableCell>Info</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {loadingFlagged && (
                    <TableRow>
                      <TableCell colSpan={6}>
                        <Stack direction="row" spacing={1} alignItems="center">
                          <CircularProgress size={16} />
                          <Typography variant="body2">Loading flagged targets...</Typography>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  )}
                  {!loadingFlagged && sortedFlagged.map((c) => {
                    const key = c.Target_Id || String(c.Flag_Id || c.Phone_No || c.Name);
                    const isOpen = !!flaggedOpenDetails[key];
                    const details = c.Target_Id ? detailsMap[c.Target_Id] : undefined;
                    return (
                      <React.Fragment key={key}>
                        <TableRow
                          hover
                          sx={{
                            '&:hover': {
                              background: 'rgba(239, 68, 68, 0.03)',
                            },
                          }}
                        >
                          <TableCell><Typography fontWeight={600}>{c.Name || '—'}</Typography></TableCell>
                          <TableCell>{c.Roll_No || '—'}</TableCell>
                          <TableCell>{c.Department_Name || '—'}</TableCell>
                          <TableCell>{c.Program || '—'}</TableCell>
                          <TableCell>{c.Call_Scheduled_DateTime || '—'}</TableCell>
                          <TableCell>
                            <IconButton size="small" onClick={() => toggleFlaggedDetails(c.Target_Id || key)}>
                              <InfoIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell colSpan={6} sx={{ p: 0, border: 0 }}>
                            <Collapse in={isOpen} timeout="auto" unmountOnExit>
                              <Box sx={{ p: 2, bgcolor: '#f9fafb', borderRadius: 1, border: '1px solid', borderColor: 'divider', mb: 1 }}>
                                <Typography variant="body2" fontWeight={700} gutterBottom>
                                  Analysis history
                                </Typography>
                                {c.Target_Id && loadingDetails[c.Target_Id] && (
                                  <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1 }}>
                                    <CircularProgress size={16} />
                                    <Typography variant="body2">Loading call history...</Typography>
                                  </Stack>
                                )}
                                {(() => {
                                  const history = details?.Call_History || [];
                                  const rowKey = c.Target_Id || key;
                                  if (!c.Target_Id || (!loadingDetails[c.Target_Id] && history.length === 0)) {
                                    return <Typography variant="body2" color="text.secondary">No call history available.</Typography>;
                                  }
                                  if (c.Target_Id && loadingDetails[c.Target_Id]) return null;

                                  const grouped: Record<'low' | 'moderate' | 'high', string[]> = {
                                    low: [],
                                    moderate: [],
                                    high: [],
                                  };

                                  history.forEach((call) => {
                                    const emo = String(call.Emotion || '').toLowerCase();
                                    const ts = call.Started_Time || call.Scheduled_Time || '—';
                                    if (emo.includes('high')) grouped.high.push(ts);
                                    else if (emo.includes('moderate')) grouped.moderate.push(ts);
                                    else if (emo.includes('low')) grouped.low.push(ts);
                                  });

                                  const currentTab = flaggedDetailTab[rowKey] ?? 'high';
                                  const entries = grouped[currentTab];
                                  const emptyMessages: Record<'low' | 'moderate' | 'high', string> = {
                                    low: 'No calls tagged with low analysis yet.',
                                    moderate: 'No calls tagged with moderate analysis yet.',
                                    high: 'No calls tagged with high analysis yet.',
                                  };

                                  return (
                                    <>
                                      <Tabs
                                        value={currentTab}
                                        onChange={(_, v: 'low' | 'moderate' | 'high') => setFlaggedDetailTab((prev) => ({ ...prev, [rowKey]: v }))}
                                        sx={{ 
                                          minHeight: 36, 
                                          mb: 1,
                                          '& .MuiTab-root': {
                                            minHeight: 36,
                                            fontSize: '0.85rem',
                                            fontWeight: 600,
                                            transition: 'all 0.2s ease',
                                            '&:hover': {
                                              background: 'rgba(0,0,0,0.05)',
                                            },
                                          },
                                          '& .MuiTab-root[value="low"]': {
                                            '&.Mui-selected': {
                                              color: '#2e7d32',
                                              background: 'rgba(46, 125, 50, 0.1)',
                                            },
                                          },
                                          '& .MuiTab-root[value="moderate"]': {
                                            '&.Mui-selected': {
                                              color: '#ed6c02',
                                              background: 'rgba(237, 108, 2, 0.1)',
                                            },
                                          },
                                          '& .MuiTab-root[value="high"]': {
                                            '&.Mui-selected': {
                                              color: '#d32f2f',
                                              background: 'rgba(211, 47, 47, 0.1)',
                                            },
                                          },
                                          '& .MuiTabs-indicator': {
                                            height: 3,
                                          },
                                        }}
                                      >
                                        <Tab label="Low" value="low" />
                                        <Tab label="Moderate" value="moderate" />
                                        <Tab label="High" value="high" />
                                      </Tabs>
                                      {entries.length === 0 ? (
                                        <Typography variant="body2" color="text.secondary">{emptyMessages[currentTab]}</Typography>
                                      ) : (
                                        entries.map((ts, idx) => (
                                          <Typography key={`${rowKey}-${currentTab}-${idx}`} variant="body2">{idx + 1}) {ts}</Typography>
                                        ))
                                      )}
                                    </>
                                  );
                                })()}
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
    </Box>
  );
}