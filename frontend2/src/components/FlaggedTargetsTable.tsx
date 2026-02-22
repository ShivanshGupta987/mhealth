import { DataGrid } from '@mui/x-data-grid';
import type { GridColDef } from '@mui/x-data-grid';
import { Paper, Button } from '@mui/material';
import type { FlaggedTarget } from '../api/targetMonitoring';

interface FlaggedTargetsTableProps {
  rows: FlaggedTarget[];
  onUnflag: (targetId: string) => void;
  loading?: boolean;
}

export function FlaggedTargetsTable({ rows, onUnflag, loading }: FlaggedTargetsTableProps) {
  const columns: GridColDef<FlaggedTarget>[] = [
    { field: 'Target_Id', headerName: 'Target ID', flex: 1, minWidth: 200 },
    { field: 'Name', headerName: 'Name', flex: 0.8, minWidth: 140 },
    { field: 'Batch', headerName: 'Batch', flex: 0.3, minWidth: 90 },
    { field: 'Department_Name', headerName: 'Department', flex: 0.7, minWidth: 160 },
    { field: 'Phone_No', headerName: 'Phone', flex: 0.6, minWidth: 140 },
    { field: 'Call_Scheduled_DateTime', headerName: 'Call Scheduled DateTime', flex: 0.9, minWidth: 190 },
    {
      field: 'actions',
      headerName: 'Actions',
      sortable: false,
      filterable: false,
      width: 140,
      renderCell: (params) => (
        <Button size="small" variant="outlined" onClick={() => onUnflag(params.row.Target_Id)}>
          Unflag
        </Button>
      ),
    },
  ];

  const gridRows = rows.map((row) => ({ ...row, id: row.Flag_Id }));

  return (
    <Paper elevation={0} sx={{ height: 480, border: '1px solid', borderColor: 'divider' }}>
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

export default FlaggedTargetsTable;
