use lincoln_record::audio::devices::{default_input_device, list_input_devices};

#[test]
fn test_list_input_devices_returns_vec() {
    let devices = list_input_devices().expect("cpal should enumerate input devices");
    assert!(
        !devices.is_empty(),
        "cpal should report at least one input device on this machine"
    );
    for name in &devices {
        assert!(!name.is_empty(), "device name should not be empty");
    }
}

#[test]
fn test_default_input_device_has_name() {
    let device = default_input_device();
    assert!(device.is_some(), "there should be a default input device");
    assert!(
        !device.unwrap().is_empty(),
        "default device name should not be empty"
    );
}
