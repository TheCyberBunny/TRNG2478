import { useState } from 'react';
import { Alert, Box, Button, Paper, TextField, Typography} from '@mui/material';
import { useAuth } from '../../context/AuthContext.jsx';

{/** extracts the login function from global AuthContext */}
function LoginForm() {
    const {login} = useAuth();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState(null);


{/**form submission handler function */}
const handleSubmit = async (event) => {
    {/**prevent a full page refresh on submit */}
    event.preventDefault()
    setError(null);
    try {
        await login(username, password);
    } catch {
        setError('Incorrect Username or password')
    }
};

return (
    <Box sx={{display: 'flex', justifyContent: 'center', mt: 8}}>
        <Paper component="form" onSubmit={handleSubmit} variant="outlined" sx={{ p: 4, width: 320}}>
            <Typography variant="h6" gutterBottom>
                Robopulse Login
            </Typography>
            {error && <Alert severity="error" sx={{mb: 2}}>{error}</Alert>}
            <TextField
                label="Username"
                fullWidth
                margin="normal"
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                />
            <TextField
                label="Password"
                type="password"
                fullWidth
                margin="normal"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                />
                <Button type="submit" variant="contained" fullWidth sx={{ mt: 2}}>
                    Log In
                </Button>
        </Paper>
    </Box>
    );
}

export default LoginForm;