# WhatsApp Backup Google Driver Downloader Decryptor

[![PyPI - Version](https://img.shields.io/pypi/v/wabdd?color=green)](https://pypi.org/project/wabdd)

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

### Getting the `oauth_token`

1. Visit <https://accounts.google.com/EmbeddedSetup>
2. Login using the Google account associated in the WhatsApp backup settings.
3. You will get the following screen
![OAuth Step 1](.github/assets/oauth_token_step1.png)
4. Now click on "I agree", the form will load indefinitely.
![OAuth Step 2](.github/assets/oauth_token_step2.png)
5. Open the Developer Tools using `F12`, `CTRL+SHIFT+I` or by right-cliking the page > Inspect
6. Now go to the Application tab, under Cookies select `https://accounts.google.com`
7. Copy the value of the `oauth_token` cookie
![OAuth Step 3](.github/assets/oauth_token_step3.png)

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
    docker build . -t wabdd:0.1.4
    ```

2. Get token

    ```shell
    docker run -it --rm --user $(id -u):$(id -g) -v $(pwd)/tokens:/tokens wabdd:0.1.4 token YOUR_GOOGLE@EMAIL.ADDRESS
    ```

3. Download backup

    ```shell
    docker run -it --rm --user $(id -u):$(id -g) -v $(pwd)/backups:/backups -v $(pwd)/tokens:/tokens wabdd:0.1.4 download --token-file /tokens/YOUR_GOOGLE_EMAIL_ADDRESS_token.txt
    ```

4. Decrypt backup

    ```shell
    docker run -it --rm --user $(id -u):$(id -g) -v $(pwd)/backups:/backups -v $(pwd)/keys:/keys wabdd:0.1.4 decrypt --key-file keys/PHONE_NUMBER_decryption.key dump backups/PHONE_NUMBER_DATE
    ``` -->
