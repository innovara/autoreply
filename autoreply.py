#!/usr/bin/env python3
import mimetypes
import smtplib
import sys
import json
import os.path
from email import message_from_file
from email.message import EmailMessage
from email.utils import make_msgid
from subprocess import Popen, PIPE
from datetime import datetime


def log(message):
    '''Logs messages to ~/autoreply.log.'''
    if logging == True:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_file = os.path.expanduser('~') + '/autoreply.log'
        with open(log_file, 'a+', encoding='utf-8') as log:
            log.write(now + ': ' + message + '\n')


def create_json():
    '''Creates ~/autoreply.json.'''
    json_file = 'autoreply.json'
    json_path = os.path.join(os.path.expanduser('~'), json_file)
    data = {}
    if os.path.isfile(json_path) is True:
        os.replace(json_path, os.path.join(os.path.expanduser('~'), 'autoreply.json.bak'))
    data['logging'] = 'off'
    data['SMTP'] = 'localhost'
    data['autoreply'] = []
    data['autoreply'].append({
        'email': 'foo@bar',
        'reply-to': 'foo@bar',
        'subject': 'Subject here',
        'body': 'Email body here'
    })
    with open(json_path, 'w', encoding='utf-8') as out_file:
        json.dump(data, out_file, indent=4)


def open_json():
    '''Opens ~/autoreply.json where settings are stored.'''
    try:
        # Opens ~/autoreply.json
        with open(os.path.expanduser('~') + '/autoreply.json', 'r') as json_file:
            data = json.load(json_file)
    # If the file .json doesn't exist, it creates a template
    except FileNotFoundError:
        create_json()
        with open(os.path.expanduser('~') + '/autoreply.json', 'r') as json_file:
            data = json.load(json_file)
    return data


def generate_email(sender, recipient, replyto, subject, body, attachment_path=None):
    '''Creates an email message object with an attachement (optional).'''
    # TODO: HTML body with formatting instead of plain text?
    message = EmailMessage()
    # Email headers
    message['From'] = sender
    message['To'] = recipient
    message['Subject'] = subject
    message['Message-ID'] = make_msgid()
    message['Reply-to'] = sender
    message.set_content(body)
    # Process the attachment and add it to the email
    if attachment_path != None:
        attachment_filename = os.path.basename(attachment_path)
        mime_type, _ = mimetypes.guess_type(attachment_path)
        mime_type, mime_subtype = mime_type.split('/', 1)
        with open(attachment_path, 'rb') as ap:
            message.add_attachment(ap.read(),
                                maintype=mime_type,
                                subtype=mime_subtype,
                                filename=attachment_filename)
    return message


def send_email(smtp, message):
    '''Sends an email via SMTP server.'''
    # TODO: be able to set up the SMTP setting stored in autoreply.json using autoreply.py
    # TODO: support authentication
    mail_server = smtplib.SMTP(smtp)
    mail_server.send_message(message)
    mail_server.quit()


def reinject_email(message, sender, recipients):
    '''Sends original email back to Postfix for final delivery.'''
    # NOTE: According to Postfix's FILTER documentation
    # you must not use -t to re-inject the message
    separator = ','
    r_recipients = separator.join(recipients)
    log('re-injecting email to: ' + r_recipients)
    process = Popen(["/usr/sbin/sendmail", "-f", sender, "-G", "-oi", r_recipients], stdin=PIPE)
    process.communicate(message.as_bytes())


def autoreply(smtp, sender, recipients):
    '''Sends auto-reply email from recipient to sender when the recipient is in ~/autoreply.json.'''
    data = open_json()
    # Iterates through JSON autoreply objects
    for recipient in data['autoreply']:
        # Checks if an email in ~/autoreply.json is in the list of recipients of the original email
        if recipient['email'] in recipients:
            log('autoreply triggered')
            log('sender is ' + str(sender))
            log('recipients are ' + str(recipients))
            log('recipient that triggered the script is ' + str(recipient['email']))
            # Checks if the auto-reply To and From are different to avoid an infinite loop
            if  recipient['email'] != sender:
                # Generates and email message with the settings from ~/autoreply.json
                message = generate_email(
                    recipient['email'],
                    sender,
                    recipient['reply-to'],
                    recipient['subject'],
                    recipient['body']
                    )
                send_email(smtp, message) #Sends auto-reply email


def main():
    '''Sends auto-reply email to sender and re-injects original email into Postfix for final delivery.
    
    - sys.argv[1] is the sender, passed by Postfix as ${sender}
    - sys.argv[2:] are the recipients, passed by Postfix as ${recipient} 
    - original email message is piped by Postfix over STDIN 
    
    Include -l to generate logs under ~/autoreply.log
    Use ./autoreply.py -j to generate a .json configuration file.
    Use ./autoreply.py -t to generate a test email text file.
    '''
    # If no parameters are passed, it prints some help
    if len(sys.argv) < 2:
        print('Use:\n\
        ./autoreply.py -j to generate a .json configuration file.\n\
        ./autoreply.py -t to generate a test email text file.\n\
        ./autoreply.py from@bar to@bar < test.txt\n')
        exit()
    # Creates ~/autoreply.json if -j is passed
    if '-j' in sys.argv[1:]:
        create_json()
    # Creates ~/test.txt if -t is passed
    if '-t' in sys.argv[1:]: 
        t_message = generate_email('bar@foo', 'foo@bar', 'bar@foo','This is a test email', 'This would be the autoreply body.')
        with open(os.path.expanduser('~') + '/test.txt', 'w', encoding='utf-8') as t_email:
            t_email.write(str(t_message))
    # Exits if either -j or -t where passed
    if '-j' in sys.argv[1:] or '-t' in sys.argv[1:]:
        exit()
    # Reads script settings
    settings = open_json()
    # Enables logging if 'logging': 'on'
    # TODO: be able to set up logging on or off using autoreply.py
    global logging
    if settings['logging'] == 'on':
        logging = True
    else:
        logging = False
    smtp = settings['SMTP']
    # Sender and recipients of the source email sent by Postfix as ./autoreply.py ${sender} ${recipient}
    # see README.md
    sender = sys.argv[1]
    # ${recipient} expands to as many recipients as the message contains
    recipients = sys.argv[2:]
    # Original message from STDIN
    original_msg = message_from_file(sys.stdin)
    # Re-injects original email into Postfix.
    # If the purpose of the script was to do something with the original email this should be done later
    reinject_email(original_msg, sender, recipients)
    # Sends the auto-reply
    autoreply(smtp, sender, recipients)


if __name__ == "__main__":
     main()
