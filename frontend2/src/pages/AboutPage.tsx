import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Container,
  Grid,
  Typography,
  Button,
  Stack,
  Fade,
  Slide,
  Zoom,
} from '@mui/material';
import { useState, useEffect } from 'react';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import PhoneInTalkIcon from '@mui/icons-material/PhoneInTalk';
import BarChartIcon from '@mui/icons-material/BarChart';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';

const navigationCards = [
  {
    id: 1,
    title: 'Call Management',
    description: 'Schedule calls to call recipients, view call history, analyze recordings, and track depressed recipients',
    icon: <PhoneInTalkIcon sx={{ fontSize: 60 }} />,
    path: '/entry-dashboard',
    color: '#1e40af',
    gradient: '#1e40af',
  },
  {
    id: 2,
    title: 'Call Status Dashboard',
    description: 'Dashboard for call metrics',
    icon: <BarChartIcon sx={{ fontSize: 60 }} />,
    path: '/metrics',
    color: '#0891b2',
    gradient: '#0891b2',
  },
  {
    id: 3,
    title: 'Admin Dashboard',
    description: 'Dashboard for system health monitoring',
    icon: <MonitorHeartIcon sx={{ fontSize: 60 }} />,
    path: '/system-health',
    color: '#1e3a8a',
    gradient: '#1e3a8a',
  },
];

export default function AboutPage() {
  const navigate = useNavigate();
  const [showCards, setShowCards] = useState(false);
  const [showTitle, setShowTitle] = useState(false);

  useEffect(() => {
    setTimeout(() => setShowTitle(true), 100);
    setTimeout(() => setShowCards(true), 300);
  }, []);

  return (
    <Box
      sx={{
        minHeight: '100vh',
        height: '100vh',
        background: '#1e40af',
        position: 'relative',
        overflow: 'hidden',
      }}
    >
      <Container maxWidth="xl" sx={{ position: 'relative', zIndex: 1, height: '100%', py: 4 }}>
        <Fade in={showTitle} timeout={1000}>
          <Box textAlign="center" mb={5}>
            <Typography
              variant="h2"
              fontWeight={800}
              color="white"
              mb={2}
              sx={{
                textShadow: '2px 2px 4px rgba(0,0,0,0.2)',
                animation: 'slideDown 1s ease-out',
                '@keyframes slideDown': {
                  from: { opacity: 0, transform: 'translateY(-30px)' },
                  to: { opacity: 1, transform: 'translateY(0)' },
                },
              }}
            >
              MHealth Platform
            </Typography>
            <Typography
              variant="h5"
              color="rgba(255,255,255,0.9)"
              fontWeight={300}
              sx={{
                animation: 'fadeInUp 1.2s ease-out',
                '@keyframes fadeInUp': {
                  from: { opacity: 0, transform: 'translateY(20px)' },
                  to: { opacity: 1, transform: 'translateY(0)' },
                },
              }}
            >
              A system for screening individuals who are susceptible to depression
            </Typography>
          </Box>
        </Fade>

        <Box sx={{ display: 'flex', flexDirection: 'row', gap: 4, alignItems: 'stretch' }}>
          {navigationCards.map((card, index) => (
            <Slide
              direction="up"
              in={showCards}
              timeout={800 + index * 200}
              mountOnEnter
              unmountOnExit
              key={card.id}
            >
              <Card
                sx={{
                  flex: '1 1 0',
                  minWidth: 0,
                  background: 'rgba(255,255,255,0.95)',
                  backdropFilter: 'blur(10px)',
                  borderRadius: 4,
                  transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
                  cursor: 'pointer',
                  position: 'relative',
                  overflow: 'hidden',
                  '&::before': {
                    content: '""',
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    right: 0,
                    height: 6,
                    background: card.gradient,
                  },
                  '&:hover': {
                    transform: 'translateY(-12px) scale(1.02)',
                    boxShadow: '0 20px 40px rgba(0,0,0,0.3)',
                    '& .card-icon': {
                      transform: 'scale(1.1) rotate(5deg)',
                    },
                    '& .arrow-icon': {
                      transform: 'translateX(8px)',
                    },
                  },
                }}
                onClick={() => navigate(card.path)}
              >
                <CardContent sx={{ p: 4, height: '100%', display: 'flex', flexDirection: 'column' }}>
                  <Box
                    className="card-icon"
                    sx={{
                      color: card.color,
                      mb: 3,
                      transition: 'transform 0.3s ease',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: 100,
                      height: 100,
                      borderRadius: 3,
                      background: `${card.color}15`,
                    }}
                  >
                    {card.icon}
                  </Box>

                  <Typography variant="h5" fontWeight={700} gutterBottom color={card.color}>
                    {card.title}
                  </Typography>

                  <Typography variant="body1" color="text.secondary" mb={3} sx={{ flexGrow: 1 }}>
                    {card.description}
                  </Typography>

                  <Button
                    variant="contained"
                    endIcon={
                      <ArrowForwardIcon
                        className="arrow-icon"
                        sx={{ transition: 'transform 0.3s ease' }}
                      />
                    }
                    sx={{
                      background: card.gradient,
                      color: 'white',
                      fontWeight: 600,
                      py: 1.5,
                      borderRadius: 2,
                      boxShadow: 'none',
                      '&:hover': {
                        boxShadow: `0 8px 16px ${card.color}40`,
                      },
                    }}
                    fullWidth
                  >
                    {card.title === 'Call Management' ? 'Open' : 'Open Dashboard'}
                  </Button>
                </CardContent>
              </Card>
            </Slide>
          ))}
        </Box>

        {/* <Fade in={showCards} timeout={2000}>
          <Box textAlign="center" mt={8}>
            <Typography variant="body1" color="rgba(255,255,255,0.8)" mb={2}>
              Empowering mental health support through technology
            </Typography>
            
          </Box>
        </Fade> */}
      </Container>
    </Box>
  );
}
