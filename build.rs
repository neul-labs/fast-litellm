/// Build script to download the latest model pricing JSON
///
/// This script:
/// - Downloads model pricing from LiteLLM's GitHub
/// - Uses curl with timeout and retry logic
/// - Falls back to wget if curl fails
/// - Validates the downloaded file

use std::env;
use std::fs;
use std::path::PathBuf;
use std::process::Command;
use std::time::Duration;

const PRICING_URL: &str =
    "https://raw.githubusercontent.com/BerriAI/litellm/refs/heads/main/model_prices_and_context_window.json";

const MAX_FILE_SIZE: usize = 10 * 1024 * 1024; // 10MB max
const DOWNLOAD_TIMEOUT_SECS: u64 = 30;
const MAX_RETRIES: u32 = 3;
const RETRY_DELAY_MS: u64 = 1000;

/// Download file with timeout and retry logic
fn download_with_retry(pricing_file: &PathBuf) -> bool {
    for attempt in 1..=MAX_RETRIES {
        println!("⬇️  Downloading model pricing (attempt {}/{})...", attempt, MAX_RETRIES);

        // Try curl first (with timeout)
        let curl_success = download_with_curl(pricing_file);

        if curl_success {
            return true;
        }

        // Fallback to wget
        println!("   curl failed, trying wget...");
        if download_with_wget(pricing_file) {
            return true;
        }

        if attempt < MAX_RETRIES {
            println!("   ⚠️  Download failed, retrying in {}ms...", RETRY_DELAY_MS);
            std::thread::sleep(Duration::from_millis(RETRY_DELAY_MS * attempt as u64)); // Exponential backoff
        }
    }

    false
}

/// Download using curl with timeout
fn download_with_curl(pricing_file: &PathBuf) -> bool {
    // curl command with:
    // -f: fail on HTTP errors
    // -s: silent mode
    // -S: show errors
    // -L: follow redirects
    // -m: max time in seconds (timeout)
    // -o: output file
    let output = Command::new("curl")
        .args(&[
            "-fsSL",
            "-m", &DOWNLOAD_TIMEOUT_SECS.to_string(),
            "-o", pricing_file.to_str().unwrap(),
            PRICING_URL,
        ])
        .output();

    match output {
        Ok(result) => {
            if result.status.success() {
                println!("   ✅ Downloaded via curl ({} bytes)", file_size(pricing_file));
                true
            } else {
                let stderr = String::from_utf8_lossy(&result.stderr);
                if stderr.contains("Could not resolve host") {
                    println!("   ⚠️  Network error: Could not resolve host");
                } else if stderr.contains("Connection refused") {
                    println!("   ⚠️  Network error: Connection refused");
                } else if stderr.contains("Operation timed out") {
                    println!("   ⚠️  Download timed out after {}s", DOWNLOAD_TIMEOUT_SECS);
                }
                false
            }
        }
        Err(e) => {
            println!("   ⚠️  Failed to execute curl: {}", e);
            false
        }
    }
}

/// Download using wget with timeout
fn download_with_wget(pricing_file: &PathBuf) -> bool {
    // wget command with:
    // -q: quiet
    // -O: output file
    // -T: timeout seconds
    // -t: retry attempts
    let output = Command::new("wget")
        .args(&[
            "-q",
            "-O", pricing_file.to_str().unwrap(),
            "-T", &DOWNLOAD_TIMEOUT_SECS.to_string(),
            "-t", "1",
            PRICING_URL,
        ])
        .output();

    match output {
        Ok(result) => {
            if result.status.success() {
                println!("   ✅ Downloaded via wget ({} bytes)", file_size(pricing_file));
                true
            } else {
                let stderr = String::from_utf8_lossy(&result.stderr);
                println!("   ⚠️  wget failed: {}", stderr);
                false
            }
        }
        Err(e) => {
            println!("   ⚠️  Failed to execute wget: {}", e);
            false
        }
    }
}

/// Get file size as string
fn file_size(path: &PathBuf) -> String {
    match fs::metadata(path) {
        Ok(metadata) => {
            let bytes = metadata.len();
            if bytes >= 1024 * 1024 {
                format!("{:.1} MB", bytes as f64 / (1024.0 * 1024.0))
            } else if bytes >= 1024 {
                format!("{:.1} KB", bytes as f64 / 1024.0)
            } else {
                format!("{} B", bytes)
            }
        }
        Err(_) => "unknown".to_string(),
    }
}

/// Validate the downloaded JSON file using basic structural checks
/// (Build scripts can't use serde_json, so we do lightweight validation)
fn validate_pricing_file(pricing_file: &PathBuf) -> bool {
    // Check if file exists
    if !pricing_file.exists() {
        println!("   ⚠️  Pricing file not found");
        return false;
    }

    // Check file size
    match fs::metadata(pricing_file) {
        Ok(metadata) => {
            let size = metadata.len() as usize;
            if size == 0 {
                println!("   ⚠️  Pricing file is empty");
                return false;
            }
            if size > MAX_FILE_SIZE {
                println!("   ⚠️  Pricing file too large ({} > {} MB)", size, MAX_FILE_SIZE / 1024 / 1024);
                return false;
            }
        }
        Err(e) => {
            println!("   ⚠️  Could not read file metadata: {}", e);
            return false;
        }
    }

    // Check if it looks like JSON (starts with { and ends with })
    match fs::read_to_string(pricing_file) {
        Ok(content) => {
            let trimmed = content.trim();
            if !trimmed.starts_with('{') || !trimmed.ends_with('}') {
                println!("   ⚠️  Downloaded file doesn't look like JSON (missing braces)");
                return false;
            }

            // Lightweight JSON validation: check for balanced braces
            // (Full JSON parsing is done at runtime in the library)
            if !has_balanced_braces(trimmed) {
                println!("   ⚠️  Downloaded file has unbalanced braces");
                return false;
            }

            println!("   ✅ Valid JSON structure ({} bytes)", file_size(pricing_file));
            true
        }
        Err(e) => {
            println!("   ⚠️  Could not read pricing file: {}", e);
            false
        }
    }
}

/// Check if JSON has balanced braces (lightweight validation)
fn has_balanced_braces(content: &str) -> bool {
    let mut depth = 0;
    let mut in_string = false;
    let mut prev_char = '\0';

    for c in content.chars() {
        if prev_char == '\\' && in_string {
            // Skip escaped characters
            prev_char = c;
            continue;
        }

        match c {
            '"' => {
                in_string = !in_string;
            }
            '{' | '[' if !in_string => {
                depth += 1;
            }
            '}' | ']' if !in_string => {
                if depth == 0 {
                    return false; // Unmatched closing brace
                }
                depth -= 1;
            }
            _ => {}
        }
        prev_char = c;
    }

    depth == 0
}

fn main() {
    let out_dir = PathBuf::from(env::var("OUT_DIR").unwrap());
    let pricing_file = out_dir.join("model_prices.json");

    // Check if we should download
    let should_download = env::var("DOWNLOAD_MODEL_PRICING").is_ok()
        || !pricing_file.exists()
        || env::var("FORCE_REBUILD").is_ok();

    if should_download {
        println!("🚀 Model Pricing Downloader");
        println!("   URL: {}", PRICING_URL);
        println!("   Timeout: {}s per attempt", DOWNLOAD_TIMEOUT_SECS);
        println!("   Max retries: {}", MAX_RETRIES);

        // Attempt download
        let success = download_with_retry(&pricing_file);

        if success {
            // Validate the downloaded file
            if validate_pricing_file(&pricing_file) {
                println!("✅ Model pricing ready for build");
            } else {
                println!("⚠️  Validation failed, using embedded defaults");
                let _ = fs::write(&pricing_file, "{}");
            }
        } else {
            println!("⚠️  Could not download model pricing after {} attempts", MAX_RETRIES);
            println!("   Using embedded defaults. Run 'DOWNLOAD_MODEL_PRICING=1 cargo build' to retry.");
            // Create empty file to prevent repeated downloads
            let _ = fs::write(&pricing_file, "{}");
        }
    }

    // Set environment variable for the build
    if pricing_file.exists() {
        println!("cargo:rerun-if-changed={}", pricing_file.display());
    }
}
