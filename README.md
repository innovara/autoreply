# autoreply.py

## Introduction

autoreply.py works in tandem with Postfix as a filter.

It sends auto-replies when a message sent to a qualifying email address, enters the Postfix mail system.

In the proposed Postfix configuration, we make use of check_recipient_access to instruct Postfix to only pipe to autoreply.py emails which are sent to these qualifying email addresses. The script, using settings stored in autoreply.json, sends the auto-reply and re-injects the original email into Postfix for delivery.

The look up table related to check_recipient_access is used for any mail received by SMTP but not for emails sent locally, using sendmail.

autoreply.py could be easily adapted to do other things with the original email, instead of just passing it on, like extracting information or storing attachments.

The following sections provide a detailed step-by-step guide on how to set up autoreply.py and Postfix.

## Background

One of our clients had a complex email infrastructure and they wanted a script that would trigger auto-replies when emails sent to some specific addresses entered one of their MTAs. Normally, these would have been configured in the MDA/mailboxes instead.

The MTA in question was Postfix. It would relay all emails and they could make configuration changes to this server safely.

After some consideration, it was deemed viable to use an after-queue content filter in Postfix to achieve this.

As the email addresses that they would need to auto reply would change over time, as well as the subjects and wording of the email, we decided to use a JSON file to store that information which could be edited without having to change the script.

## System configuration

This section is somehow optional but please note that, as per [Postfix's FILTER documentation](http://www.postfix.org/FILTER_README.html), filter scripts should be run using a separate account, as these are handling potentially malicious emails. To quote their documentation, do not use "nobody", and most certainly do not use "root" or "postfix".

1. Add autoreply user with home directory /opt/autoreply and nologin.
```shell
sudo useradd -d /opt/autoreply -s /usr/sbin/nologin autoreply
```
2. Create autoreply's home directory.
```shell
sudo mkdir /opt/autoreply
```
3. Change autoreply's home directory ownership.
```shell
sudo chown autoreply:autoreply /opt/autoreply
```
4. Restrict access to autoreply's home directory.
```shell
sudo chmod 700 /opt/autoreply
```
## Script configuration

1. Change to autoreply user.
```
sudo su - autoreply -s /bin/bash
```
2. Download autoreply.py.
```shell
wget https://github.com/innovara/autoreply/raw/master/autoreply.py
```
3. Change permissions.
```shell
chmod 700 autoreply.py
```
3. Run ./autoreply.py -j to generate ~/autoreply.json.
```
./autoreply.py -j
```
4. Edit autoreply.json.
```
nano autoreply.json
```
```json
{
    "logging": "off",
    "SMTP": "localhost",
    "autoreply": [
        {
            "email": "foo@bar",
            "reply-to": "foo@bar",
            "subject": "Subject here",
            "body": "Email body here"
        }
    ]
}
```
Edit:
* logging: on or off to enable/disable logging to ~/autoreply.log.
* SMTP: if the server that will send the auto-reply emails is different from localhost.
* email: email addresses that you want to send an auto-reply from.
* reply-to: this is useful in case you want to use noreply@...

5. If you want to add a more email addresses, the JSON file would look something like this.
```json
{
    "logging": "off",
    "SMTP": "localhost",
    "autoreply": [
        {
            "email": "foo@bar",
            "reply-to": "foo@bar",
            "subject": "Subject here",
            "body": "Email body here"
        },
        {
            "email": "foo2@bar",
            "reply-to": "foo2@bar",
            "subject": "Subject here",
            "body": "Email body here"
        }
    ]
}
```
6. If you want to create an email file for testing, run ./autoreply.py -t and edit From, To and Reply-to accordingly.
```shell
./autoreply.py -t
nano test.txt
```
7. Run a test from the command line.
```
./autoreply.py from@bar to@bar < test.txt
```

At this point, the recipient of the test email should have received the test email from the sender, and the sender an auto-reply message from the recipient.

8. Exit autoreply shell
```
exit
```

## Postfix configuration

Now you have to edit the configuration of the Postfix server to pipe emails to the script.

You could pipe all the emails to autoreply.py, but the script would unnecessarily handle a number of emails that would not trigger an auto-reply. 
To avoid emails out of the scope of autoreply.py being piped to it, we use check_recipient_access under smtpd_recipient_restrictions in main.cf.

Bear in mind that, if there are multiple recipients, Postfix will pipe the email as long as at least one of them is in the lookup table. 

1. Create a Postfix lookup table input file.
```shell
sudo nano /etc/postfix/autoreply
```
2. Add one line per recipient:
```
foo@bar FILTER autoreply:dummy
```
3. Create its corresponding Postfix lookup table.
```shell
sudo postmap /etc/postfix/autoreply
```
4. Back up main.cf.
```shell
sudo cp /etc/postfix/main.cf /etc/postfix/main.cf.bak
```
5. Edit main.cf
```shell
sudo nano /etc/postfix/main.cf
```
6. Add the new lookup table as the first item in smtpd_recipient_restrictions
```
smtpd_recipient_restrictions = check_recipient_access hash:/etc/postfix/autoreply
```
7. Back up master.cf
```
sudo cp /etc/postfix/master.cf /etc/postfix/master.cf.bak
```
8. Edit /etc/postfix/master.cf
```shell
sudo nano /etc/postfix/master.cf
```
9. Add the autoreply pipe at the end of the file. Edit user and script path if you are not following the instructions regarding system configuration. 
```
# autoreply pipe
autoreply unix  -       n       n       -       -       pipe
  flags= user=autoreply null_sender=
  argv=/opt/autoreply/autoreply.py ${sender} ${recipient}
```
10. Restart Postfix.
```shell
sudo systemctl restart postfix
```
You are ready to go. If everything has gone well, when Postfix receives emails addressed to your target auto-reply email addresses, it will pass them to autoreply.py and the script will send the auto-reply email according to your configuration.