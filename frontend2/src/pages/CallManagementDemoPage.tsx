import React, { ChangeEvent, useMemo, useRef, useState } from 'react';
import { Box, Button, Card, CardContent, Collapse, Divider, IconButton, Menu, MenuItem, Stack, Table, TableBody, TableCell, TableHead, TableRow, Tabs, Tab, TextField, Tooltip, Typography } from '@mui/material';
import CallEndIcon from '@mui/icons-material/CallEnd';
import PhoneMissedIcon from '@mui/icons-material/PhoneMissed';
import PhoneInTalkIcon from '@mui/icons-material/PhoneInTalk';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CloseIcon from '@mui/icons-material/Close';
import InfoIcon from '@mui/icons-material/InfoOutlined';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CheckBoxIcon from '@mui/icons-material/CheckBox';
import ArrowUpwardIcon from '@mui/icons-material/ArrowUpward';
import ArrowDownwardIcon from '@mui/icons-material/ArrowDownward';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import AddCircleOutlineIcon from '@mui/icons-material/AddCircleOutline';
// import CheckCircleIcon from '@mui/icons-material/CheckCircle';
  
type CallEntry = {
  times: string[];
  notes: string[];
  status: keyof typeof STATUS_MAP;
  analysis: keyof typeof ANALYSIS_ICONS;
  recording_available: boolean;
};

type Target = {
  scheduled: boolean;
  name: string;
  roll: string;
  dept: string;
  program: string;
  phone: string;
  last_call_status: keyof typeof STATUS_MAP;
  last_analysis: keyof typeof ANALYSIS_ICONS;
  last_recording: boolean;
};

type PotentialCase = {
  name: string;
  roll: string;
  phone: string;
  dept: string;
  program: string;
  callDateTime: string;
  lowAnalysisAt: string[];
  moderateAnalysisAt: string[];
  highAnalysisAt: string[];
};

const STATUS_MAP = {
  not_made: true,
  not_picked: true,
  picked_short: true,
  picked_full: true,
};

const STATUS_ICON_MAP: Record<keyof typeof STATUS_MAP, { left: React.ReactNode; right?: React.ReactNode }> = {
  not_made: {
    left: <CallEndIcon sx={{ color: '#d32f2f' }} fontSize="small" />,
  },
  not_picked: {
    left: <PhoneMissedIcon sx={{ color: '#d32f2f' }} fontSize="small" />,
  },
  picked_short: {
    left: <PhoneInTalkIcon sx={{ color: '#8e24aa' }} fontSize="small" />,
    right: <AccessTimeIcon sx={{ color: '#5e35b1' }} fontSize="small" />,
  },
  picked_full: {
    left: <PhoneInTalkIcon sx={{ color: '#8e24aa' }} fontSize="small" />,
    right: <CheckCircleIcon sx={{ color: '#2e7d32' }} fontSize="small" />,
  },
};

const renderStatusIconsCompact = (status: keyof typeof STATUS_MAP) => {
  const icons = STATUS_ICON_MAP[status];
  if (!icons) return null;
  return (
    <Stack direction="row" spacing={0.5} alignItems="center" flexWrap="nowrap">
      {icons.left}
      {icons.right}
    </Stack>
  );
};

const STATUS_SORT_ORDER = ['not_made', 'not_picked', 'picked_short', 'picked_full'];

const ANALYSIS_ICONS = {
  not_analyzed: <HelpOutlineIcon sx={{ color: '#d32f2f', fontSize: 18, verticalAlign: 'middle' }} />,
  low: <Typography component="span" sx={{ color: '#2e7d32', fontWeight: 600 }}>Low</Typography>,
  moderate: <Typography component="span" sx={{ color: '#ed6c02', fontWeight: 600 }}>Moderate</Typography>,
  high: <Typography component="span" sx={{ color: '#d32f2f', fontWeight: 700 }}>High (Potential Case)</Typography>,
};

const potentialCases: PotentialCase[] = [
  {
    name: 'Tanvi Kulkarni',
    roll: '24250301',
    phone: '9871112233',
    dept: 'Computer Science',
    program: 'BTech',
    callDateTime: '05-12-2025 15:10:12',
    lowAnalysisAt: ['22-11-2025 09:05:10', '10-11-2025 08:55:00'],
    moderateAnalysisAt: ['01-12-2025 11:45:12', '19-11-2025 12:05:45'],
    highAnalysisAt: ['28-11-2025 10:15:05', '15-10-2025 09:22:11', '07-10-2025 18:01:30'],
  },
  {
    name: 'Ayaan Sheikh',
    roll: '24250302',
    phone: '9862223344',
    dept: 'Mechanical',
    program: 'MTech',
    callDateTime: '06-12-2025 11:45:03',
    lowAnalysisAt: ['20-11-2025 08:30:00', '05-11-2025 07:42:50'],
    moderateAnalysisAt: ['28-11-2025 14:20:35', '17-11-2025 16:18:05', '02-11-2025 19:55:10'],
    highAnalysisAt: ['01-12-2025 09:55:22', '23-10-2025 21:10:00'],
  },
  {
    name: 'Muskaan Batra',
    roll: '24250303',
    phone: '9853334455',
    dept: 'Electrical',
    program: 'BTech',
    callDateTime: '07-12-2025 09:05:27',
    lowAnalysisAt: ['18-11-2025 16:12:40', '03-11-2025 08:10:25'],
    moderateAnalysisAt: ['25-11-2025 12:18:10', '11-11-2025 09:44:55'],
    highAnalysisAt: ['29-11-2025 17:20:18', '12-11-2025 18:00:00', '27-10-2025 13:05:05'],
  },
  {
    name: 'Kabir Malhotra',
    roll: '24250304',
    phone: '9844445566',
    dept: 'Civil',
    program: 'MTech',
    callDateTime: '03-12-2025 18:22:40',
    lowAnalysisAt: ['15-11-2025 10:40:10', '01-11-2025 07:15:45'],
    moderateAnalysisAt: ['22-11-2025 19:05:55', '12-11-2025 21:20:30'],
    highAnalysisAt: ['25-11-2025 12:45:02', '06-11-2025 08:55:10'],
  },
  {
    name: 'Simran Kaur',
    roll: '24250305',
    phone: '9835556677',
    dept: 'Chemical',
    program: 'PhD',
    callDateTime: '04-12-2025 14:33:18',
    lowAnalysisAt: ['17-11-2025 08:05:33', '09-11-2025 06:55:11'],
    moderateAnalysisAt: ['24-11-2025 15:14:22', '13-11-2025 13:48:00', '02-11-2025 18:19:22'],
    highAnalysisAt: ['26-11-2025 08:35:44', '05-11-2025 20:10:09'],
  },
  {
    name: 'Farhan Ali',
    roll: '24250306',
    phone: '9826667788',
    dept: 'Physics',
    program: 'BTech',
    callDateTime: '02-12-2025 12:05:55',
    lowAnalysisAt: ['12-11-2025 13:20:45', '28-10-2025 10:02:25'],
    moderateAnalysisAt: ['20-11-2025 17:55:05', '06-11-2025 12:30:30'],
    highAnalysisAt: ['24-11-2025 16:05:11', '14-11-2025 22:14:00'],
  },
  {
    name: 'Ishita Roy',
    roll: '24250307',
    phone: '9817778899',
    dept: 'Mathematics',
    program: 'MTech',
    callDateTime: '08-12-2025 10:48:09',
    lowAnalysisAt: ['21-11-2025 09:45:00', '07-11-2025 07:15:35'],
    moderateAnalysisAt: ['27-11-2025 10:10:55', '15-11-2025 17:25:05'],
    highAnalysisAt: ['30-11-2025 15:10:30', '19-10-2025 11:45:45', '03-10-2025 16:40:12'],
  },
  {
    name: 'Dev Patel',
    roll: '24250308',
    phone: '9808889900',
    dept: 'Biological Sciences',
    program: 'BTech',
    callDateTime: '01-12-2025 16:12:44',
    lowAnalysisAt: ['14-11-2025 07:40:22', '01-11-2025 06:58:18'],
    moderateAnalysisAt: ['21-11-2025 18:30:10', '11-11-2025 12:12:00', '27-10-2025 08:11:40'],
    highAnalysisAt: ['23-11-2025 09:02:55', '08-11-2025 09:35:05'],
  },
  {
    name: 'Aditi Nanda',
    roll: '24250309',
    phone: '9799990011',
    dept: 'Computer Science',
    program: 'PhD',
    callDateTime: '09-12-2025 08:20:33',
    lowAnalysisAt: ['16-11-2025 11:25:35', '02-11-2025 10:15:20'],
    moderateAnalysisAt: ['23-11-2025 20:14:55', '12-11-2025 14:05:05'],
    highAnalysisAt: ['02-12-2025 18:45:19', '14-11-2025 07:55:33', '05-10-2025 19:22:45'],
  },
  {
    name: 'Rudra Sengupta',
    roll: '24250310',
    phone: '9780001122',
    dept: 'Chemical',
    program: 'MTech',
    callDateTime: '10-12-2025 17:55:01',
    lowAnalysisAt: ['19-11-2025 10:20:30', '04-11-2025 11:11:11'],
    moderateAnalysisAt: ['27-11-2025 09:15:20', '13-11-2025 13:09:55'],
    highAnalysisAt: ['03-12-2025 14:25:33', '25-10-2025 20:05:05'],
  },
];

const initialTargets: Target[] = [
  { scheduled: false, name: 'Atharv Kulkarni', roll: '24250001', dept: 'Computer Science', program: 'BTech', phone: '9001112233', last_call_status: 'not_made', last_analysis: 'not_analyzed', last_recording: false },
  { scheduled: true, name: 'Shivansh Gupta', roll: '24250086', dept: 'Computer Science', program: 'MTech', phone: '9369049853', last_call_status: 'picked_full', last_analysis: 'low', last_recording: true },
  { scheduled: false, name: 'Priya Menon', roll: '24250123', dept: 'Mechanical', program: 'MTech', phone: '9876501234', last_call_status: 'picked_short', last_analysis: 'not_analyzed', last_recording: true },
  { scheduled: false, name: 'Sarthak Deshpande', roll: '24250099', dept: 'Mechanical', program: 'BTech', phone: '9000000000', last_call_status: 'not_picked', last_analysis: 'not_analyzed', last_recording: false },
  { scheduled: true, name: 'Ananya Sharma', roll: '24250045', dept: 'Electrical', program: 'BTech', phone: '9876543210', last_call_status: 'picked_full', last_analysis: 'high', last_recording: true },
  { scheduled: false, name: 'Rohan Verma', roll: '24250067', dept: 'Civil', program: 'MTech', phone: '9123456789', last_call_status: 'not_picked', last_analysis: 'not_analyzed', last_recording: false },
  { scheduled: true, name: 'Kavya Reddy', roll: '24250098', dept: 'Chemical', program: 'BTech', phone: '9234567890', last_call_status: 'picked_short', last_analysis: 'moderate', last_recording: true },
  { scheduled: false, name: 'Aditya Patel', roll: '24250034', dept: 'Computer Science', program: 'BTech', phone: '9345678901', last_call_status: 'picked_full', last_analysis: 'low', last_recording: true },
  { scheduled: false, name: 'Neha Singh', roll: '24250112', dept: 'Mathematics', program: 'MTech', phone: '9456789012', last_call_status: 'not_picked', last_analysis: 'not_analyzed', last_recording: false },
  { scheduled: true, name: 'Arjun Kumar', roll: '24250078', dept: 'Physics', program: 'PhD', phone: '9567890123', last_call_status: 'picked_short', last_analysis: 'moderate', last_recording: true },
  { scheduled: false, name: 'Riya Joshi', roll: '24250145', dept: 'Biological Sciences', program: 'MTech', phone: '9678901234', last_call_status: 'picked_full', last_analysis: 'high', last_recording: true },
  { scheduled: false, name: 'Vikram Desai', roll: '24250156', dept: 'Electrical', program: 'BTech', phone: '9789012345', last_call_status: 'not_picked', last_analysis: 'not_analyzed', last_recording: false },
  { scheduled: true, name: 'Meera Nair', roll: '24250167', dept: 'Chemical', program: 'MTech', phone: '9890123456', last_call_status: 'picked_short', last_analysis: 'low', last_recording: true },
  { scheduled: false, name: 'Karan Mehta', roll: '24250189', dept: 'Civil', program: 'BTech', phone: '9901234567', last_call_status: 'picked_full', last_analysis: 'high', last_recording: true },
  { scheduled: false, name: 'Divya Iyer', roll: '24250201', dept: 'Mechanical', program: 'MTech', phone: '9012345678', last_call_status: 'not_picked', last_analysis: 'not_analyzed', last_recording: false },
  { scheduled: true, name: 'Rahul Bhatt', roll: '24250223', dept: 'Computer Science', program: 'PhD', phone: '9123450987', last_call_status: 'picked_short', last_analysis: 'moderate', last_recording: true },
  { scheduled: false, name: 'Sneha Rao', roll: '24250234', dept: 'Physics', program: 'BTech', phone: '9234561098', last_call_status: 'picked_full', last_analysis: 'low', last_recording: true },
  { scheduled: false, name: 'Mihir Shah', roll: '24250250', dept: 'Mathematics', program: 'BTech', phone: '9123012345', last_call_status: 'not_made', last_analysis: 'not_analyzed', last_recording: false },
  { scheduled: true, name: 'Ritika Banerjee', roll: '24250251', dept: 'Electronics', program: 'MTech', phone: '9345601234', last_call_status: 'not_made', last_analysis: 'not_analyzed', last_recording: false },
];

const callHistory: Record<string, CallEntry[]> = {
  '24250001': [],
  '24250086': [
    { times: ['10-12-2025 15:30:10', '10-12-2025 15:30:15', '10-12-2025 15:33:15'], notes: ['Call made', 'Call picked', 'Call hungup with communication'], status: 'picked_full', analysis: 'high', recording_available: true },
    { times: ['08-12-2025 10:20:05', '08-12-2025 10:20:10', '08-12-2025 10:22:30'], notes: ['Call made', 'Call picked', 'Call hungup with short communication'], status: 'picked_short', analysis: 'moderate', recording_available: true },
    { times: ['05-12-2025 14:15:22'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250123': [
    { times: ['09-12-2025 11:25:40', '09-12-2025 11:25:45', '09-12-2025 11:27:10'], notes: ['Call made', 'Call picked', 'Call hungup with short communication'], status: 'picked_short', analysis: 'not_analyzed', recording_available: true },
    { times: ['07-12-2025 13:40:22', '07-12-2025 13:40:28', '07-12-2025 13:43:28'], notes: ['Call made', 'Call picked', 'Call hungup with communication'], status: 'picked_full', analysis: 'high', recording_available: true },
    { times: ['04-12-2025 10:05:15'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250099': [
    { times: ['10-12-2025 12:11:12'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
    { times: ['08-12-2025 09:30:25'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
    { times: ['06-12-2025 14:45:18'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250045': [
    { times: ['09-12-2025 14:20:10', '09-12-2025 14:20:15', '09-12-2025 14:23:15'], notes: ['Call made', 'Call picked', 'Call hungup with communication'], status: 'picked_full', analysis: 'high', recording_available: true },
    { times: ['07-12-2025 10:15:20', '07-12-2025 10:15:25', '07-12-2025 10:17:40'], notes: ['Call made', 'Call picked', 'Call hungup with short communication'], status: 'picked_short', analysis: 'moderate', recording_available: true },
    { times: ['05-12-2025 16:30:15'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250067': [
    { times: ['09-12-2025 09:40:22'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
    { times: ['07-12-2025 11:20:15'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250098': [
    { times: ['10-12-2025 13:10:30', '10-12-2025 13:10:35', '10-12-2025 13:12:45'], notes: ['Call made', 'Call picked', 'Call hungup with short communication'], status: 'picked_short', analysis: 'not_analyzed', recording_available: true },
    { times: ['08-12-2025 15:25:10', '08-12-2025 15:25:15', '08-12-2025 15:28:15'], notes: ['Call made', 'Call picked', 'Call hungup with communication'], status: 'picked_full', analysis: 'high', recording_available: true },
    { times: ['06-12-2025 09:50:25'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250034': [
    { times: ['10-12-2025 11:45:12', '10-12-2025 11:45:17', '10-12-2025 11:48:17'], notes: ['Call made', 'Call picked', 'Call hungup with communication'], status: 'picked_full', analysis: 'moderate', recording_available: true },
    { times: ['08-12-2025 14:30:20'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250112': [
    { times: ['09-12-2025 16:20:45'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
    { times: ['07-12-2025 12:10:30'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
    { times: ['05-12-2025 10:45:15'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250078': [
    { times: ['10-12-2025 10:30:20', '10-12-2025 10:30:25', '10-12-2025 10:32:40'], notes: ['Call made', 'Call picked', 'Call hungup with short communication'], status: 'picked_short', analysis: 'not_analyzed', recording_available: true },
    { times: ['08-12-2025 13:15:10', '08-12-2025 13:15:15', '08-12-2025 13:18:15'], notes: ['Call made', 'Call picked', 'Call hungup with communication'], status: 'picked_full', analysis: 'moderate', recording_available: true },
  ],
  '24250145': [
    { times: ['09-12-2025 15:40:35', '09-12-2025 15:40:40', '09-12-2025 15:43:40'], notes: ['Call made', 'Call picked', 'Call hungup with communication'], status: 'picked_full', analysis: 'high', recording_available: true },
    { times: ['07-12-2025 09:25:15', '07-12-2025 09:25:20', '07-12-2025 09:27:30'], notes: ['Call made', 'Call picked', 'Call hungup with short communication'], status: 'picked_short', analysis: 'not_analyzed', recording_available: true },
    { times: ['05-12-2025 11:50:25'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250156': [
    { times: ['09-12-2025 12:35:40'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
    { times: ['07-12-2025 14:20:30'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250167': [
    { times: ['10-12-2025 14:25:15', '10-12-2025 14:25:20', '10-12-2025 14:27:35'], notes: ['Call made', 'Call picked', 'Call hungup with short communication'], status: 'picked_short', analysis: 'not_analyzed', recording_available: true },
    { times: ['08-12-2025 11:40:25', '08-12-2025 11:40:30', '08-12-2025 11:43:30'], notes: ['Call made', 'Call picked', 'Call hungup with communication'], status: 'picked_full', analysis: 'low', recording_available: true },
    { times: ['06-12-2025 15:10:20'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250189': [
    { times: ['09-12-2025 13:50:30', '09-12-2025 13:50:35', '09-12-2025 13:53:35'], notes: ['Call made', 'Call picked', 'Call hungup with communication'], status: 'picked_full', analysis: 'high', recording_available: true },
    { times: ['07-12-2025 10:30:20'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250201': [
    { times: ['09-12-2025 11:15:25'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
    { times: ['07-12-2025 15:45:30'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
    { times: ['05-12-2025 13:20:15'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250223': [
    { times: ['10-12-2025 12:40:20', '10-12-2025 12:40:25', '10-12-2025 12:42:35'], notes: ['Call made', 'Call picked', 'Call hungup with short communication'], status: 'picked_short', analysis: 'not_analyzed', recording_available: true },
    { times: ['08-12-2025 09:50:15'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250234': [
    { times: ['10-12-2025 16:10:40', '10-12-2025 16:10:45', '10-12-2025 16:13:45'], notes: ['Call made', 'Call picked', 'Call hungup with communication'], status: 'picked_full', analysis: 'not_analyzed', recording_available: true },
    { times: ['08-12-2025 12:25:30', '08-12-2025 12:25:35', '08-12-2025 12:28:35'], notes: ['Call made', 'Call picked', 'Call hungup with communication'], status: 'picked_full', analysis: 'low', recording_available: true },
    { times: ['06-12-2025 14:15:20'], notes: ['Call made but not picked'], status: 'not_picked', analysis: 'not_analyzed', recording_available: false },
  ],
  '24250250': [],
  '24250251': [],
};

export default function CounsellorPage() {
  const [activeTab, setActiveTab] = useState<'targets' | 'flagged'>('targets');
  const [targets, setTargets] = useState<Target[]>(initialTargets);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [openDetails, setOpenDetails] = useState<Record<string, boolean>>({});
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortAscending, setSortAscending] = useState(true);
  const [flaggedSortColumn, setFlaggedSortColumn] = useState<keyof PotentialCase | null>(null);
  const [flaggedSortAscending, setFlaggedSortAscending] = useState(true);
  const [flaggedOpenDetails, setFlaggedOpenDetails] = useState<Record<string, boolean>>({});
  const [flaggedDetailTab, setFlaggedDetailTab] = useState<Record<string, 'low' | 'moderate' | 'high'>>({});
  const [flaggedSearch, setFlaggedSearch] = useState('');
  const [exportAnchor, setExportAnchor] = useState<null | HTMLElement>(null);
  const [targetSearch, setTargetSearch] = useState('');
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const toggleSelect = (roll: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(roll)) next.delete(roll);
      else next.add(roll);
      return next;
    });
  };

  const toggleDetails = (roll: string) => {
    setOpenDetails((prev) => ({ ...prev, [roll]: !prev[roll] }));
  };

  const toggleFlaggedDetails = (roll: string) => {
    setFlaggedOpenDetails((prev) => ({ ...prev, [roll]: !prev[roll] }));
  };

  const handleExportClick = (event: React.MouseEvent<HTMLButtonElement>) => {
    setExportAnchor(event.currentTarget);
  };

  const handleExportClose = () => setExportAnchor(null);

  const handleExportRange = (label: string) => {
    alert(`Exporting ${label} data (demo placeholder).`);
    setExportAnchor(null);
  };

  const normalizeRow = (row: Record<string, string>): Target | null => {
    const name = (row.name || '').trim();
    const roll = (row.roll || row.rollno || row['roll no'] || '').trim();
    const phone = (row.phone || row['phone no'] || row['phone number'] || '').trim();
    const dept = (row.dept || row.department || '').trim();
    const program = (row.program || row.course || '').trim();

    if (!name || !roll || !phone) return null;

    return {
      scheduled: false,
      name,
      roll,
      dept,
      program,
      phone,
      last_call_status: 'not_made',
      last_analysis: 'not_analyzed',
      last_recording: false,
    };
  };

  const parseCsv = async (file: File): Promise<Target[]> => {
    const text = await file.text();
    const lines = text.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
    if (lines.length < 2) return [];

    const headers = lines[0].split(',').map((h) => h.trim().toLowerCase());
    return lines.slice(1).map((line) => {
      const cells = line.split(',');
      const row: Record<string, string> = {};
      headers.forEach((h, idx) => {
        row[h] = (cells[idx] || '').trim();
      });
      return normalizeRow(row);
    }).filter((r): r is Target => !!r);
  };

  const parseExcel = async (file: File): Promise<Target[]> => {
    try {
      const XLSX = await import('xlsx');
      const buffer = await file.arrayBuffer();
      const workbook = XLSX.read(buffer, { type: 'array' });
      const sheet = workbook.Sheets[workbook.SheetNames[0]];
      const rows = XLSX.utils.sheet_to_json<Record<string, any>>(sheet, { defval: '' });
      return rows
        .map((row) => {
          const lowered: Record<string, string> = {};
          Object.keys(row).forEach((k) => {
            lowered[k.toLowerCase()] = String(row[k] ?? '').trim();
          });
          return normalizeRow(lowered);
        })
        .filter((r): r is Target => !!r);
    } catch (err) {
      throw new Error('Unable to parse Excel. Please ensure the xlsx package is installed.');
    }
  };

  const handleFileImport = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const ext = file.name.split('.').pop()?.toLowerCase();
      let imported: Target[] = [];
      if (ext === 'csv') {
        imported = await parseCsv(file);
      } else if (ext === 'xlsx' || ext === 'xls') {
        imported = await parseExcel(file);
      } else {
        throw new Error('Unsupported file type. Upload CSV or Excel.');
      }

      if (!imported.length) {
        throw new Error('No valid rows found. Required columns: name, roll, phone.');
      }

      setTargets((prev) => {
        const existing = new Set(prev.map((t) => t.roll));
        const fresh = imported.filter((t) => !existing.has(t.roll));
        return fresh.length ? [...prev, ...fresh] : prev;
      });
    } catch (error: any) {
      alert(error?.message || 'Failed to import file.');
    } finally {
      event.target.value = '';
    }
  };

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortAscending(!sortAscending);
    } else {
      setSortColumn(column);
      setSortAscending(true);
    }
  };

  const handleFlaggedSort = (column: keyof PotentialCase) => {
    if (flaggedSortColumn === column) {
      setFlaggedSortAscending(!flaggedSortAscending);
    } else {
      setFlaggedSortColumn(column);
      setFlaggedSortAscending(true);
    }
  };

  const sortedTargets = useMemo(() => {
    const query = targetSearch.trim().toLowerCase();
    const base = targets
      .filter((t) => {
        if (!query) return true;
        const fields = [t.name, t.roll, t.dept, t.program, t.phone, t.last_call_status, t.last_analysis];
        return fields.some((f) => String(f || '').toLowerCase().includes(query));
      })
      .slice();
    if (!sortColumn) return base;

    return base.sort((a, b) => {
      let aVal: any = a[sortColumn as keyof Target];
      let bVal: any = b[sortColumn as keyof Target];

      if (sortColumn === 'last_call_status') {
        const aIdx = STATUS_SORT_ORDER.indexOf(String(aVal));
        const bIdx = STATUS_SORT_ORDER.indexOf(String(bVal));
        const aOrder = aIdx === -1 ? Number.MAX_SAFE_INTEGER : aIdx;
        const bOrder = bIdx === -1 ? Number.MAX_SAFE_INTEGER : bIdx;
        if (aOrder !== bOrder) {
          return sortAscending ? aOrder - bOrder : bOrder - aOrder;
        }
      }
      
      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }
      
      if (aVal < bVal) return sortAscending ? -1 : 1;
      if (aVal > bVal) return sortAscending ? 1 : -1;
      return 0;
    });
  }, [targets, sortColumn, sortAscending]);

  const sortedFlagged = useMemo(() => {
    const query = flaggedSearch.trim().toLowerCase();
    const base = potentialCases
      .filter((c) => {
        if (!query) return true;
        const fields = [c.name, c.roll, c.dept, c.program, c.callDateTime];
        return fields.some((f) => f.toLowerCase().includes(query));
      })
      .slice();
    if (!flaggedSortColumn) return base;

    return base.sort((a, b) => {
      let aVal: any = a[flaggedSortColumn];
      let bVal: any = b[flaggedSortColumn];
      if (typeof aVal === 'string') {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }
      if (aVal < bVal) return flaggedSortAscending ? -1 : 1;
      if (aVal > bVal) return flaggedSortAscending ? 1 : -1;
      return 0;
    });
  }, [flaggedSearch, flaggedSortColumn, flaggedSortAscending]);

  return (
    <Box sx={{ p: { xs: 1, md: 2 } }}>
      <Typography variant="h4" fontWeight={700} mb={1}>
        Entry Dashboard Demo Page
      </Typography>
      

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs
          value={activeTab}
          onChange={(_, v) => setActiveTab(v)}
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab label="Schedule Calls" value="targets" />
          <Tab label="Potential Cases For Investigation" value="flagged" />
        </Tabs>
      </Box>
      {activeTab === 'targets' && (
        <>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap', mb: 2 }}>
            <Button
              variant="outlined"
              startIcon={<AddCircleOutlineIcon />}
              onClick={() => alert('Open create target form')}
            >
              Add Recipient
            </Button>
            <Button variant="outlined" onClick={() => fileInputRef.current?.click()}>
              Import Recipients (CSV/XLSX)
            </Button>
            <Tooltip
              title="Required fields: (Name, Roll_No, Phone_No, Department_Name, Program). Use these exact column headers in CSV/XLSX file while importing recipients."
              placement="right"
            >
              <IconButton size="small" color="primary" aria-label="Import instructions">
                <InfoIcon />
              </IconButton>
            </Tooltip>
            <Typography variant="body2" color="text.secondary">Instruction while importing CSV/XLSX file</Typography>
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
              onClick={() => alert(`Scheduling calls to: ${Array.from(selected).join(', ') || 'none'}`)}
            >
              Schedule Call to Selected Recipients
            </Button>
            <TextField
              size="small"
              label="Search Recipients"
              placeholder="Search"
              value={targetSearch}
              onChange={(e) => setTargetSearch(e.target.value)}
              sx={{ minWidth: 260 }}
            />
          </Box>

          <Card>
            <CardContent>
              <Box sx={{ overflowX: 'auto' }}>
                <Table size="small" sx={{ minWidth: 1100 }}>
                  <TableHead>
                    <TableRow>
                      <TableCell>Schedule</TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          Name
                          <IconButton size="small" onClick={() => handleSort('name')}>
                            {sortColumn === 'name' && !sortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          Roll No
                          <IconButton size="small" onClick={() => handleSort('roll')}>
                            {sortColumn === 'roll' && !sortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          Department
                          <IconButton size="small" onClick={() => handleSort('dept')}>
                            {sortColumn === 'dept' && !sortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          Program
                          <IconButton size="small" onClick={() => handleSort('program')}>
                            {sortColumn === 'program' && !sortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          Last Call Status
                          <IconButton size="small" onClick={() => handleSort('last_call_status')}>
                            {sortColumn === 'last_call_status' && !sortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          Last Call Analysis
                          <IconButton size="small" onClick={() => handleSort('last_analysis')}>
                            {sortColumn === 'last_analysis' && !sortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                          Last Call Recording
                          <IconButton size="small" onClick={() => handleSort('last_recording')}>
                            {sortColumn === 'last_recording' && !sortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                          </IconButton>
                        </Box>
                      </TableCell>
                      <TableCell>Info</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {sortedTargets.map((t) => {
                      const isOpen = !!openDetails[t.roll];
                      const history = callHistory[t.roll] || [];
                      const latestCall = history[0];
                      const lastStatus = latestCall?.status ?? t.last_call_status;
                      const lastAnalysis = latestCall?.analysis ?? t.last_analysis;
                      const lastRecording = latestCall?.recording_available ?? t.last_recording;
                      return (
                        <>
                          <TableRow key={t.roll} hover>
                            <TableCell>
                              <IconButton size="small" onClick={() => toggleSelect(t.roll)}>
                                {selected.has(t.roll) ? <CheckBoxIcon color="primary" /> : <CheckBoxOutlineBlankIcon />}
                              </IconButton>
                            </TableCell>
                            <TableCell><Typography fontWeight={600}>{t.name}</Typography></TableCell>
                            <TableCell>{t.roll}</TableCell>
                            <TableCell>{t.dept}</TableCell>
                            <TableCell>{t.program}</TableCell>
                            <TableCell>{renderStatusIconsCompact(lastStatus)}</TableCell>
                            <TableCell>
                              <Tooltip title={lastAnalysis === 'not_analyzed' ? 'Not analyzed' : lastAnalysis}>
                                <span>
                                  {lastAnalysis === 'not_analyzed' ? (
                                    <HelpOutlineIcon sx={{ color: '#d32f2f' }} />
                                  ) : (
                                    <CheckCircleIcon sx={{ color: '#2e7d32' }} />
                                  )}
                                </span>
                              </Tooltip>
                            </TableCell>
                            <TableCell>
                              {lastRecording ? (
                                <IconButton size="small"><PlayArrowIcon /></IconButton>
                              ) : (
                                '—'
                              )}
                            </TableCell>
                            <TableCell>
                              <IconButton size="small" onClick={() => toggleDetails(t.roll)}>
                                <InfoIcon />
                              </IconButton>
                            </TableCell>
                          </TableRow>
                          <TableRow>
                            <TableCell colSpan={9} sx={{ p: 0, border: 0 }}>
                              <Collapse in={isOpen} timeout="auto" unmountOnExit>
                                <Box sx={{ p: 2, bgcolor: '#f9fafb', borderRadius: 1, border: '1px solid', borderColor: 'divider', mb: 1 }}>
                                  <Typography variant="subtitle2" mb={1}>
                                    {t.name} — {t.program} — Roll No {t.roll} — Phone No {t.phone}
                                  </Typography>
                                  {history.length === 0 && <Typography variant="body2">No call made</Typography>}
                                  {history.map((call, idx) => (
                                    <Box key={`${t.roll}-call-${idx}`} sx={{ mb: 1.5 }}>
                                      {call.times.map((time, stepIdx) => (
                                        <Stack key={`${t.roll}-step-${idx}-${stepIdx}`} direction="row" spacing={2} alignItems="center" sx={{ mb: 0.5 }}>
                                          <Typography variant="body2" sx={{ minWidth: 170, whiteSpace: 'nowrap' }}>{time}</Typography>
                                          <Stack direction="row" spacing={1} alignItems="center" flexWrap="nowrap">
                                            {STATUS_ICON_MAP[call.status]?.left}
                                            {STATUS_ICON_MAP[call.status]?.right}
                                            <Typography variant="body2" sx={{ whiteSpace: 'nowrap' }}>{call.notes[stepIdx] || ''}</Typography>
                                          </Stack>
                                        </Stack>
                                      ))}
                                      <Stack direction="row" spacing={2} alignItems="center" sx={{ mt: 0.5 }}>
                                        <Typography variant="body2" fontWeight={600}>
                                          Analysis: {ANALYSIS_ICONS[call.analysis]}
                                        </Typography>
                                        {call.recording_available ? (
                                          <Button size="small" startIcon={<PlayArrowIcon />}>Play</Button>
                                        ) : (
                                          <Typography variant="body2" color="text.secondary">No recording</Typography>
                                        )}
                                      </Stack>
                                      <Divider sx={{ mt: 1 }} />
                                    </Box>
                                  ))}
                                </Box>
                              </Collapse>
                            </TableCell>
                          </TableRow>
                        </>
                      );
                    })}
                  </TableBody>
                </Table>
              </Box>
            </CardContent>
          </Card>
        </>
      )}

      {activeTab === 'flagged' && (
        <Card>
          <CardContent>
            <Typography variant="h6" fontWeight={700} mb={2}>Potential Cases for Investigation</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, flexWrap: 'wrap', mb: 2 }}>
              <TextField
                size="small"
                label="Search Potential Cases"
                placeholder="Search"
                value={flaggedSearch}
                onChange={(e) => setFlaggedSearch(e.target.value)}
                sx={{ minWidth: 260 }}
              />
              <Button variant="outlined" onClick={handleExportClick}>
                Export
              </Button>
              <Menu anchorEl={exportAnchor} open={Boolean(exportAnchor)} onClose={handleExportClose}>
                <MenuItem onClick={() => handleExportRange('last 7 days')}>Last 7 days</MenuItem>
                <MenuItem onClick={() => handleExportRange('last 30 days')}>Last 30 days</MenuItem>
              </Menu>
            </Box>
            <Box sx={{ overflowX: 'auto' }}>
              <Table size="small" sx={{ minWidth: 900 }}>
                <TableHead>
                  <TableRow>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        Name
                        <IconButton size="small" onClick={() => handleFlaggedSort('name')}>
                          {flaggedSortColumn === 'name' && !flaggedSortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                        </IconButton>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        Roll No
                        <IconButton size="small" onClick={() => handleFlaggedSort('roll')}>
                          {flaggedSortColumn === 'roll' && !flaggedSortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                        </IconButton>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        Department
                        <IconButton size="small" onClick={() => handleFlaggedSort('dept')}>
                          {flaggedSortColumn === 'dept' && !flaggedSortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                        </IconButton>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        Program
                        <IconButton size="small" onClick={() => handleFlaggedSort('program')}>
                          {flaggedSortColumn === 'program' && !flaggedSortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                        </IconButton>
                      </Box>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        Call Made Date And Time
                        <IconButton size="small" onClick={() => handleFlaggedSort('callDateTime')}>
                          {flaggedSortColumn === 'callDateTime' && !flaggedSortAscending ? <ArrowDownwardIcon fontSize="small" /> : <ArrowUpwardIcon fontSize="small" />}
                        </IconButton>
                      </Box>
                    </TableCell>
                    <TableCell>Info</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {sortedFlagged.map((c) => {
                    const isOpen = !!flaggedOpenDetails[c.roll];
                    return (
                      <React.Fragment key={c.roll}>
                        <TableRow hover>
                          <TableCell><Typography fontWeight={600}>{c.name}</Typography></TableCell>
                          <TableCell>{c.roll}</TableCell>
                          <TableCell>{c.dept}</TableCell>
                          <TableCell>{c.program}</TableCell>
                          <TableCell>{c.callDateTime}</TableCell>
                          <TableCell>
                            <IconButton size="small" onClick={() => toggleFlaggedDetails(c.roll)}>
                              <InfoIcon />
                            </IconButton>
                          </TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell colSpan={6} sx={{ p: 0, border: 0 }}>
                            <Collapse in={isOpen} timeout="auto" unmountOnExit>
                              <Box sx={{ p: 2, bgcolor: '#f9fafb', borderRadius: 1, border: '1px solid', borderColor: 'divider', mb: 1 }}>
                                <Tabs
                                  value={flaggedDetailTab[c.roll] ?? 'high'}
                                  onChange={(_, v: 'low' | 'moderate' | 'high') => setFlaggedDetailTab((prev) => ({ ...prev, [c.roll]: v }))}
                                  sx={{ minHeight: 36, mb: 1 }}
                                >
                                  <Tab label="Low" value="low" sx={{ minHeight: 36 }} />
                                  <Tab label="Moderate" value="moderate" sx={{ minHeight: 36 }} />
                                  <Tab label="High" value="high" sx={{ minHeight: 36 }} />
                                </Tabs>
                                {(() => {
                                  const currentTab = flaggedDetailTab[c.roll] ?? 'high';
                                  const tabData: Record<'low' | 'moderate' | 'high', string[]> = {
                                    low: c.lowAnalysisAt,
                                    moderate: c.moderateAnalysisAt,
                                    high: c.highAnalysisAt,
                                  };
                                  const messages: Record<'low' | 'moderate' | 'high', string> = {
                                    low: 'No prior low-analysis calls recorded.',
                                    moderate: 'No prior moderate-analysis calls recorded.',
                                    high: 'No prior high-analysis calls recorded.',
                                  };
                                  const entries = tabData[currentTab];
                                  if (!entries.length) {
                                    return <Typography variant="body2" color="text.secondary">{messages[currentTab]}</Typography>;
                                  }
                                  return entries.map((ts, idx) => (
                                    <Typography key={`${c.roll}-${currentTab}-${idx}`} variant="body2">{idx + 1}) {ts}</Typography>
                                  ));
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