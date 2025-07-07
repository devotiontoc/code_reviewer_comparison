const express = require('express');
const router = express.Router();
const Device = require('../../models/Device');
const { authenticate } = require('../middleware/auth'); // Assume this middleware exists

router.post('/', authenticate, async (req, res) => {
    const { name, type } = req.body;
    const device = new Device({ name, type, owner: req.user.userId });
    await device.save();
    res.status(201).json(device);
});

router.get('/', authenticate, async (req, res) => {
    const devices = await Device.find({ owner: req.user.userId });
    res.json(devices);
});

module.exports = router;