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
  data['logging'] = False
  data['SMTP'] = 'localhost'
  data['port'] = 25
  data['starttls'] = False
  data['smtpauth'] = False
  data['username'] = 'user'
  data['password'] = 'pass'
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
    with open(os.path.expanduser('~') + '/autoreply.json', 'r', encoding='utf-8') as json_file:
      data = json.load(json_file)
  # If the file .json doesn't exist, it creates a template
  except FileNotFoundError:
    create_json()
    sys.exit("Couldn't find ~/autoreply.json. New template created.")
  return data


def generate_email(sender, recipient, replyto, subject, body, attachment_path=None, test=False):
  '''Creates an email message object with an attachement (optional).'''
  # TODO: HTML body with formatting instead of plain text?
  message = EmailMessage()
  # Email headers
  message['From'] = sender
  message['To'] = recipient
  message['Subject'] = subject
  message['Message-ID'] = make_msgid()
  message['Reply-to'] = replyto
  if test == False:
    message['X-Autoreply'] = "yes"
    message['Auto-Submitted'] = "auto-replied"
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


def send_email(message):
  '''Sends an email via SMTP server.'''
  settings = open_json()
  mail_server = smtplib.SMTP(settings['SMTP'], settings['port'])
  if settings['starttls'] == True:
    mail_server.starttls()
  if settings['smtpauth'] == True:
    mail_server.login(settings['username'], settings['password'])
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


def autoreply(sender, recipients):
  '''Sends auto-reply email from recipient to sender when the recipient is in ~/autoreply.json.'''
  settings = open_json()
  # Iterates through JSON autoreply objects
  for recipient in settings['autoreply']:
    # Checks if an email in ~/autoreply.json is in the list of recipients of the original email
    if recipient['email'] in recipients:
      log('autoreply triggered')
      log('sender is ' + str(sender))
      log('recipients are ' + str(recipients))
      log('recipient that triggered the script is ' + str(recipient['email']))
      # Checks if the auto-reply To and From are different to avoid an infinite loop
      if recipient['email'] != sender:
        # Generates and email message with the settings from ~/autoreply.json
        message = generate_email(
          recipient['email'],
          sender,
          recipient['reply-to'],
          recipient['subject'],
          recipient['body']
          )
        #Sends auto-reply email
        send_email(message)


def main():
  '''Sends auto-reply email to sender and re-injects original email into Postfix for final delivery.
  
  - sys.argv[1] is the sender, passed by Postfix as ${sender}
  - sys.argv[2:] are the recipients, passed by Postfix as ${recipient} 
  - original email message is piped by Postfix over STDIN 
  
  Use './autoreply.py -j' to generate a .json configuration file.
  Use './autoreply.py -l' to show the content of the .json configuration file.
  Use './autoreply.py -t' to generate a test email text file.
  Use './autoreply.py from@bar to@bar < test.txt' to test autoreply.py. Note: edit test.txt first and replace from@bar and to@bar with your own 
  '''
  # If no parameters are passed, it prints some help
  if len(sys.argv) < 2:
    print("Use:\n\
    './autoreply.py -j' to generate a .json configuration file.\n\
    './autoreply.py -l' to show the content of the .json configuration file.\n\
    './autoreply.py -t' to generate a test email text file.\n\
    './autoreply.py from@bar to@bar < test.txt' to test autoreply.py. Note: edit test.txt first and replace from@bar and to@bar with your own\n")
    exit()
  # Creates ~/autoreply.json if -j is passed
  if '-j' in sys.argv[1:]:
    create_json()
  # Shows the content of ~/autoreply.json if -l is passed
  if '-l' in sys.argv[1:]:
    print(json.dumps(open_json(), indent=4))
  # Creates ~/test.txt if -t is passed
  if '-t' in sys.argv[1:]: 
    t_message = generate_email('from@bar', 'to@bar', 'from@foo','This is a test email', 'This is an email to test autoreply.py', test=True)
    with open(os.path.expanduser('~') + '/test.txt', 'w', encoding='utf-8') as t_email:
      t_email.write(str(t_message))
  # Exits if -j, -l or -t were passed
  if '-j' in sys.argv[1:] or '-l' in sys.argv[1:] or '-t' in sys.argv[1:]:
    sys.exit()
  # Reads script settings
  settings = open_json()
  # Enables logging if 'logging': true
  # TODO: be able to set up logging on or off using autoreply.py
  global logging
  if settings['logging'] == True:
    logging = True
  else:
    logging = False
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
  autoreply(sender, recipients)


if __name__ == "__main__":
   main()
