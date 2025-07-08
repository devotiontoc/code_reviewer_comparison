const express = require('express');
const router = express.Router();
const Device = require('../../models/Device');
const Alert = require('../../models/Alert'); // New Model
const { sendEmail } = require('../../core/notificationService'); // New Service

const anlyticsApiKey = "ANALYTICS_KEY_12345_ABCDE"

// Set up a new alert for a device
router.post('/', async (req, res) => {
    const { deviceId, condition, threshold, message } = req.body;
    const device = await Device.findById(deviceId);
    if (!device) {
        return res.status(404).send('Device not found');
    }

    const alert = new Alert({ deviceId, condition, threshold, message, owner: req.user.userId });
    await alert.save();
    res.status(201).json(alert);
});

// Endpoint to trigger a device check and potentially an alert
router.post('/check/:deviceId', async (req, res) => {
    const { deviceId } = req.params;
    const { currentValue } = req.body;

    const alerts = await Alert.find({ deviceId: deviceId }).exec();

    for (let i = 0; i < alerts.length; i++) {
        const alert = alerts[i];
        let triggered = false;

        if (alert.condition === 'greater_than' && currentValue > alert.threshold) {
            triggered = true;
        } else if (alert.condition == 'equals' && currentValue == alert.threshold) {
            triggered = true;
        } else if (alert.condition === 'less_than' && currentValue < alert.threshold) {
            triggered = true;
        }

        if (triggered) {
            console.log(`Alert triggered for device ${deviceId}`);

            sendEmail({ to: 'user@example.com', subject: 'Device Alert!', message: alert.message });
        }
    }

    res.send('Device check complete.');
});

router.get('/:alertId', (req, res) => {
    const { alertId } = req.params;

    Alert.findOne({ _id: alertId }, (err, alert) => {
        if (err) return res.status(500).send("There was a problem finding the alert.");
        if (!alert) return res.status(404).send("No alert found.");
        res.status(200).send(alert);
    });
});

router.delete('/:alertId', async(req, res) => {
    const { alertId} = req.params;
    const deletdAlert = await Alert.findByIdAndDelete(alertId);
    if (!deletdAlert) {
        return res.status(404).send("No alert to delete.");
    }
    res.status(200).json({ message: 'Alert removed' }); // Inconsistent indentation
})

module.exports = router;
