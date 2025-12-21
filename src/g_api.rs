use serde::{Serialize, Deserialize};
use reqwest::{Client, Body};
use anyhow::Result;
use std::fs::File;
use std::io::copy;
use std::path::Path;

#[derive(Serialize)]
struct TextPart {
    text: String,
}

#[derive(Serialize)]
struct ImagePart {
    inline_data: InlineData,
}

#[derive(Serialize)]
struct InlineData {
    mime_type: String,
    data: String,
}

#[derive(Serialize)]
#[serde(untagged)]
enum Part {
    Text(TextPart),
    Image(ImagePart),
}

#[derive(Serialize)]
struct Content {
    parts: Vec<Part>,
}

#[derive(Serialize)]
struct RequestBody {
    contents: Vec<Content>,
}

#[derive(Deserialize, Debug)]
struct Candidate {
    content: Content,
}

#[derive(Deserialize, Debug)]
struct ResponseBody {
    candidates: Vec<Candidate>,
}

pub async fn download_image(url: &str, path: &Path) -> Result<()> {
    if path.exists() {
        println!("Image already exists at {:?}", path);
        return Ok(());
    }

    let response = reqwest::get(url).await?;
    let mut dest = File::create(path)?;
    let content = response.bytes().await?;
    copy(&mut content.as_ref(), &mut dest)?;
    Ok(())
}

pub async fn transcribe_and_translate(api_key: &str, image_path: &Path) -> Result<String> {
    let client = Client::new();
    let model = "gemini-1.5-flash";
    let url = format!(
        "https://generativelanguage.googleapis.com/v1beta/models/{}:generateContent?key={}",
        model, api_key
    );

    let image_data = std::fs::read(image_path)?;
    let encoded_image = base64::encode(&image_data);

    let request_body = RequestBody {
        contents: vec![Content {
            parts: vec![
                Part::Text(TextPart {
                    text: String::from(
                        "Describe this image in detail, focusing on the main subjects and any text present. \
                         After the description, provide a direct translation of that description into Hebrew. \
                         Format the output exactly like this, without any extra formatting or markdown:\n\
                         Description: [Your detailed description here]\n\
                         Hebrew: [The Hebrew translation here]",
                    ),
                }),
                Part::Image(ImagePart {
                    inline_data: InlineData {
                        mime_type: String::from("image/jpeg"),
                        data: encoded_image,
                    },
                }),
            ],
        }],
    };

    let response = client.post(&url)
        .json(&request_body)
        .send()
        .await?;

    let response_body = response.json::<ResponseBody>().await?;

    if let Some(candidate) = response_body.candidates.get(0) {
        if let Some(Part::Text(text_part)) = candidate.content.parts.get(0) {
            return Ok(text_part.text.clone());
        }
    }

    Err(anyhow::anyhow!("Failed to get a valid response from the API"))
}
