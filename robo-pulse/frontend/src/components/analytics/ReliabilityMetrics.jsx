import { useEffect, useState } from 'react';
import {
  Alert,
  CircularProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
} from '@mui/material';
import apiClient from '../../api/client.js';

function ReliabilityMetrics() {
  const [metrics, setMetrics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function fetchMetrics() {
      try {
        const response = await apiClient.get('/missions/reliability');
        setMetrics(response.data);
      } catch {
        setError('Could not load reliability metrics.');
      } finally {
        setLoading(false);
      }
    }
    fetchMetrics();
  }, []);

  if (loading) return <CircularProgress />;
  if (error) return <Alert severity="error">{error}</Alert>;

  return (
    <TableContainer>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Model</TableCell>
            <TableCell align="right">Total Missions</TableCell>
            <TableCell align="right">Completed</TableCell>
            <TableCell align="right">Failed</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {metrics.map((row) => (
            <TableRow key={row.model}>
              <TableCell>{row.model}</TableCell>
              <TableCell align="right">{row.total_missions}</TableCell>
              <TableCell align="right">{row.completed_count}</TableCell>
              <TableCell align="right">{row.failed_count}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

export default ReliabilityMetrics;