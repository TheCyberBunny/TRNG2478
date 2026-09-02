import { useEffect, useState } from 'react';
import { DataGrid } from '@mui/x-data-grid';
import { Alert, Box, CircularProgress, Button, Dialog, DialogActions, DialogContent, DialogTitle, MenuItem, Stack, TextField } from '@mui/material';
import apiClient from '../../api/client.js';

//defines our DataGrid columns and maps them to our backend API response data
const columns = [
  { field: 'id', headerName: 'ID', width: 70 },
  { field: 'serial_number', headerName: 'Serial Number', width: 150 },
  { field: 'model', headerName: 'Model', width: 160 },
  { field: 'battery_level', headerName: 'Battery %', width: 120, type: 'number' },
  { field: 'status', headerName: 'Status', width: 130 },
  { field: 'facility_id', headerName: 'Facility ID', width: 110, type: 'number' },
];

const STATUS_OPTIONS = ['Idle', 'In-Mission', 'Maintenance', 'Offline'];

//local state variables for tracking table rows, loading status, and network errors
//to track the lifecycle of the async API request so the UI can render appropriately
// onSuccess: a function passed down from Dashboard, called with a message string
// whenever this component successfully creates a robot
function RobotDataGrid({ onSuccess }) {
  const [robots, setRobots] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formValues, setFormValues] = useState({
    serial_number: '',
    model: '',
    battery_level: '',
    facility_id: '',
    status: 'Idle',
  });


  //pulling out of the useEffect hook so that it can be called again after a successful create, not
  //just once on mount
  //React effect hook that runs our async fetch 
  // useEffect(() => {
  //   //tracks component mount status to prevent memory leaks via network request delays
  //   let isMounted = true;

    //pulls our robot fleet data from our backend
    async function fetchRobots() {
      setLoading(true);
      try {
        const response = await apiClient.get('/robots');
        setRobots(response.data);
        setError(null); //make sure we clear any old errors
        //if (isMounted) setRobots(response.data);
      } catch {
        //if (isMounted) 
          setError('Could not load fleet data.');
      } finally {
        // if (isMounted) 
          setLoading(false);
      }
    }

    useEffect(() => {
      fetchRobots();
    }, []);

    const handleFieldChange = (field) => (event) => {
      setFormValues((prev)=> ({ ...prev, [field]: event.target.value}));
    }

  //   return () => {
  //     isMounted = false;
  //   };
  // }, []);

  //handles the actual creation of a new robot record in the db
  const handleCreate = async() => {
    try {
      await apiClient.post('/robots', {
        ...formValues,
      battery_level: Number(formValues.battery_level),
      facility_id: Number(formValues.facility_id),
    });
    setDialogOpen(false);
    setFormValues({serial_number: '', model: '', battery_level: '', facility_id: '', status: 'Idle'});
    onSuccess(`Robot ${formValues.serial_number} created.`);
    await fetchRobots(); //see the table data refreshed with the new robot
    } catch {
      //a real app would surface this inline in the dialog
    }
  }

  //shows a spinning progress indicator if loading data
  if (loading) return <CircularProgress />;
  //shows error alert if API call fails
  if (error) return <Alert severity="error">{error}</Alert>;

  //loads data grid component if all goes well
  return (
    <Box>
      <Button variant="outlined" sx={{ mb: 2}} onClick={() => setDialogOpen(true)}>Add Robot</Button>
    <Box sx={{ height: 400, width: '100%' }}>
      <DataGrid rows={robots} columns={columns} getRowId={(row) => row.id} />
    </Box>

    <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
      <DialogTitle>Add New Robot</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1, minWidth: 300}}>
          <TextField label="Serial Number" value={formValues.serial_number} onChange={handleFieldChange('serial_number')} />
          <TextField label="Model" value={formValues.model} onChange={handleFieldChange('model')} />
          <TextField label="Battery Level" type="number" value={formValues.battery_level} onChange={handleFieldChange('battery_level')} />
          <TextField label="Facility ID" type="number" value={formValues.facility_id} onChange={handleFieldChange('facility_id')} />
          <TextField select label="Status" value={formValues.status} onChange={handleFieldChange('status')}>
            {STATUS_OPTIONS.map((option) => (
              <MenuItem key={option} value={option}>{option}</MenuItem>
            ))}
          </TextField>
        </Stack>
      </DialogContent>
            <DialogActions>
              <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
              <Button variant="contained" onClick={handleCreate}>Create</Button>
            </DialogActions>

    </Dialog>

    </Box>
  );
}

export default RobotDataGrid; 