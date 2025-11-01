use std::io::{self, Write};

const FNV_PRIME: u32 = 16777619;
const FNV_OFFSET: u32 = 2166136261;

#[inline]
fn fnv1_32(data: &[u8]) -> u32 {
    let mut hash = FNV_OFFSET;
    for &byte in data {
        hash = hash.wrapping_mul(FNV_PRIME);
        hash ^= byte as u32;
    }
    hash
}

#[inline]
fn fnv1_continue(mut hash: u32, data: &[u8]) -> u32 {
    for &byte in data {
        hash = hash.wrapping_mul(FNV_PRIME);
        hash ^= byte as u32;
    }
    hash
}

struct SearchConfig {
    prefix: String,
    chars: Vec<char>,
    min_num: u64,
    max_num: u64,
    continue_after_match: bool,
    digits: usize,
}

fn reverse_hash(target_hash: u32, config: &SearchConfig) -> Vec<String> {
    // Precompute partial hashes for "prefix + char" (always lowercase)
    let mut partial_hashes = Vec::with_capacity(config.chars.len());
    for &ch in &config.chars {
        let mut buf = String::with_capacity(config.prefix.len() + 1);
        buf.push_str(&config.prefix.to_lowercase());
        buf.push(ch.to_ascii_lowercase());
        partial_hashes.push((ch, fnv1_32(buf.as_bytes())));
    }
    
    // Calculate actual max based on digits (e.g., 6 digits = 0 to 999999)
    let digit_max = 10u64.pow(config.digits as u32);
    let actual_max = config.max_num.min(digit_max);
    
    let total_per_char = actual_max - config.min_num;
    let total_checks = config.chars.len() as u64 * total_per_char;
    let mut checked = 0u64;
    let mut results = Vec::new();
    
    // Allocate buffer for padded number (up to 20 digits for u64::MAX)
    let mut num_buf = vec![0u8; config.digits.max(20)];
    
    // Try each character
    for (ch, partial_hash) in partial_hashes {
        // Brute force the number range
        for num in config.min_num..actual_max {
            // Format number into buffer with specified digits
            let mut n = num;
            for i in (0..config.digits).rev() {
                num_buf[i] = b'0' + (n % 10) as u8;
                n /= 10;
            }
            
            let hash = fnv1_continue(partial_hash, &num_buf[..config.digits]);
            
            if hash == target_hash {
                let result = format!("{}{}{:0width$}", 
                    config.prefix.to_lowercase(), 
                    ch.to_ascii_lowercase(), 
                    num,
                    width = config.digits);
                println!("\n✓ Found: {}", result);
                results.push(result);
                
                if !config.continue_after_match {
                    return results;
                }
            }
            
            checked += 1;
            
            // Progress every 500M checks
            if checked % 500_000_000 == 0 {
                eprint!("\rProgress: {:.1}% ({} / {})", 
                    (checked as f64 / total_checks as f64) * 100.0,
                    checked / 1_000_000, total_checks / 1_000_000);
                io::stderr().flush().unwrap();
            }
        }
    }
    
    eprintln!("\rSearch complete: {:.2} billion hashes checked", checked as f64 / 1_000_000_000.0);
    results
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() < 2 {
        eprintln!("Usage: {} <hash> [OPTIONS]", args[0]);
        eprintln!("\nOptions:");
        eprintln!("  --prefix <string>      Prefix string (default: 'Play_')");
        eprintln!("  --chars <chars>        Characters to try (default: 'scv', all: 'acfopsmvxbiyzegd')");
        eprintln!("  --digits <count>       Number of digits (default: 10)");
        eprintln!("  --min <number>         Minimum number (default: 0)");
        eprintln!("  --max <number>         Maximum number (default: auto from --digits)");
        eprintln!("  --continue             Continue searching after finding a match");
        eprintln!("\nExample:");
        eprintln!("  {} 1234567890 --prefix Test_ --chars abc --digits 6", args[0]);
        eprintln!("  This searches: Test_a000000 to Test_a999999, Test_b000000 to Test_b999999, etc.");
        std::process::exit(1);
    }
    
    let target_hash: u32 = args[1].parse()
        .expect("Invalid hash format. Use a 32-bit unsigned integer");
    
    // Parse options
    let mut config = SearchConfig {
        prefix: "Play_".to_string(),
        chars: vec!['s', 'c', 'v'],
        min_num: 0,
        max_num: 10_000_000_000,
        continue_after_match: false,
        digits: 10,
    };
    
    let mut max_specified = false;
    
    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--prefix" => {
                if i + 1 < args.len() {
                    config.prefix = args[i + 1].clone();
                    i += 2;
                } else {
                    eprintln!("Error: --prefix requires a value");
                    std::process::exit(1);
                }
            }
            "--chars" => {
                if i + 1 < args.len() {
                    config.chars = args[i + 1].chars().collect();
                    i += 2;
                } else {
                    eprintln!("Error: --chars requires a value");
                    std::process::exit(1);
                }
            }
            "--digits" => {
                if i + 1 < args.len() {
                    config.digits = args[i + 1].parse()
                        .expect("Invalid --digits value");
                    i += 2;
                } else {
                    eprintln!("Error: --digits requires a value");
                    std::process::exit(1);
                }
            }
            "--min" => {
                if i + 1 < args.len() {
                    config.min_num = args[i + 1].parse()
                        .expect("Invalid --min value");
                    i += 2;
                } else {
                    eprintln!("Error: --min requires a value");
                    std::process::exit(1);
                }
            }
            "--max" => {
                if i + 1 < args.len() {
                    config.max_num = args[i + 1].parse()
                        .expect("Invalid --max value");
                    max_specified = true;
                    i += 2;
                } else {
                    eprintln!("Error: --max requires a value");
                    std::process::exit(1);
                }
            }
            "--continue" => {
                config.continue_after_match = true;
                i += 1;
            }
            _ => {
                eprintln!("Unknown option: {}", args[i]);
                std::process::exit(1);
            }
        }
    }
    
    // If max wasn't specified, calculate it from digits
    if !max_specified {
        config.max_num = 10u64.pow(config.digits as u32);
    }
    
    // Calculate actual max based on digits
    let digit_max = 10u64.pow(config.digits as u32);
    let actual_max = config.max_num.min(digit_max);
    
    println!("Searching for hash: {} (0x{:08x})", target_hash, target_hash);
    println!("Prefix: '{}' (lowercase)", config.prefix.to_lowercase());
    println!("Characters: {:?}", config.chars.iter().collect::<String>());
    println!("Digits: {} (range: 0 to {})", config.digits, digit_max - 1);
    println!("Number range: {} to {}", config.min_num, actual_max - 1);
    println!("Continue after match: {}", config.continue_after_match);
    let total_combinations = config.chars.len() as u64 * (actual_max - config.min_num);
    println!("Total combinations: {}\n", total_combinations);
    
    let results = reverse_hash(target_hash, &config);
    
    if results.is_empty() {
        println!("\n✗ Hash not found in search space");
    } else {
        println!("\n✓ Found {} match(es)", results.len());
    }
}