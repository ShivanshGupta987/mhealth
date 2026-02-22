import { useMemo, useState, type ReactNode } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
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
import UploadFileIcon from '@mui/icons-material/UploadFile';
import AddIcon from '@mui/icons-material/Add';
import DeleteIcon from '@mui/icons-material/Delete';
import EditIcon from '@mui/icons-material/Edit';
import PageHeader from '../components/PageHeader';
import LoadingState from '../components/LoadingState';
import EmptyState from '../components/EmptyState';
import {
  listTargets,
  listModels,
  listEmotions,
  listAdmins,
  listCalls,
  listFlaggedTargetsRaw,
  createTarget,
  updateTarget,
  deleteTarget,
  importTargets,
  createModel,
  updateModel,
  deleteModel,
  createEmotion,
  updateEmotion,
  deleteEmotion,
  createAdmin,
  updateAdmin,
  deleteAdmin,
  createCall,
  updateCall,
  deleteCall,
  createFlaggedTarget,
  updateFlaggedTarget,
  deleteFlaggedTarget,
  type TargetRecord,
  type ModelRecord,
  type EmotionRecord,
  type AdminRecord,
  type CallRecord,
  type FlaggedTargetRecord,
} from '../api/database';
import { useQuery, useQueryClient } from '@tanstack/react-query';

type TargetFormState = {
  Name: string;
  Roll_No: string;
  Phone_No: string;
  Department_Name: string;
  Program: string;
};

type ModelFormState = {
  Model_Id: string;
  Model_Name: string;
  Model_Version: string;
  Model_Details: string;
};

type EmotionFormState = {
  Emotion_Id: string;
  Emotion: string;
};

type AdminFormState = {
  Admin_Id?: string;
  Email: string;
  Password: string;
};

type CallFormState = {
  Target_Id: string;
  Model_Id: string;
  Emotion_Id: string;
  Call_Sid: string;
  Status: string;
  Scheduled_Time: string;
  Started_Time: string;
  Duration: string;
  Recording_Url: string;
};

type FlaggedFormState = {
  Target_Id: string;
};

// Simplified table display
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
      const aVal = a[sortKey];
      const bVal = b[sortKey];
      if (aVal == null && bVal == null) return 0;
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
      }
      const aStr = String(aVal).toLowerCase();
      const bStr = String(bVal).toLowerCase();
      if (aStr < bStr) return sortDir === 'asc' ? -1 : 1;
      if (aStr > bStr) return sortDir === 'asc' ? 1 : -1;
      return 0;
    });
  }, [rows, sortKey, sortDir]);

  const handleSort = (key: keyof T) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  return (
    <Box sx={{ overflowX: 'auto' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            {columns.map((col) => {
              const isActive = sortKey === col.key;
              return (
                <th
                  key={String(col.key)}
                  style={{ textAlign: 'left', padding: '8px', borderBottom: '1px solid #ddd', cursor: 'pointer', userSelect: 'none' }}
                  onClick={() => handleSort(col.key)}
                >
                  <Stack direction="row" spacing={0.5} alignItems="center">
                    <span>{col.label}</span>
                    {isActive ? (
                      sortDir === 'asc' ? (
                        <ArrowUpwardIcon sx={{ fontSize: 16 }} />
                      ) : (
                        <ArrowDownwardIcon sx={{ fontSize: 16 }} />
                      )
                    ) : (
                      <ArrowUpwardIcon sx={{ fontSize: 16, opacity: 0.35 }} />
                    )}
                  </Stack>
                </th>
              );
            })}
            {actions && <th style={{ width: 160 }} />}
          </tr>
        </thead>
        <tbody>
          {sortedRows.map((row, index) => {
            const id = getRowId ? getRowId(row, index) : String((row as any).id ?? index);
            return (
              <tr key={id}>
                {columns.map((col) => (
                  <td key={String(col.key)} style={{ padding: '8px', borderBottom: '1px solid #f0f0f0' }}>
                    {String(row[col.key] ?? '')}
                  </td>
                ))}
                {actions && <td style={{ padding: '8px' }}>{actions(row)}</td>}
              </tr>
            );
          })}
        </tbody>
      </table>
    </Box>
  );
}

export default function DatabaseManagementPage() {
  const queryClient = useQueryClient();
  const [tab, setTab] = useState<'targets' | 'models' | 'emotions' | 'admins' | 'calls' | 'flagged'>('targets');

  const [openTargetDialog, setOpenTargetDialog] = useState(false);
  const [editingTarget, setEditingTarget] = useState<TargetRecord | null>(null);
  const [targetForm, setTargetForm] = useState<TargetFormState>({ Name: '', Roll_No: '', Phone_No: '', Department_Name: '', Program: '' });
  const [targetFile, setTargetFile] = useState<File | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [savingTarget, setSavingTarget] = useState(false);
  const [importing, setImporting] = useState(false);

  const [openModelDialog, setOpenModelDialog] = useState(false);
  const [editingModel, setEditingModel] = useState<ModelRecord | null>(null);
  const [modelForm, setModelForm] = useState<ModelFormState>({ Model_Id: '', Model_Name: '', Model_Version: '', Model_Details: '' });
  const [savingModel, setSavingModel] = useState(false);

  const [openEmotionDialog, setOpenEmotionDialog] = useState(false);
  const [editingEmotion, setEditingEmotion] = useState<EmotionRecord | null>(null);
  const [emotionForm, setEmotionForm] = useState<EmotionFormState>({ Emotion_Id: '', Emotion: '' });
  const [savingEmotion, setSavingEmotion] = useState(false);

  const [openAdminDialog, setOpenAdminDialog] = useState(false);
  const [editingAdmin, setEditingAdmin] = useState<AdminRecord | null>(null);
  const [adminForm, setAdminForm] = useState<AdminFormState>({ Email: '', Password: '' });
  const [savingAdmin, setSavingAdmin] = useState(false);

  const [openCallDialog, setOpenCallDialog] = useState(false);
  const [editingCall, setEditingCall] = useState<CallRecord | null>(null);
  const [callForm, setCallForm] = useState<CallFormState>({
    Target_Id: '',
    Model_Id: '',
    Emotion_Id: '',
    Call_Sid: '',
    Status: '',
    Scheduled_Time: '',
    Started_Time: '',
    Duration: '',
    Recording_Url: '',
  });
  const [savingCall, setSavingCall] = useState(false);

  const [openFlaggedDialog, setOpenFlaggedDialog] = useState(false);
  const [editingFlag, setEditingFlag] = useState<FlaggedTargetRecord | null>(null);
  const [flaggedForm, setFlaggedForm] = useState<FlaggedFormState>({ Target_Id: '' });
  const [savingFlagged, setSavingFlagged] = useState(false);

  const targetsQuery = useQuery<TargetRecord[]>({ queryKey: ['db-targets'], queryFn: listTargets });
  const modelsQuery = useQuery<ModelRecord[]>({ queryKey: ['db-models'], queryFn: listModels });
  const emotionsQuery = useQuery<EmotionRecord[]>({ queryKey: ['db-emotions'], queryFn: listEmotions });
  const adminsQuery = useQuery<AdminRecord[]>({ queryKey: ['db-admins'], queryFn: listAdmins });
  const callsQuery = useQuery<CallRecord[]>({ queryKey: ['db-calls'], queryFn: listCalls });
  const flaggedQuery = useQuery<FlaggedTargetRecord[]>({ queryKey: ['db-flagged'], queryFn: listFlaggedTargetsRaw });

  const handleSaveTarget = async () => {
    setActionError(null);
    setSavingTarget(true);
    const payload: Partial<TargetRecord> = {
      Name: targetForm.Name || undefined,
      Roll_No: targetForm.Roll_No || undefined,
      Phone_No: targetForm.Phone_No || undefined,
      Program: targetForm.Program || undefined,
      Department_Name: targetForm.Department_Name || undefined,
    };

    try {
      if (editingTarget) {
        await updateTarget(editingTarget.Target_Id, payload);
      } else {
        await createTarget(payload);
      }
      setOpenTargetDialog(false);
      setEditingTarget(null);
      setTargetForm({ Name: '', Roll_No: '', Phone_No: '', Department_Name: '', Program: '' });
      await queryClient.invalidateQueries({ queryKey: ['db-targets'] });
    } catch (err) {
      setActionError((err as Error).message);
    } finally {
      setSavingTarget(false);
    }
  };

  const handleDeleteTarget = async (id: string) => {
    try {
      setActionError(null);
      await deleteTarget(id);
      await queryClient.invalidateQueries({ queryKey: ['db-targets'] });
    } catch (err) {
      setActionError((err as Error).message);
    }
  };

  const handleImportTargets = async () => {
    if (!targetFile) return;
    setImportError(null);
    setActionError(null);
    setImporting(true);
    try {
      await importTargets(targetFile);
      setTargetFile(null);
      await queryClient.invalidateQueries({ queryKey: ['db-targets'] });
    } catch (err) {
      setImportError((err as Error).message);
    } finally {
      setImporting(false);
    }
  };

  const handleSaveModel = async () => {
    setActionError(null);
    setSavingModel(true);
    const payload: Partial<ModelRecord> = {
      Model_Name: modelForm.Model_Name || undefined,
      Model_Version: modelForm.Model_Version || undefined,
      Model_Details: modelForm.Model_Details || undefined,
    };

    if (!editingModel) {
      payload.Model_Id = modelForm.Model_Id || undefined;
    }

    try {
      if (editingModel) {
        await updateModel(editingModel.Model_Id, payload);
      } else {
        await createModel(payload);
      }
      setOpenModelDialog(false);
      setEditingModel(null);
      setModelForm({ Model_Id: '', Model_Name: '', Model_Version: '', Model_Details: '' });
      await queryClient.invalidateQueries({ queryKey: ['db-models'] });
    } catch (err) {
      setActionError((err as Error).message);
    } finally {
      setSavingModel(false);
    }
  };

  const handleDeleteModel = async (id: string) => {
    try {
      setActionError(null);
      await deleteModel(id);
      await queryClient.invalidateQueries({ queryKey: ['db-models'] });
    } catch (err) {
      setActionError((err as Error).message);
    }
  };

  const handleSaveEmotion = async () => {
    setActionError(null);
    setSavingEmotion(true);
    const payload: Partial<EmotionRecord> = {
      Emotion: emotionForm.Emotion || undefined,
    };

    if (!editingEmotion) {
      payload.Emotion_Id = emotionForm.Emotion_Id || undefined;
    }

    try {
      if (editingEmotion) {
        await updateEmotion(editingEmotion.Emotion_Id, payload);
      } else {
        await createEmotion(payload);
      }
      setOpenEmotionDialog(false);
      setEditingEmotion(null);
      setEmotionForm({ Emotion_Id: '', Emotion: '' });
      await queryClient.invalidateQueries({ queryKey: ['db-emotions'] });
    } catch (err) {
      setActionError((err as Error).message);
    } finally {
      setSavingEmotion(false);
    }
  };

  const handleDeleteEmotion = async (id: string) => {
    try {
      setActionError(null);
      await deleteEmotion(id);
      await queryClient.invalidateQueries({ queryKey: ['db-emotions'] });
    } catch (err) {
      setActionError((err as Error).message);
    }
  };

  const handleSaveAdmin = async () => {
    setActionError(null);
    setSavingAdmin(true);
    const payload: Partial<AdminRecord> = {
      Email: adminForm.Email || undefined,
    };

    if (adminForm.Password) {
      payload.Password = adminForm.Password;
    }

    if (!editingAdmin) {
      payload.Admin_Id = adminForm.Admin_Id || undefined;
    }

    try {
      if (editingAdmin) {
        await updateAdmin(editingAdmin.Admin_Id, payload);
      } else {
        await createAdmin(payload);
      }
      setOpenAdminDialog(false);
      setEditingAdmin(null);
      setAdminForm({ Email: '', Password: '' });
      await queryClient.invalidateQueries({ queryKey: ['db-admins'] });
    } catch (err) {
      setActionError((err as Error).message);
    } finally {
      setSavingAdmin(false);
    }
  };

  const handleDeleteAdmin = async (id: string) => {
    try {
      setActionError(null);
      await deleteAdmin(id);
      await queryClient.invalidateQueries({ queryKey: ['db-admins'] });
    } catch (err) {
      setActionError((err as Error).message);
    }
  };

  const handleSaveCall = async () => {
    setActionError(null);
    setSavingCall(true);
    const durationNumber = callForm.Duration ? Number(callForm.Duration) : undefined;
    const payload: Partial<CallRecord> = {
      Target_Id: callForm.Target_Id || undefined,
      Model_Id: callForm.Model_Id || undefined,
      Emotion_Id: callForm.Emotion_Id || undefined,
      Call_Sid: callForm.Call_Sid || undefined,
      Status: callForm.Status || undefined,
      Scheduled_Time: callForm.Scheduled_Time || undefined,
      Started_Time: callForm.Started_Time || undefined,
      Duration: Number.isNaN(durationNumber) ? undefined : durationNumber,
      Recording_Url: callForm.Recording_Url || undefined,
    };

    try {
      if (editingCall) {
        await updateCall(editingCall.Call_Id, payload);
      } else {
        await createCall(payload);
      }
      setOpenCallDialog(false);
      setEditingCall(null);
      setCallForm({ Target_Id: '', Model_Id: '', Emotion_Id: '', Call_Sid: '', Status: '', Scheduled_Time: '', Started_Time: '', Duration: '', Recording_Url: '' });
      await queryClient.invalidateQueries({ queryKey: ['db-calls'] });
    } catch (err) {
      setActionError((err as Error).message);
    } finally {
      setSavingCall(false);
    }
  };

  const handleDeleteCall = async (id: string) => {
    try {
      setActionError(null);
      await deleteCall(id);
      await queryClient.invalidateQueries({ queryKey: ['db-calls'] });
    } catch (err) {
      setActionError((err as Error).message);
    }
  };

  const handleSaveFlagged = async () => {
    setActionError(null);
    setSavingFlagged(true);

    if (!flaggedForm.Target_Id) {
      setActionError('Target ID is required');
      setSavingFlagged(false);
      return;
    }

    const payload: Partial<FlaggedTargetRecord> = {
      Target_Id: flaggedForm.Target_Id || undefined,
    };

    try {
      if (editingFlag) {
        await updateFlaggedTarget(editingFlag.Flag_Id, payload);
      } else {
        await createFlaggedTarget({ Target_Id: flaggedForm.Target_Id });
      }
      setOpenFlaggedDialog(false);
      setEditingFlag(null);
      setFlaggedForm({ Target_Id: '' });
      await queryClient.invalidateQueries({ queryKey: ['db-flagged'] });
    } catch (err) {
      setActionError((err as Error).message);
    } finally {
      setSavingFlagged(false);
    }
  };

  const handleDeleteFlagged = async (id: string) => {
    try {
      setActionError(null);
      await deleteFlaggedTarget(id);
      await queryClient.invalidateQueries({ queryKey: ['db-flagged'] });
    } catch (err) {
      setActionError((err as Error).message);
    }
  };

  const targetColumns = useMemo<Array<{ key: keyof TargetRecord; label: string }>>(
    () => [
      { key: 'Name', label: 'Name' },
      { key: 'Roll_No', label: 'Roll_No' },
      { key: 'Phone_No', label: 'Phone_No' },
      { key: 'Department_Name', label: 'Department_Name' },
      { key: 'Program', label: 'Program' },
    ],
    []
  );

  const modelColumns = useMemo<Array<{ key: keyof ModelRecord; label: string }>>(
    () => [
      { key: 'Model_Id', label: 'ID' },
      { key: 'Model_Name', label: 'Name' },
      { key: 'Model_Version', label: 'Version' },
      { key: 'Model_Details', label: 'Details' },
    ],
    []
  );

  const emotionColumns = useMemo<Array<{ key: keyof EmotionRecord; label: string }>>(
    () => [
      { key: 'Emotion_Id', label: 'ID' },
      { key: 'Emotion', label: 'Emotion' },
    ],
    []
  );

  const adminColumns = useMemo<Array<{ key: keyof AdminRecord; label: string }>>(
    () => [
      { key: 'Admin_Id', label: 'ID' },
      { key: 'Email', label: 'Email' },
      { key: 'Password', label: 'Password' },
    ],
    []
  );

  const callColumns = useMemo<Array<{ key: keyof CallRecord; label: string }>>(
    () => [
      { key: 'Call_Id', label: 'ID' },
      { key: 'Target_Id', label: 'Target' },
      { key: 'Model_Id', label: 'Model' },
      { key: 'Emotion_Id', label: 'Emotion' },
      { key: 'Call_Sid', label: 'Call SID' },
      { key: 'Status', label: 'Status' },
      { key: 'Scheduled_Time', label: 'Scheduled' },
      { key: 'Started_Time', label: 'Started' },
      { key: 'Duration', label: 'Duration' },
      { key: 'Recording_Url', label: 'Recording URL' },
    ],
    []
  );

  const flaggedColumns = useMemo<Array<{ key: keyof FlaggedTargetRecord; label: string }>>(
    () => [
      { key: 'Flag_Id', label: 'ID' },
      { key: 'Target_Id', label: 'Target' },
      { key: 'Call_Scheduled_DateTime', label: 'Call Scheduled DateTime' },
    ],
    []
  );

  return (
    <Box>
      <PageHeader title="Database Management" subtitle="Inspect and edit core entities." />

      {(targetsQuery.error || modelsQuery.error || emotionsQuery.error || adminsQuery.error || callsQuery.error || flaggedQuery.error) && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Failed to load some data. Please refresh.
        </Alert>
      )}

      {actionError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {actionError}
        </Alert>
      )}

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Tabs value={tab} onChange={(_, v) => setTab(v)} variant="scrollable" scrollButtons="auto">
            <Tab label="Targets" value="targets" />
            <Tab label="Models" value="models" />
            <Tab label="Emotions" value="emotions" />
            <Tab label="Admins" value="admins" />
            <Tab label="Calls" value="calls" />
            <Tab label="Flagged Targets" value="flagged" />
          </Tabs>
        </CardContent>
      </Card>

      {tab === 'targets' && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} justifyContent="space-between" alignItems={{ xs: 'stretch', md: 'center' }}>
              <Typography variant="h6">Targets</Typography>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} alignItems={{ xs: 'flex-start', sm: 'center' }}>
                <Button
                  variant="outlined"
                  startIcon={<UploadFileIcon />}
                  component="label"
                  disabled={importing}
                >
                  Bulk Import Targets (CSV/XLSX)
                  <input
                    type="file"
                    accept=".csv, application/vnd.ms-excel, application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    hidden
                    onChange={(e) => setTargetFile(e.target.files?.[0] ?? null)}
                  />
                </Button>
                <Button
                  variant="contained"
                  startIcon={<AddIcon />}
                  onClick={() => {
                    setEditingTarget(null);
                    setTargetForm({ Name: '', Roll_No: '', Phone_No: '', Department_Name: '', Program: '' });
                    setOpenTargetDialog(true);
                  }}
                >
                  Add Target
                </Button>
              </Stack>
            </Stack>

            <Typography variant="body2" color="text.secondary" sx={{ mt: 1, mb: 1 }}>
              Required Fields: (Name, Roll_No, Phone_No) Optional Fields: (Department_Name, Program). Use these exact field names in bulk import files.
            </Typography>

            {importError && (
              <Alert severity="error" sx={{ mt: 1 }}>
                {importError}
              </Alert>
            )}

            {targetsQuery.isLoading && <LoadingState label="Loading targets…" />}

            {targetsQuery.data && (
              <SimpleTable<TargetRecord>
                rows={targetsQuery.data}
                columns={targetColumns}
                getRowId={(row) => row.Target_Id}
                actions={(row) => (
                  <Stack direction="row" spacing={1}>
                    <Button
                      size="small"
                      variant="text"
                      startIcon={<EditIcon />}
                      onClick={() => {
                        setEditingTarget(row);
                        setTargetForm({
                          Name: row.Name || '',
                          Roll_No: (row as any).Roll_No || '',
                          Phone_No: row.Phone_No || '',
                          Department_Name: row.Department_Name || '',
                          Program: (row as any).Program || '',
                        });
                        setOpenTargetDialog(true);
                      }}
                    >
                      Edit
                    </Button>
                    <Button
                      size="small"
                      color="error"
                      variant="text"
                      startIcon={<DeleteIcon />}
                      onClick={() => handleDeleteTarget(row.Target_Id)}
                    >
                      Delete
                    </Button>
                  </Stack>
                )}
              />
            )}
          </CardContent>
        </Card>
      )}

      {tab === 'models' && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Models</Typography>
              <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setEditingModel(null); setModelForm({ Model_Id: '', Model_Name: '', Model_Version: '', Model_Details: '' }); setOpenModelDialog(true); }}>
                Add Model
              </Button>
            </Stack>
            {modelsQuery.isLoading && <LoadingState label="Loading models…" />}
            {modelsQuery.data && (
              <SimpleTable<ModelRecord>
                rows={modelsQuery.data}
                columns={modelColumns}
                getRowId={(row) => row.Model_Id}
                actions={(row) => (
                  <Stack direction="row" spacing={1}>
                    <Button size="small" startIcon={<EditIcon />} onClick={() => { setEditingModel(row); setModelForm({ Model_Id: row.Model_Id || '', Model_Name: row.Model_Name || '', Model_Version: row.Model_Version || '', Model_Details: row.Model_Details || '' }); setOpenModelDialog(true); }}>Edit</Button>
                    <Button size="small" color="error" startIcon={<DeleteIcon />} onClick={() => handleDeleteModel(row.Model_Id)}>Delete</Button>
                  </Stack>
                )}
              />
            )}
          </CardContent>
        </Card>
      )}

      {tab === 'emotions' && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Emotions</Typography>
              <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setEditingEmotion(null); setEmotionForm({ Emotion_Id: '', Emotion: '' }); setOpenEmotionDialog(true); }}>
                Add Emotion
              </Button>
            </Stack>
            {emotionsQuery.isLoading && <LoadingState label="Loading emotions…" />}
            {emotionsQuery.data && (
              <SimpleTable<EmotionRecord>
                rows={emotionsQuery.data}
                columns={emotionColumns}
                getRowId={(row) => row.Emotion_Id}
                actions={(row) => (
                  <Stack direction="row" spacing={1}>
                    <Button size="small" startIcon={<EditIcon />} onClick={() => { setEditingEmotion(row); setEmotionForm({ Emotion_Id: row.Emotion_Id || '', Emotion: row.Emotion || '' }); setOpenEmotionDialog(true); }}>Edit</Button>
                    <Button size="small" color="error" startIcon={<DeleteIcon />} onClick={() => handleDeleteEmotion(row.Emotion_Id)}>Delete</Button>
                  </Stack>
                )}
              />
            )}
          </CardContent>
        </Card>
      )}

      {tab === 'admins' && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Admins</Typography>
              <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setEditingAdmin(null); setAdminForm({ Email: '', Password: '' }); setOpenAdminDialog(true); }}>
                Add Admin
              </Button>
            </Stack>
            {adminsQuery.isLoading && <LoadingState label="Loading admins…" />}
            {adminsQuery.data && (
              <SimpleTable<AdminRecord>
                rows={adminsQuery.data}
                columns={adminColumns}
                getRowId={(row) => row.Admin_Id}
                actions={(row) => (
                  <Stack direction="row" spacing={1}>
                    <Button size="small" startIcon={<EditIcon />} onClick={() => { setEditingAdmin(row); setAdminForm({ Admin_Id: row.Admin_Id, Email: row.Email || '', Password: '' }); setOpenAdminDialog(true); }}>Edit</Button>
                    <Button size="small" color="error" startIcon={<DeleteIcon />} onClick={() => handleDeleteAdmin(row.Admin_Id)}>Delete</Button>
                  </Stack>
                )}
              />
            )}
          </CardContent>
        </Card>
      )}

      {tab === 'calls' && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Calls</Typography>
              <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setEditingCall(null); setCallForm({ Target_Id: '', Model_Id: '', Emotion_Id: '', Call_Sid: '', Status: '', Scheduled_Time: '', Started_Time: '', Duration: '', Recording_Url: '' }); setOpenCallDialog(true); }}>
                Add Call
              </Button>
            </Stack>
            {callsQuery.isLoading && <LoadingState label="Loading calls…" />}
            {callsQuery.data && (
              <SimpleTable<CallRecord>
                rows={callsQuery.data}
                columns={callColumns}
                getRowId={(row) => row.Call_Id}
                actions={(row) => (
                  <Stack direction="row" spacing={1}>
                    <Button size="small" startIcon={<EditIcon />} onClick={() => {
                      setEditingCall(row);
                      setCallForm({
                        Target_Id: row.Target_Id || '',
                        Model_Id: row.Model_Id || '',
                        Emotion_Id: row.Emotion_Id || '',
                        Call_Sid: row.Call_Sid || '',
                        Status: row.Status || '',
                        Scheduled_Time: row.Scheduled_Time || '',
                        Started_Time: row.Started_Time || '',
                        Duration: row.Duration != null ? String(row.Duration) : '',
                        Recording_Url: row.Recording_Url || '',
                      });
                      setOpenCallDialog(true);
                    }}>Edit</Button>
                    <Button size="small" color="error" startIcon={<DeleteIcon />} onClick={() => handleDeleteCall(row.Call_Id)}>Delete</Button>
                  </Stack>
                )}
              />
            )}
          </CardContent>
        </Card>
      )}

      {tab === 'flagged' && (
        <Card sx={{ mb: 2 }}>
          <CardContent>
            <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Flagged Targets</Typography>
              <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setEditingFlag(null); setFlaggedForm({ Target_Id: '' }); setOpenFlaggedDialog(true); }}>
                Flag Target
              </Button>
            </Stack>
            {flaggedQuery.isLoading && <LoadingState label="Loading flagged targets…" />}
            {flaggedQuery.data && (
              <SimpleTable<FlaggedTargetRecord>
                rows={flaggedQuery.data}
                columns={flaggedColumns}
                getRowId={(row, idx) => row.Flag_Id ?? String(idx)}
                actions={(row) => (
                  <Stack direction="row" spacing={1}>
                    <Button size="small" startIcon={<EditIcon />} onClick={() => { setEditingFlag(row); setFlaggedForm({ Target_Id: row.Target_Id || '' }); setOpenFlaggedDialog(true); }}>Edit</Button>
                    <Button size="small" color="error" startIcon={<DeleteIcon />} onClick={() => handleDeleteFlagged(row.Flag_Id)}>Delete</Button>
                  </Stack>
                )}
              />
            )}
          </CardContent>
        </Card>
      )}

      <Dialog open={openTargetDialog} onClose={() => setOpenTargetDialog(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editingTarget ? 'Edit Target' : 'Add Target'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField
              label="Name"
              value={targetForm.Name}
              onChange={(e) => setTargetForm((f) => ({ ...f, Name: e.target.value }))}
            />
            <TextField
              label="Roll_No"
              value={targetForm.Roll_No}
              onChange={(e) => setTargetForm((f) => ({ ...f, Roll_No: e.target.value }))}
            />
            <TextField
              label="Phone_No"
              value={targetForm.Phone_No}
              onChange={(e) => setTargetForm((f) => ({ ...f, Phone_No: e.target.value }))}
            />
            <TextField
              label="Department_Name"
              value={targetForm.Department_Name}
              onChange={(e) => setTargetForm((f) => ({ ...f, Department_Name: e.target.value }))}
            />
            <TextField
              label="Program"
              value={targetForm.Program}
              onChange={(e) => setTargetForm((f) => ({ ...f, Program: e.target.value }))}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenTargetDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveTarget} disabled={savingTarget}>
            {editingTarget ? 'Update' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={Boolean(targetFile)} onClose={() => setTargetFile(null)} fullWidth maxWidth="sm">
        <DialogTitle>Import Targets</DialogTitle>
        <DialogContent>
          <Typography variant="body2">Ready to import file: {targetFile?.name}</Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTargetFile(null)}>Cancel</Button>
          <Button variant="contained" onClick={handleImportTargets} startIcon={<UploadFileIcon />} disabled={importing}>
            Import
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openModelDialog} onClose={() => setOpenModelDialog(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editingModel ? 'Edit Model' : 'Add Model'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            {!editingModel && (
              <TextField
                label="Model ID"
                value={modelForm.Model_Id}
                onChange={(e) => setModelForm((f) => ({ ...f, Model_Id: e.target.value }))}
              />
            )}
            <TextField
              label="Name"
              value={modelForm.Model_Name}
              onChange={(e) => setModelForm((f) => ({ ...f, Model_Name: e.target.value }))}
            />
            <TextField
              label="Version"
              value={modelForm.Model_Version}
              onChange={(e) => setModelForm((f) => ({ ...f, Model_Version: e.target.value }))}
            />
            <TextField
              label="Details"
              value={modelForm.Model_Details}
              onChange={(e) => setModelForm((f) => ({ ...f, Model_Details: e.target.value }))}
              multiline
              minRows={2}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenModelDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveModel} disabled={savingModel}>
            {editingModel ? 'Update' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openEmotionDialog} onClose={() => setOpenEmotionDialog(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editingEmotion ? 'Edit Emotion' : 'Add Emotion'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            {!editingEmotion && (
              <TextField
                label="Emotion ID"
                value={emotionForm.Emotion_Id}
                onChange={(e) => setEmotionForm((f) => ({ ...f, Emotion_Id: e.target.value }))}
              />
            )}
            <TextField
              label="Emotion"
              value={emotionForm.Emotion}
              onChange={(e) => setEmotionForm((f) => ({ ...f, Emotion: e.target.value }))}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenEmotionDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveEmotion} disabled={savingEmotion}>
            {editingEmotion ? 'Update' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openAdminDialog} onClose={() => setOpenAdminDialog(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editingAdmin ? 'Edit Admin' : 'Add Admin'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField
              label="Email"
              value={adminForm.Email}
              onChange={(e) => setAdminForm((f) => ({ ...f, Email: e.target.value }))}
            />
            <TextField
              label="Password"
              type="password"
              value={adminForm.Password}
              onChange={(e) => setAdminForm((f) => ({ ...f, Password: e.target.value }))}
              helperText={editingAdmin ? 'Leave blank to keep current password' : undefined}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenAdminDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveAdmin} disabled={savingAdmin}>
            {editingAdmin ? 'Update' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openCallDialog} onClose={() => setOpenCallDialog(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editingCall ? 'Edit Call' : 'Add Call'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField
              label="Target ID"
              value={callForm.Target_Id}
              onChange={(e) => setCallForm((f) => ({ ...f, Target_Id: e.target.value }))}
            />
            <TextField
              label="Model ID"
              value={callForm.Model_Id}
              onChange={(e) => setCallForm((f) => ({ ...f, Model_Id: e.target.value }))}
            />
            <TextField
              label="Emotion ID"
              value={callForm.Emotion_Id}
              onChange={(e) => setCallForm((f) => ({ ...f, Emotion_Id: e.target.value }))}
            />
            <TextField
              label="Call SID"
              value={callForm.Call_Sid}
              onChange={(e) => setCallForm((f) => ({ ...f, Call_Sid: e.target.value }))}
            />
            <TextField
              label="Status"
              value={callForm.Status}
              onChange={(e) => setCallForm((f) => ({ ...f, Status: e.target.value }))}
            />
            <TextField
              label="Scheduled Time"
              value={callForm.Scheduled_Time}
              onChange={(e) => setCallForm((f) => ({ ...f, Scheduled_Time: e.target.value }))}
              placeholder="YYYY-MM-DD HH:MM:SS"
            />
            <TextField
              label="Started Time"
              value={callForm.Started_Time}
              onChange={(e) => setCallForm((f) => ({ ...f, Started_Time: e.target.value }))}
              placeholder="YYYY-MM-DD HH:MM:SS"
            />
            <TextField
              label="Duration (seconds)"
              value={callForm.Duration}
              onChange={(e) => setCallForm((f) => ({ ...f, Duration: e.target.value }))}
            />
            <TextField
              label="Recording URL"
              value={callForm.Recording_Url}
              onChange={(e) => setCallForm((f) => ({ ...f, Recording_Url: e.target.value }))}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenCallDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveCall} disabled={savingCall}>
            {editingCall ? 'Update' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      <Dialog open={openFlaggedDialog} onClose={() => setOpenFlaggedDialog(false)} fullWidth maxWidth="sm">
        <DialogTitle>{editingFlag ? 'Edit Flagged Target' : 'Flag Target'}</DialogTitle>
        <DialogContent>
          <Stack spacing={2} mt={1}>
            <TextField
              label="Target ID"
              value={flaggedForm.Target_Id}
              onChange={(e) => setFlaggedForm((f) => ({ ...f, Target_Id: e.target.value }))}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenFlaggedDialog(false)}>Cancel</Button>
          <Button variant="contained" onClick={handleSaveFlagged} disabled={savingFlagged}>
            {editingFlag ? 'Update' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
