def to_bytes32(s: str) -> bytes:
    if s.startswith("0x") and len(s) == 66:
        return bytes.fromhex(s[2:])
    b = s.encode('utf-8')
    pad = 32 - len(b)
    if pad < 0:
        return b[:32]
    return b + bytes([0]) * pad