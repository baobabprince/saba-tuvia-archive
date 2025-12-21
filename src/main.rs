use clap::{Parser, Subcommand};
use anyhow::Result;
use std::path::PathBuf;

mod cropper;
mod g_api;

#[derive(Parser)]
#[clap(author, version, about, long_about = None)]
struct Cli {
    #[clap(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Crop an image
    Crop {
        #[clap(parse(from_os_str))]
        input_path: PathBuf,
        #[clap(parse(from_os_str))]
        output_path: PathBuf,
        #[clap(long, arg_enum, default_value_t = cropper::CropMethod::Contour)]
        method: cropper::CropMethod,
    },
    /// Transcribe and translate an image
    Transcribe {
        #[clap(long, default_value = "images")]
        image_dir: String,
        #[clap(long, default_value = "transcriptions.txt")]
        output_file: String,
        #[clap(long, default_value = ".last_processed_image")]
        state_file: String,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();

    match &cli.command {
        Commands::Crop { input_path, output_path, method } => {
            let mut img = image::open(input_path)?;
            cropper::crop_image(&mut img, method, output_path.to_str().unwrap())?;
            println!("Image cropped successfully and saved to {:?}", output_path);
        }
        Commands::Transcribe { image_dir, output_file, state_file } => {
            let next_image_filename = get_next_image_filename(state_file, 700)?;
            if let Some(filename) = next_image_filename {
                let image_path = PathBuf::from(image_dir).join(&filename);
                let base_url = "https://assets.yadvashem.org/image/upload/t_f_low_image/f_auto/v1/remote_media/documentation4/16/12612299_03263622/";
                let image_url = format!("{}{}", base_url, filename);

                g_api::download_image(&image_url, &image_path).await?;

                let api_key = std::env::var("GEMINI_API_KEY")?;
                let result = g_api::transcribe_and_translate(&api_key, &image_path).await?;

                use std::io::Write;
                let mut file = std::fs::OpenOptions::new()
                    .create(true)
                    .append(true)
                    .open(output_file)?;
                writeln!(file, "---\nFile: {}\n{}", filename, result)?;

                std::fs::write(state_file, filename)?;
            } else {
                println!("All images have been processed.");
            }
        }
    }

    Ok(())
}

fn get_next_image_filename(state_file: &str, max_images: u32) -> Result<Option<String>> {
    let last_processed_num = if PathBuf::from(state_file).exists() {
        let content = std::fs::read_to_string(state_file)?;
        content.trim().split('.').next().unwrap_or("0").parse::<u32>().unwrap_or(0)
    } else {
        0
    };

    let next_image_num = last_processed_num + 1;
    if next_image_num > max_images {
        Ok(None)
    } else {
        Ok(Some(format!("{:05}.JPG", next_image_num)))
    }
}
