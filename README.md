# AES-Steganography
This project implements a secure communication system that combines two layers of protection — cryptography and steganography — to hide secret messages inside ordinary-looking images. Rather than just encrypting a message the system disguises the very existence of the message by embedding it invisibly inside a photo.


# Secure Communication System — AES Encryption + Image Steganography

Hide a secret text message inside an image. The message is first
encrypted with **AES-256**, and the encrypted bytes are then hidden
inside the image's pixels using **LSB (Least Significant Bit)
steganography**. The output image looks identical to the original to
the human eye, but secretly carries an encrypted payload that only
someone with the correct password can extract and read.

```
Sender:                                   Receiver:
message + password                        stego_image.png + password
      |                                          |
      v                                          v
 [AES-256 encrypt]                     [LSB extract encrypted bytes]
      |                                          |
      v                                          v
 [LSB hide in image]  --> stego_image.png -->  [AES-256 decrypt]
                                                  |
                                                  v
                                          original message
```

## Project structure

```
secure_comm_system/
├── crypto_utils.py         # AES-256-CBC encrypt/decrypt (PBKDF2 key derivation)
├── stego_utils.py          # LSB steganography: hide/extract bytes in images
├── encrypt_and_hide.py     # Sender-side CLI script
├── decrypt_and_reveal.py   # Receiver-side CLI script
├── requirements.txt
├── sample_cover.png        # A sample image to test with
└── README.md
```

## 1. Setup in VS Code

### Install VS Code extensions
Open the Extensions panel (`Ctrl+Shift+X` / `Cmd+Shift+X`) and install:

| Extension | Publisher | Why you need it |
|---|---|---|
| **Python** | Microsoft | Core Python support: run/debug, IntelliSense, environment selection |
| **Pylance** | Microsoft | Fast type checking & autocomplete (usually bundled with Python extension) |
| **Python Debugger** | Microsoft | Lets you set breakpoints and step through the code |
| **Even Better TOML** *(optional)* | tamasfe | Nice-to-have if you later add `pyproject.toml` |
| **Rainbow CSV** *(optional)* | mechatroner | Handy if you extend the project to log results to CSV |

The only *required* ones are **Python**, **Pylance**, and **Python Debugger** — install those from the Extensions marketplace and select your Python interpreter with `Ctrl+Shift+P` → "Python: Select Interpreter".

### Install dependencies
Open a terminal in VS Code (`` Ctrl+` ``) inside the project folder and run:

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```

> Note: this project uses the `cryptography` library for AES (rather than
> `pycryptodome`) — it's actively maintained, audited, and installs cleanly
> on all platforms with no extra build tools.

## 2. How to run

### Step 1 — Sender: encrypt & hide the message

```bash
python encrypt_and_hide.py --image sample_cover.png --output stego_output.png --message "Meet me at 9pm" --password "MyStrongPassword"
```

Or just run `python encrypt_and_hide.py` with no arguments and it will prompt you interactively (and hide the password as you type it).

This produces `stego_output.png` — send **this file** to the receiver. Share the password separately (e.g. in person, over a phone call, or via a different secure channel — never in the same message as the image).

### Step 2 — Receiver: extract & decrypt the message

```bash
python decrypt_and_reveal.py --image stego_output.png --password "MyStrongPassword"
```

If the password is correct, the original message is printed. If it's wrong, decryption fails safely with an error (it won't silently output garbage).

## 3. How it works (for your project report)

### AES-256 encryption (`crypto_utils.py`)
- The password is never used directly as the key. Instead, **PBKDF2-HMAC-SHA256** with 200,000 iterations stretches it into a 256-bit key, using a random 16-byte salt. This defends against brute-force/dictionary attacks on the password.
- A random 16-byte IV (initialization vector) is generated per message so the same message never produces the same ciphertext twice.
- The message is encrypted with **AES-256 in CBC mode** with PKCS7 padding.
- Final blob = `salt (16 bytes) + IV (16 bytes) + ciphertext`. This whole blob is what gets hidden in the image — nothing is stored in plaintext anywhere.

### LSB Image Steganography (`stego_utils.py`)
- Every pixel has 3 color channels (R, G, B), each an 8-bit number (0–255).
- We overwrite only the **least significant bit** of each channel value with one bit of our encrypted data. This changes a pixel value by at most 1 out of 255 — invisible to the human eye.
- A 32-bit header is embedded first, storing the exact byte-length of the hidden payload, so extraction knows exactly where to stop reading.
- The image must be saved as **PNG** (lossless) — JPEG uses lossy compression and would destroy the hidden bits.

### Capacity
A `W x H` image can hide up to `(W * H * 3 - 32) / 8` bytes. The scripts check this automatically and raise a clear error if your message + image combination won't fit.

## 4. Security notes (good to mention in a project writeup)

- This demonstrates **defense in depth**: even if the image is intercepted, an attacker sees an ordinary-looking picture. Even if they suspect steganography and extract the hidden bytes, they still face AES-256 encryption without the password.
- Use a strong, high-entropy password — PBKDF2 slows down brute-force attempts but doesn't make a weak password strong.
- LSB steganography is **not robust against image processing** (resizing, re-compression to JPEG, cropping) — any of these will corrupt/destroy the hidden data. Always send the exact `.png` file, e.g. via file transfer rather than pasting into a chat app that recompresses images.
- This is a good academic/learning project; for production-grade secure messaging, use established protocols (Signal Protocol, TLS, etc.) rather than steganography, which offers *obscurity*, not proven cryptographic guarantees, once someone knows to look for it.

## 5. Ideas to extend the project
- Add a Tkinter or PyQt GUI so users don't need the command line.
- Support hiding files (not just text) by embedding a filename + file bytes.
- Add HMAC-based integrity verification so tampering with the stego image is detected explicitly (rather than just failing to decrypt).
- Switch to AES-GCM (authenticated encryption) instead of CBC + PKCS7 for built-in tamper detection.
