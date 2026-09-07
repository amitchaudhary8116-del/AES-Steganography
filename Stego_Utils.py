"""
stego_utils.py
---------------
LSB (Least Significant Bit) image steganography.

We hide raw bytes (the AES-encrypted blob) inside a PNG image by
overwriting the least significant bit of each color channel value
(R, G, B) of each pixel. Changing the LSB shifts a pixel value by at
most 1 out of 255, which is invisible to the human eye.

Data layout embedded in the image:
    [32 bits = length of payload in bytes] + [payload bits...]

The 32-bit length header lets the extractor know exactly how many
bytes to read back out, instead of reading the whole image.
"""

import numpy as np
from PIL import Image

HEADER_BITS = 32  # bits used to store the payload length


def _bytes_to_bits(data: bytes) -> np.ndarray:
    """Convert bytes into a numpy array of individual bits (0/1), MSB first."""
    arr = np.frombuffer(data, dtype=np.uint8)
    bits = np.unpackbits(arr)
    return bits


def _bits_to_bytes(bits: np.ndarray) -> bytes:
    """Convert a numpy array of bits back into bytes."""
    return np.packbits(bits).tobytes()


def max_capacity_bytes(image_path: str) -> int:
    """Return how many payload bytes can be hidden in the given image."""
    img = Image.open(image_path)
    img = img.convert("RGB")
    width, height = img.size
    total_bits = width * height * 3  # 3 channels per pixel
    usable_bits = total_bits - HEADER_BITS
    return max(usable_bits // 8, 0)


def hide_data(image_path: str, data: bytes, output_path: str) -> None:
    """
    Hide `data` (raw bytes, e.g. an AES-encrypted blob) inside the image
    at image_path, using LSB steganography, and save the result as a
    new lossless PNG at output_path.
    """
    img = Image.open(image_path)
    img = img.convert("RGB")  # ensure consistent 3-channel format
    pixels = np.array(img)  # shape: (height, width, 3), dtype=uint8

    capacity = max_capacity_bytes(image_path)
    if len(data) > capacity:
        raise ValueError(
            f"Message too large for this image. "
            f"Max capacity: {capacity} bytes, message size: {len(data)} bytes. "
            f"Use a larger image."
        )

    # Build header (32-bit length) + payload bits
    length_header = np.array(list(np.binary_repr(len(data), width=HEADER_BITS)), dtype=np.uint8)
    payload_bits = _bytes_to_bits(data)
    all_bits = np.concatenate([length_header, payload_bits])

    flat_pixels = pixels.reshape(-1)  # flatten to 1D array of channel values
    # Clear the LSB of each channel value we are about to use, then set it
    flat_pixels[:len(all_bits)] = (flat_pixels[:len(all_bits)] & 0xFE) | all_bits

    stego_pixels = flat_pixels.reshape(pixels.shape)
    stego_img = Image.fromarray(stego_pixels, mode="RGB")
    stego_img.save(output_path, format="PNG")  # PNG = lossless, required for LSB to survive


def extract_data(image_path: str) -> bytes:
    """
    Extract the hidden byte payload from a stego image produced by hide_data().
    """
    img = Image.open(image_path)
    img = img.convert("RGB")
    pixels = np.array(img)
    flat_pixels = pixels.reshape(-1)

    # Read the 32-bit length header first
    header_bits = flat_pixels[:HEADER_BITS] & 1
    payload_len_bytes = int("".join(header_bits.astype(str)), 2)

    total_payload_bits = payload_len_bytes * 8
    start = HEADER_BITS
    end = start + total_payload_bits

    if end > flat_pixels.size:
        raise ValueError(
            "Image does not contain a valid hidden payload "
            "(corrupted image or wrong file)."
        )

    payload_bits = flat_pixels[start:end] & 1
    return _bits_to_bytes(payload_bits)


if __name__ == "__main__":
    # Quick self-test using a generated test image
    test_img = Image.fromarray(
        (np.random.rand(200, 200, 3) * 255).astype(np.uint8), mode="RGB"
    )
    test_img.save("_test_cover.png")

    secret = b"Hello, this is a hidden AES-encrypted blob!"
    hide_data("_test_cover.png", secret, "_test_stego.png")
    recovered = extract_data("_test_stego.png")

    assert recovered == secret
    print("Self-test passed. Recovered:", recovered)
    print("Capacity of 200x200 test image:", max_capacity_bytes("_test_cover.png"), "bytes")
