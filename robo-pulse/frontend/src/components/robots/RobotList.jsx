import {Grid} from '@mui/material';
import RobotCard from './RobotCard.jsx';

function RobotList({robots}) {
    return (
        <Grid container spacing = {2}>
            {/**
             * The map function is used to iterate over the 'robots' array and render
             * a RobotCard component for each robot
             */}
             {robots.map((robot)=> (
            <Grid item key={robot.id}>
                <RobotCard robot={robot} />
            </Grid>
        ))}
        </Grid>
    );
}

export default RobotList;