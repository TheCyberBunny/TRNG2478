import {Alert, Card, CardContent, Typography, Stack} from '@mui/material';

function DiscrepancyCard({discrepancy}){
    return (
        <Card variant="outlined" sx={{ minWidth: 280 }}>
            <CardContent>
                <Typography variant="h6" component="div">
                    {discrepancy.title}
                </Typography>
                <Typography color="text.secondary" gutterBottom>
                    Mission #{discrepancy.missionId}
                </Typography>
                <Stack spacing={0.5} sx={{ mb: 1.5}}>
                    <Typography variant="body2">
                        Robot Facility: {discrepancy.robotFacilityId}
                    </Typography>
                    <Typography variant="body2">
                        Operator Facility: {discrepancy.operatorFacilityId}
                    </Typography>
                </Stack>
                <Alert severity="warning">Facility Mismatch Detected</Alert>
            </CardContent>
        </Card>
    )
}

export default DiscrepancyCard;