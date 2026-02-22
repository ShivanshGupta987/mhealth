import { DataGrid } from '@mui/x-data-grid';
import type { GridColDef, GridRowsProp } from '@mui/x-data-grid';
import { Paper } from '@mui/material';
import { useMemo } from 'react';
import type { CallHistoryEntry } from '../api/callMonitoring';

function formatDateTime(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

type CallHistoryRow = CallHistoryEntry & { id: string };

interface CallMonitoringTableProps {
  rows: CallHistoryEntry[];
  loading?: boolean;
}

export function CallMonitoringTable({ rows, loading }: CallMonitoringTableProps) {
  const columns = useMemo<GridColDef[]>(
    () => [
      { field: 'Call_Id', headerName: 'Call ID', flex: 1, minWidth: 220 },
      {
        field: 'Target_Name',
        headerName: 'Target',
        flex: 1,
        minWidth: 160,
        valueGetter: ({ row }) => (row as CallHistoryEntry).Target_Name || 'Unknown',
      },
      {
        field: 'Department_Name',
        headerName: 'Department',
        flex: 0.8,
        minWidth: 160,
        valueGetter: ({ row }) => (row as CallHistoryEntry).Department_Name || '—',
      },
      {
        field: 'Batch',
        headerName: 'Batch',
        flex: 0.4,
        minWidth: 100,
        valueGetter: ({ row }) => (row as CallHistoryEntry).Batch ?? '—',
      },
      {
        field: 'Status',
        headerName: 'Status',
        flex: 1,
        minWidth: 220,
        valueGetter: ({ row }) => (row as CallHistoryEntry).Status || 'Unknown',
      },
      {
        field: 'Scheduled_Time',
        headerName: 'Scheduled',
        flex: 0.9,
        minWidth: 190,
        valueGetter: ({ row }) => formatDateTime((row as CallHistoryEntry).Scheduled_Time),
      },
      {
        field: 'Started_Time',
        headerName: 'Started',
        flex: 0.9,
        minWidth: 190,
        valueGetter: ({ row }) => formatDateTime((row as CallHistoryEntry).Started_Time),
      },
      {
        field: 'Duration',
        headerName: 'Duration (s)',
        type: 'number',
        flex: 0.4,
        minWidth: 140,
        valueGetter: ({ row }) => (row as CallHistoryEntry).Duration ?? 0,
      },
    ],
    [],
  );

  const gridRows: GridRowsProp<CallHistoryRow> = rows.map((row) => ({ ...row, id: row.Call_Id }));

  return (
    <Paper elevation={0} sx={{ height: 520, border: '1px solid', borderColor: 'divider' }}>
      <DataGrid
        rows={gridRows}
        columns={columns}
        loading={loading}
        disableRowSelectionOnClick
        pageSizeOptions={[10, 25, 50]}
        initialState={{
          pagination: {
            paginationModel: { pageSize: 10 },
          },
        }}
      />
    </Paper>
  );
}

export default CallMonitoringTable;
