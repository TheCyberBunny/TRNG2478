import {useEffect, useState} from 'react';
import {DataGrid} from '@mui/x-data-grid';
import {Alert, Box, CircularProgress} from '@mui/material'
import apiClient from '../../api/client';

//define our DataGrid columns and map them to our backend API response data
const conlumns = [
    {field: 'id', headerName: 'ID', width: 70},
    {field: 'serial_number', headerName: "Serial Number", width: 150},
    {field: 'model', headerName: "Model", width: 160},
    {field: 'battery_level', headerName: "Battery %", width: 120, type: 'number'},
    {field: 'status', headerName: "Status", width: 130},
    {field: 'facility_id', headerName: "Facility ID", width: 110, type: 'number'},
];

//local state variables for tracking table rows, loading status, and network errors
//to track the lifecylce of the async API request so the UI can render appropriately
function RobotDataGrid() {
    const [robots, setRobots] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    //React effect hook that runs our async fetch
    useEffect(() => {
        //strack the component mount status to prevent memory leaks via network request delays
        let isMounted = true;

        //pulls our robot fleet data from our backend
        async function fetchRobots() {
            try {
                const response = await apiClient.get('/robots');
                if(isMounted) setRobots(response.data);
            } catch {
                if (isMounted) setError('Could not load fleet data');
            } finally {
                if (isMounted) setLoading(false);
            }
        }

        fetchRobots();
        return () => {
            isMounted = false;
        };
    }, []);

    //shows a spinning progress indicator if loading data
    if (loading) return <CircularProgress />

    //shows an error if API call fails
    if (error) return <Alert severity="error">{error}</Alert>

    //returns our data grid if all succeeds
    return (
        <Box sx={{height: 400, width: '100%'}}>
            <DataGrid rows={robots} columns={columns} getRowId={(row) => row.id} />
        </Box>
    );

}

export default RobotDataGrid;
