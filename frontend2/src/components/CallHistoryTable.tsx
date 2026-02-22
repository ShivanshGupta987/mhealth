import { DataGrid } from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import type { GridRenderCellParams } from '@mui/x-data-grid';
import { Paper } from '@mui/material';
import { useMemo } from 'react';
import type { CallHistoryEntry } from '../api/counsellor';

export interface CallHistoryTableProps {
  rows: CallHistoryEntry[];
  loading?: boolean;
}

type RowParams = { row: CallHistoryEntry };

function formatDate(value?: string | null) {
  if (!value) return '—';
  const date = new Date(value);
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

export function CallHistoryTable({ rows, loading }: CallHistoryTableProps) {
  const columns = useMemo<GridColDef<CallHistoryEntry>[]>(
    () => [
      { field: 'Call_Id', headerName: 'Call ID', flex: 1, minWidth: 220 },
      {
        field: 'Started_Time',
        headerName: 'Started',
        flex: 1,
        minWidth: 180,
        valueGetter: (params: RowParams) => params.row.Started_Time,
        renderCell: (params: GridRenderCellParams<CallHistoryEntry, string | null>) =>
          formatDate(params.row.Started_Time),
      },
      {
        field: 'Status',
        headerName: 'Status',
        flex: 0.8,
        minWidth: 140,
      },
      {
        field: 'Emotion',
        headerName: 'Emotion',
        flex: 0.6,
        minWidth: 130,
        valueGetter: (params: RowParams) => params.row.Emotion || 'Pending',
      },
      {
        field: 'Duration',
        headerName: 'Duration (s)',
        type: 'number',
        flex: 0.4,
        minWidth: 140,
        valueGetter: (params: RowParams) => params.row.Duration ?? 0,
      },
      {
        field: 'Attempts',
        headerName: 'Attempts',
        type: 'number',
        flex: 0.3,
        minWidth: 120,
        valueGetter: (params: RowParams) => params.row.Attempts ?? 0,
      },
    ],
    [],
  );

  const mappedRows = rows.map((row) => ({ ...row, id: row.Call_Id }));

  return (
    <Paper elevation={0} sx={{ height: 420, border: '1px solid', borderColor: 'divider' }}>
      <DataGrid
        rows={mappedRows}
        columns={columns}
        loading={loading}
        disableRowSelectionOnClick
        pageSizeOptions={[5, 10, 20]}
        initialState={{
          pagination: {
            paginationModel: { pageSize: 10 },
          },
        }}
      />
    </Paper>
  );
}

export default CallHistoryTable;
