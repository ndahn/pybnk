def calc_hash(input: str) -> int:
    # This is the FNV-1a 32-bit hash taken from rewwise
    # https://github.com/vswarte/rewwise/blob/127d665ab5393fb7b58f1cade8e13a46f71e3972/analysis/src/fnv.rs#L6
    FNV_BASE = 2166136261
    FNV_PRIME = 16777619
    
    input_lower = input.lower()
    input_bytes = input_lower.encode()
    
    result = FNV_BASE
    for byte in input_bytes:
        result *= FNV_PRIME
        # Ensure it stays within 32-bit range
        result &= 0xFFFFFFFF
        result ^= byte
    
    return result


def crack_event_hash(
    target_hash: int, 
    *, 
    words: list[str] = ("Play", "Stop"),
    sound_types: str = "acfopsmvxbiyzegd",
) -> str:
    """
    Crack hash for pattern: "<word>_<sound_type><id>"
    - word: the type of the event
    - sound_type: single character corresponding to the sound types Fromsoft uses
    - id: 9-digit number
    """
    for word in words:
        for type_char in sound_types:
            for id_num in range(1_000_000_000):
                candidate = f"{word}_{type_char}{id_num:010d}"
                if calc_hash(candidate) == target_hash:
                    return candidate
                
                # Progress indicator every 100k attempts
                if id_num % 100_000 == 0:
                    print(f"Trying: {candidate}", end='\r')
    
    return None


def crack_event_hash_parallel(
    target_hash: int, 
    *, 
    words: list[str] = ("Play", "Stop"), 
    sound_types: str = "acfopsmvxbiyzegd",
) -> str:
    """
    Same as crack_hash, but uses parallel processing to speed up computation.
    """
    from multiprocessing import Pool, cpu_count
    
    words = ["Play", "Stop"]
    sound_types = "acfopsmvxbiyzegd"
    
    def check_range(args):
        word, type_char, start_id, end_id, target = args

        for id_num in range(start_id, end_id):
            candidate = f"{word}_{type_char}{id_num:010d}"
            if calc_hash(candidate) == target:
                return candidate
        
        return None
    
    # Split the 10-digit space into chunks of 10^6 IDs
    chunk_size = 1_000_000
    tasks = []
    
    for word in words:
        for type_char in sound_types:
            for start in range(0, 10_000_000_000, chunk_size):
                end = min(start + chunk_size, 10_000_000_000)
                tasks.append((word, type_char, start, end, target_hash))
    
    with Pool(cpu_count()) as pool:
        for result in pool.imap_unordered(check_range, tasks):
            if result:
                pool.terminate()
                return result
    
    return None