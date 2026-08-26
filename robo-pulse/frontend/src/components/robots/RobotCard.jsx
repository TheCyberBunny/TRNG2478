import { Card, CardContent, Typography, Chip, Stack } from '@mui/material';

const LOW_BATTERY_THRESHOLD = 20;

{/* RobotCard function is a React component that takes in a 'robot' object as a prop (aka a parameter).
 The component uses Material-UI components to create a card that displays the robot's serial number,
  model, battery level, and status. It also checks if the robot's battery level is below a certain
   threshold (20%) and changes the color of the battery level chip accordingly. */}
function RobotCard({ robot }) {
  const isLowBattery = robot.batteryLevel < LOW_BATTERY_THRESHOLD;

  return (
    <Card variant="outlined" sx={{ minWidth: 240 }}>
      <CardContent>
        {/* The Typography component lets us display text with different styles.*/}
        <Typography variant="h6" component="div">
          {robot.serialNumber}
        </Typography>
        <Typography color="text.secondary" gutterBottom>
          {robot.model}
        </Typography>
        {/* The Stack component is a layout component that arranges its children in a row or column.*/}
        <Stack direction="row" spacing={1} alignItems="center">
        {/* The Chip component is a small, interactive element that can display information or trigger actions.*/}
          <Chip
            label={`${robot.batteryLevel}% battery`}
            color={isLowBattery ? 'error' : 'success'}
            size="small"
          />
          <Chip label={robot.status} variant="outlined" size="small" />
        </Stack>
      </CardContent>
    </Card>
  );
}

export default RobotCard;