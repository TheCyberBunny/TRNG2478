import { Container, Typography, Box} from '@mui/material'
import AppHeader from './components/layout/AppHeader.jsx'
import RobotList from './components/robots/RobotList.jsx'
import DiscrepancyList from './components/missions/DiscrepancyList.jsx'
import { mockRobots } from './mockData/robots.js'
import {mockDiscrepancies} from './mockData/discrepancies.js'

function App(){
  return (
    <>
      <AppHeader />
      <Container maxWidth='lg' sx={{ mt: 4}}>
        <Typography variant="h5" component="h2" gutterBottom>
          Fleet Overview
        </Typography>
        <Box sx={{ mb: 4}}>
          <RobotList robots={mockRobots} />
        </Box>
        <Typography variant="h5" component="h2" gutterBottom>
          Co-Location Discrepancies
        </Typography>
        <Box sx={{ mb: 4}}>
          <DiscrepancyList discrepancies={mockDiscrepancies} />
        </Box>

      </Container>
    </>
  )
}

export default App;