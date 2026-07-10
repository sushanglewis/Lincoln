use clap::Parser;
use lincoln_record::audio::devices::{default_input_device, list_input_devices};
use lincoln_record::cli::Cli;

#[tokio::main]
async fn main() {
    env_logger::init();

    match Cli::parse() {
        Cli::Devices => {
            match default_input_device() {
                Some(name) => println!("Default input: {}", name),
                None => eprintln!("No default input device found"),
            }
            for name in list_input_devices() {
                println!("  {}", name);
            }
        }
        other => {
            eprintln!("{:?} is not yet implemented", other);
            std::process::exit(1);
        }
    }
}
