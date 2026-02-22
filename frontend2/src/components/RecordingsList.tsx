import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Chip,
  Stack,
  Typography,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import type { CallHistoryEntry } from '../api/counsellor';

interface RecordingsListProps {
  rows: CallHistoryEntry[];
  apiBaseUrl: string;
}

function buildRecordingUrl(entry: CallHistoryEntry, apiBaseUrl: string) {
  if (entry.Recording_Proxy_Url) {
    return `${apiBaseUrl}${entry.Recording_Proxy_Url}`;
  }
  return entry.Recording_Url || '';
}

function formatTitle(entry: CallHistoryEntry) {
  const started = entry.Started_Time ? new Date(entry.Started_Time) : null;
  const formatted = started
    ? new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(started)
    : 'Unknown time';
  return `${formatted} — ${entry.Status || 'Status N/A'}`;
}

export function RecordingsList({ rows, apiBaseUrl }: RecordingsListProps) {
  const recordings = rows.filter((row) => row.Recording_Proxy_Url || row.Recording_Url);

  if (!recordings.length) {
    return (
      <Box sx={{ border: '1px dashed', borderColor: 'divider', borderRadius: 2, p: 4, textAlign: 'center' }}>
        <Typography variant="body1" color="text.secondary">
          No recordings available for this selection.
        </Typography>
      </Box>
    );
  }

  return (
    <Stack spacing={1.5}>
      {recordings.map((entry) => {
        const url = buildRecordingUrl(entry, apiBaseUrl);
        if (!url) return null;

        return (
          <Accordion key={entry.Call_Id} disableGutters>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}> 
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1} flex={1}>
                <Typography variant="subtitle1">{formatTitle(entry)}</Typography>
                <Chip label={entry.Emotion || 'Pending'} size="small" color="secondary" sx={{ alignSelf: 'flex-start' }} />
              </Stack>
            </AccordionSummary>
            <AccordionDetails>
              <Stack spacing={1}>
                <Typography variant="body2" color="text.secondary">
                  Duration: {entry.Duration ?? 'N/A'} seconds • Attempts logged: {entry.Attempts ?? 0}
                </Typography>
                <audio controls src={url} style={{ width: '100%' }} />
              </Stack>
            </AccordionDetails>
          </Accordion>
        );
      })}
    </Stack>
  );
}

export default RecordingsList;
