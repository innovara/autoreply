# autoreply.py

> This is a fork of [innovara/autoreply](https://github.com/innovara/autoreply) with added support for domain-based auto-replies and other improvements.

## Introduction

`autoreply.py` is a Postfix filter that automatically sends reply emails when messages are sent to configured email addresses or domains. When an email enters the Postfix mail system addressed to a qualifying recipient, the script sends an auto-reply and then re-injects the original email for normal delivery.

### Key Features

- Supports specific email addresses and entire domains for auto-replies
- Configurable via a simple JSON file
- Supports SMTP authentication, StartTLS, and SSL
- HTML or plain text auto-reply messages
- Customizable templates with placeholders
- Avoids auto-reply loops and respects email standards

## How It Works

The script integrates with Postfix using `check_recipient_access` to selectively process only relevant emails. When an email is received:

1. Postfix checks if any recipient matches the configured auto-reply addresses/domains
2. If matched, the email is piped to `autoreply.py`
3. The script sends an auto-reply based on the configuration
4. The original email is re-injected into Postfix for normal delivery

This approach ensures that only qualifying emails trigger the auto-reply process, while all other emails follow their normal delivery path.

## System Configuration

For security reasons, as recommended in [Postfix's FILTER documentation](http://www.postfix.org/FILTER_README.html), the script should run under a dedicated user account (not "nobody", "root", or "postfix").

1. Create a dedicated user:
```shell
sudo useradd -d /opt/autoreply -s /usr/sbin/nologin autoreply
```

2. Set up the home directory:
```shell
sudo mkdir /opt/autoreply
sudo chown autoreply:autoreply /opt/autoreply
sudo chmod 700 /opt/autoreply
```

## Script Installation and Configuration

1. Switch to the autoreply user:
```shell
sudo su - autoreply -s /bin/bash
```

2. Download the script:
```shell
wget https://github.com/mikaeljohannessen/autoreply/raw/master/autoreply.py
chmod 700 autoreply.py
```

3. Generate the configuration file:
```shell
./autoreply.py -j
```

4. Edit the configuration file:
```shell
nano autoreply.json
```

### Configuration Options

The configuration file (`autoreply.json`) contains the following settings:

```json
{
    "logging": false,
    "SMTP": "localhost",
    "port": 25,
    "starttls": false,
    "ssl": false,
    "smtpauth": false,
    "username": "user",
    "password": "pass",
    "autoreply": [
        {
            "email": "support@example.com",
            "from": "Support Team <support@example.com>",
            "reply-to": "support@example.com",
            "subject": "RE: {ORIGINAL_SUBJECT}",
            "body": "Thank you for contacting our support team. We have received your email and will respond shortly.",
            "html": false,
            "_comment": "If you set html to true, set body to the full path of your html file"
        },
        {
            "domain": "example.com",
            "from": "Example Company <noreply@example.com>",
            "reply-to": "info@example.com",
            "subject": "RE: {ORIGINAL_SUBJECT}",
            "body": "Thank you for contacting Example Company. Your email to {ORIGINAL_DESTINATION} has been received.",
            "html": false,
            "_comment": "This will auto-reply to any email sent to *@example.com"
        }
    ]
}
```

#### Global Settings

- `logging`: Enable/disable logging to `~/autoreply.log`
- `SMTP`: Server that will send the auto-reply emails
- `port`: SMTP port of the server
- `starttls`: Enable STARTTLS for secure connections
- `ssl`: Enable SSL for secure connections from the beginning
- `smtpauth`: Enable SMTP authentication
- `username`: SMTP username (if authentication is enabled)
- `password`: SMTP password (if authentication is enabled)

#### Auto-reply Configuration

Each entry in the `autoreply` array can use either:

- `email`: Specific email address(es) that trigger an auto-reply
- `domain`: Domain name that triggers auto-replies for any address at that domain

Other settings for each entry:

- `from`: The sender address shown in the auto-reply
- `reply-to`: The reply-to address for the auto-reply
- `subject`: The subject line (can include `{ORIGINAL_SUBJECT}` placeholder)
- `body`: The message content or path to HTML file (can include `{ORIGINAL_DESTINATION}` placeholder)
- `html`: Set to `true` for HTML emails, `false` for plain text

### Configuration Examples

#### Multiple Email Addresses with the Same Configuration

```json
{
    "autoreply": [
        {
            "email": ["support@example.com", "help@example.com"],
            "from": "Support Team <support@example.com>",
            "reply-to": "support@example.com",
            "subject": "RE: {ORIGINAL_SUBJECT}",
            "body": "/path/to/email.html",
            "html": true
        }
    ]
}
```

#### Different Configurations for Different Recipients

```json
{
    "autoreply": [
        {
            "email": "sales@example.com",
            "from": "Sales Team <sales@example.com>",
            "reply-to": "sales@example.com",
            "subject": "RE: {ORIGINAL_SUBJECT}",
            "body": "/path/to/sales.html",
            "html": true
        },
        {
            "domain": "support.example.com",
            "from": "Support <noreply@example.com>",
            "reply-to": "support@example.com",
            "subject": "RE: {ORIGINAL_SUBJECT}",
            "body": "Thank you for contacting our support team at {ORIGINAL_DESTINATION}.",
            "html": false
        }
    ]
}
```

## Testing the Script

1. Generate a test email:
```shell
./autoreply.py -t
nano test.txt  # Edit the test email as needed
```

2. Run a test:
```shell
./autoreply.py from@example.org to@example.com < test.txt
```

3. Exit the autoreply shell:
```shell
exit
```

## Postfix Integration

To integrate with Postfix, you need to configure it to pipe relevant emails to the script.

1. Create a lookup table for auto-reply recipients:
```shell
sudo nano /etc/postfix/autoreply
```

2. Add entries for each email address or domain:
```
support@example.com FILTER autoreply:dummy
example.com         FILTER autoreply:dummy
```

3. Generate the Postfix lookup table:
```shell
sudo postmap /etc/postfix/autoreply
```

4. Back up and edit `main.cf`:
```shell
sudo cp /etc/postfix/main.{cf,cf.bak}
sudo nano /etc/postfix/main.cf
```

5. Add the lookup table to `smtpd_recipient_restrictions`:
```
smtpd_recipient_restrictions = check_recipient_access hash:/etc/postfix/autoreply
```

6. Back up and edit `master.cf`:
```shell
sudo cp /etc/postfix/master.{cf,cf.bak}
sudo nano /etc/postfix/master.cf
```

7. Add the autoreply pipe at the end of the file:
```
# autoreply pipe
autoreply unix  -       n       n       -       -       pipe
  flags= user=autoreply null_sender=
  argv=/opt/autoreply/autoreply.py ${sender} ${recipient}
```

8. Restart Postfix:
```shell
sudo systemctl restart postfix
```

## Upgrading

When upgrading to a new version of `autoreply.py`, it's recommended to generate a new configuration file and transfer your existing settings to it:

```shell
./autoreply.py -j
# Backup your existing configuration
cp ~/autoreply.json ~/autoreply.json.bak
# Edit the new configuration file with your settings
nano ~/autoreply.json
```

## Troubleshooting

If you encounter issues:

1. Enable logging in `autoreply.json` by setting `"logging": true`
2. Check the log file at `~/autoreply.log`
3. Verify Postfix configuration with `sudo postfix check`
4. Test the script directly with `./autoreply.py from@example.org to@example.com < test.txt`
