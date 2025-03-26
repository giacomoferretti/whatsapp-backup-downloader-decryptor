# WhatsApp Backup Google Driver Downloader Decryptor

[![PyPI - Version](https://img.shields.io/pypi/v/wabdd?color=green)](https://pypi.org/project/wabdd)

## Prerequisites

- End-to-end encrypted backups on Google Drive
- 64-digit encryption key (**PASSWORD IS NOT SUPPORTED**)

## Usage

### Using PyPi

1. Install the `wabdd` package

    ```shell
    pip install wabdd
    ```

    or by using `pipx`

    ```shell
    pipx install wabdd
    ```

2. Get token (change with your Google account email used in WhatsApp backup settings)

    ```shell
    wabdd token YOUR_GOOGLE@EMAIL.ADDRESS
    ```

    - If you need additional information, check [the guide](#getting-the-oauth_token)

3. Download backup

    ```shell
    wabdd download --token-file /tokens/YOUR_GOOGLE_EMAIL_ADDRESS_token.txt
    ```

    or with filters (e.g. excluding videos)

    ```shell
    wabdd download --exclude "Media/WhatsApp Video/*" --token-file /tokens/YOUR_GOOGLE_EMAIL_ADDRESS_token.txt

4. Decrypt backup (only if end-to-end encryption is enabled)

    ```shell
    wabdd decrypt --key-file keys/PHONE_NUMBER_decryption.key dump backups/PHONE_NUMBER_DATE
    ```

### Getting the 64-digit encryption key

#### Creating a new backup

1. Under `Settings > Chats > Chat backup > End-to-end encrypted backup`
2. Tap on `Turn on`
3. Choose `Use 64-digit encryption key instead`

    <img src=".github/assets/backup_key_step1.png" alt="64-Digit Key Step 1" width="300px">

4. Generate your 64-digit key
5. Copy the value into a text file (e.g. in this case `bf902e3b590af0ba781b75134c08026614ef6af12b754ee0139ebbd25f58481c`)

    <img src=".github/assets/backup_key_step2.png" alt="64-Digit Key Step 2" width="300px">

#### Using root access

1. Copy the `/data/data/com.whatsapp/encrypted_backup.key` to your pc
2. Run the following script

    ```python
    with open("encrypted_backup.key", "rb") as f:
        print(f.read()[-32:].hex())
    ```

3. Copy paste the output string into a new file

### Getting the `oauth_token`

1. Visit <https://accounts.google.com/EmbeddedSetup>
2. Login using the Google account associated in the WhatsApp backup settings.
3. You will get the following screen

    <img src=".github/assets/oauth_token_step1.png" alt="OAuth Step 1" width="600px">

4. Now click on "I agree", the form will load indefinitely.

    <img src=".github/assets/oauth_token_step2.png" alt="OAuth Step 2" width="600px">

5. Open the Developer Tools using `F12`, `CTRL+SHIFT+I` or by right-cliking the page > Inspect
6. Now go to the Application tab, under Cookies select `https://accounts.google.com`
7. Copy the value of the `oauth_token` cookie

    <img src=".github/assets/oauth_token_step3.png" alt="OAuth Step 3" width="600px">

## Frequently Asked Question

### Does this tool support normal backups (`.crypt14`)?

No, this tool only supports end-to-end encrypted backups `.crypt15`. Follow #18 for more.

### I made the backup using a password instead of the 64-digit encryption key. Can I use this tool?

No, this tool only supports end-to-end encrypted backups that use the 64-digit encryption key. Follow #14 for more.

## 💖 Support My Work

If you find my projects useful, consider supporting me:  

[![Donate on Liberapay](https://img.shields.io/badge/Liberapay-giacomoferretti-F6C915.svg?style=flat-square&logo=liberapay)](https://liberapay.com/giacomoferretti)  
[![Support me on Ko-fi](https://img.shields.io/badge/Ko--fi-giacomoferretti-ff5f5f?style=flat-square&logo=ko-fi)](https://ko-fi.com/giacomoferretti)  
[![Donate via PayPal](https://img.shields.io/badge/PayPal-hexile0-0070ba?style=flat-square&logo=paypal)](https://www.paypal.me/hexile0)  

Your support helps me continue improving these tools and creating new ones. Thank you! 🙌

If you can't donate, I also appreciate **stars** ⭐ on my repositories!

<!-- ### Prerequisites (only for poetry and docker)

1. Clone repository

    ```shell
    git clone https://github.com/giacomoferretti/whatsapp-backup-downloader-decryptor
    ```

2. Write down your backup decryption key
   - RECOMMENDED: create a folder named `keys` and store your key there

### Using Poetry

1. Install dependencies

    ```shell
    poetry install
    ```

2. Get token

    ```shell
    poetry run wabdd token YOUR_GOOGLE@EMAIL.ADDRESS
    ```

3. Download backup

    ```shell
    poetry run wabdd download --token-file /tokens/YOUR_GOOGLE_EMAIL_ADDRESS_token.txt
    ```

4. Decrypt backup

    ```shell
    poetry run wabdd decrypt --key-file keys/PHONE_NUMBER_decryption.key dump backups/PHONE_NUMBER_DATE
    ```

### Using Docker

1. Build docker image

    ```shell
    docker build . -t wabdd:0.1.5
    ```

2. Get token

    ```shell
    docker run -it --rm --user $(id -u):$(id -g) -v $(pwd)/tokens:/tokens wabdd:0.1.5 token YOUR_GOOGLE@EMAIL.ADDRESS
    ```

3. Download backup

    ```shell
    docker run -it --rm --user $(id -u):$(id -g) -v $(pwd)/backups:/backups -v $(pwd)/tokens:/tokens wabdd:0.1.5 download --token-file /tokens/YOUR_GOOGLE_EMAIL_ADDRESS_token.txt
    ```

4. Decrypt backup

    ```shell
    docker run -it --rm --user $(id -u):$(id -g) -v $(pwd)/backups:/backups -v $(pwd)/keys:/keys wabdd:0.1.5 decrypt --key-file keys/PHONE_NUMBER_decryption.key dump backups/PHONE_NUMBER_DATE
    ``` -->
