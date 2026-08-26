// 
// Day 6 - React and Material UI theme

// the createTheme function is used to create custom themes for materialUI components
//in this case, we are creating a 'light' mode theme with specific primary and secondary
// colors, as well as custom border radius for components.
import {createTheme} from '@mui/material/styles';


const theme = createTheme({
    palette: {
        mode: 'light',
        primary: {
            main: '#0d47a1'
        },
        secondary: {
            main: '#ff6f00'
        },
    },
    shape: {
        borderRadius: 8,
    }
});

export default theme;