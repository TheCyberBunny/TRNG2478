import { useEffect, useState} from 'react';
import {DataGrid} from '@mui/x-data-grid';
import { Alert, Box, CircularProgress, FormControl,
    InputLabel, MenuItem, Select
} from '@mui/material';
import apiClient from '../../api/client.js';

//map data to the DataGrid from the backend
const columns = [
    {field: 'mission_id', headerName: 'Mission ID', width: 110},
    {field: 'title', headerName: 'Title', width: 220},
    {field: 'robot_facility_id', headerName: 'Robot Facility', width: 140, type: 'number'},
    {field: 'operator_facility_id', headerName: 'Operator Facility', width: 150, type: 'number'},
];

const PRIORITY_OPTIONS = ['', 'Low', 'Medium', 'Critical'];

//state variables for our table
function DiscrepancyDataGrid() {
    const [priority, setPriority] = useState('');
    const [discrepancies, setDiscrepancies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    //react hook for our fetch
    useEffect(() => {
        let isMounted = true;
        setLoading(true);

        //the fetch function to get our data
        async function fetchDiscrepancies() {
            try {
                const response = await apiClient.get('/missions/discrepancies', {
                    params: {priority: priority || undefined },
                });
                if (isMounted) setDiscrepancies(response.data);

            } catch {
                if (isMounted) setError('Could not load Discrepancy report');
            } finally {
                if(isMounted) setLoading(false);
            }
        }

        fetchDiscrepancies();

        return () => {
            isMounted = false;
        };

    }, [priority]);

    return (
        <Box>
            <FormControl size="small" sx={{ mb: 2, minWidth: 180}}>
                <InputLabel id="priority-filter-label">Priority</InputLabel>
                <Select
                    labelId="priority-filter-label"
                    label="priority"
                    value={priority}
                    onChange={(event) => setPriority(event.target.value)}
                    >
                        {PRIORITY_OPTIONS.map((option) => (
                            <MenuItem key={option || 'All'} value={option}>
                                {option === '' ? 'All' : option}
                            </MenuItem>))}
                    </Select>
            </FormControl>
            {loading && <CircularProgress />}
            {error && <Alert severity="error">{error}</Alert>}
            {!loading && !error && (
                <Box sx={{ height: 400, width: '100%'}}>
                    <DataGrid
                        rows={discrepancies}
                        columns={columns}
                        getRowId={(row) => row.mission_id} />
                </Box>
            )}
        </Box>
    );
}

export default DiscrepancyDataGrid;