use cpal::traits::HostTrait;

pub fn list_input_devices() -> Vec<String> {
    let host = cpal::default_host();
    host.input_devices()
        .map(|iter| iter.map(|device| device.to_string()).collect())
        .unwrap_or_default()
}

pub fn default_input_device() -> Option<String> {
    let host = cpal::default_host();
    host.default_input_device().map(|device| device.to_string())
}
