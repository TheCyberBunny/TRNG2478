import { Container, Typography, Box, Snackbar, Alert} from '@mui/material'
import {useState} from 'react'
import AppHeader from './components/layout/AppHeader.jsx'
// import RobotList from './components/robots/RobotList.jsx'
// import DiscrepancyList from './components/missions/DiscrepancyList.jsx'
// import { mockRobots } from './mockData/robots.js'
// import {mockDiscrepancies} from './mockData/discrepancies.js'

import ReliabilityMetrics from './components/analytics/ReliabilityMetrics.jsx'
import MaintenanceFlags from './components/analytics/MaintenanceFlags.jsx'
import ReportingLines from './components/analytics/ReportingLines.jsx'

import LoginForm from './components/auth/LoginForm.jsx';
import RobotDataGrid from './components/robots/RobotDataGrid.jsx';
import DiscrepancyDataGrid from './components/missions/DiscrepancyDataGrid.jsx';
import { AuthProvider, useAuth } from './context/AuthContext.jsx';

//a main dashboard component that renders the application header and robot data grid to authenticated users
function Dashboard(){
  //stores the current user object and logout function from the global AuthContext
  const {user, logout} = useAuth()
  const [notification, setNotification] = useState(null)

  return (
    <>
      <AppHeader username={user?.sub} role={user?.role} onLogout={logout} />
      <Container maxWidth="lg" sx={{ mt: 4}}>
        <Typography variant="h5" component="h2" gutterBottom>
          Fleet Overview
        </Typography>
        <Box sx={{ mb: 4}}>
          <RobotDataGrid onSuccess={setNotification}/>
        </Box>
        <Typography variant="h5" component="h2" gutterBottom>
          Co-Location Discrepancies
        </Typography>
        <Box sx={{ mb: 4}}>
          <DiscrepancyDataGrid />
        </Box>
      </Container>

      <Typography variant="h5" component="h2" gutterBottom>
      Reliability Metrics
      </Typography>
      <Box sx={{ mb: 4 }}>
      <ReliabilityMetrics />
      </Box>

      <Typography variant="h5" component="h2" gutterBottom>
      Maintenance Flags
      </Typography>
      <Box sx={{ mb: 4 }}>
      <MaintenanceFlags />
      </Box>

      <Typography variant="h5" component="h2" gutterBottom>
      Reporting Lines
      </Typography>
      <Box sx={{ mb: 4 }}>
      <ReportingLines />
      </Box>

      <Snackbar
        open={Boolean(notification)}
        autoHideDuration={4000}
        onClose={() => setNotification(null)}>
          <Alert severity="success" onClose={() => setNotification(null)}>
            {notification}
          </Alert>
        </Snackbar>

    </>
  );
}

//conditional layout switcher component that renders either the Dashboard or the login form
//based on the user's authentication status, tracked in the global AuthContext
function AppContent() {
  const {isAuthenticated } = useAuth();
  return isAuthenticated ? <Dashboard /> : <LoginForm />;
}

//acts as a root application component that wraps the entire app in the AuthProvider context
function App(){
  return (
      <AuthProvider>
        <AppContent />
      </AuthProvider>



    // <>
    //   <AppHeader />
    //   <Container maxWidth='lg' sx={{ mt: 4}}>
    //     <Typography variant="h5" component="h2" gutterBottom>
    //       Fleet Overview
    //     </Typography>
    //     <Box sx={{ mb: 4}}>
    //       <RobotList robots={mockRobots} />
    //     </Box>
    //     <Typography variant="h5" component="h2" gutterBottom>
    //       Co-Location Discrepancies
    //     </Typography>
    //     <Box sx={{ mb: 4}}>
    //       <DiscrepancyList discrepancies={mockDiscrepancies} />
    //     </Box>

    //   </Container>
    // </>
  )
}

export default App;