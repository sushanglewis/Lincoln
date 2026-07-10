use cpal::traits::HostTrait;
use log::warn;

/// Enumerate the names of all available audio input devices.
pub fn list_input_devices() -> Result<Vec<String>, cpal::Error> {
    let host = cpal::default_host();
    let devices = host.input_devices()?;
    Ok(devices.map(|device| device.to_string()).collect())
}

/// Return the name of the default audio input device, if any.
pub fn default_input_device() -> Option<String> {
    let host = cpal::default_host();
    host.default_input_device().map(|device| device.to_string())
}

/// Log a warning when device enumeration fails so callers can still fall back.
pub fn log_device_enumeration_error(error: &cpal::Error) {
    warn!("failed to enumerate audio input devices: {}", error);
}
