#!/usr/bin/env python3
import mimetypes
import smtplib
import sys
import json
import os.path
from os import chmod
from email import message_from_bytes
from email.message import EmailMessage
from email.utils import make_msgid
from subprocess import Popen, PIPE
from datetime import datetime


def log(message):
  '''Logs messages to ~/autoreply.log.'''
  if logging == True:
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_file = os.path.expanduser('~') + '/autoreply.log'
    with open(log_file, 'a+', encoding='utf-8') as log:
      log.write(now + ': ' + message + '\n')

def create_html():
  '''Creates ~/autoreply.html'''
  html_file = 'autoreply.html'
  html_path = os.path.join(os.path.expanduser('~'), html_file)
  if os.path.isfile(html_path) is True:
    os.replace(html_path, os.path.join(os.path.expanduser('~'), 'autoreply.html.bak'))
  html_content = '''<html>
  <head></head>
  <body>
    <p>Thank you for contacting us.<p>
    <p>We have received your message and will be in touch soon.</p>
    <p>Regards,</p>
    <p><b>Your company</b></p>
    <!- Want a logo? Encode your image here: https://elmah.io/tools/base64-image-encoder (no affiliation whatsoever)
        and replace the base64 string accordingly  -->
  <img src="data:image/png;base64,
  iVBORw0KGgoAAAANSUhEUgAAADIAAAAyCAMAAAAp4XiDAAAAwXpUWHRSYXcgcHJvZmlsZSB0eXBlIGV4aWYAAHjabVBRDsMgCP3nFDsCAioex7Yu2Q12/KHSpm57CU/kkScC7f16wqODgoDErKmkhAYpUqhaojhRBweUwQNMroW1DpdAVuLeOa+avP+sh8tgHtWyeDPS3YVtFYq4v34Z+cPcJ+r54UZlv0YeQnCDOr+FqWi+f2FruEJnQCfRdeyfe7btHdHeYaLGgdGYOc0BuAcDVxNosFijseXIOji7mS3k355OwAfhmFkT34ZaJgAAAYRpQ0NQSUNDIHByb2ZpbGUAAHicfZE9SMNAGIbfppWKVAXtIOKQoTrZRUUctQpFqBBqhVYdTC79gyYNSYqLo+BacPBnserg4qyrg6sgCP6AuLo4KbpIid8lhRYx3nHcw3vf+3L3HSA0KkyzQrOApttmOpkQs7lVMfyKCPpohjAgM8uYk6QUfMfXPQJ8v4vzLP+6P0evmrcYEBCJZ5lh2sQbxNObtsF5nzjKSrJKfE48btIFiR+5rnj8xrnossAzo2YmPU8cJRaLHax0MCuZGvEUcUzVdMoXsh6rnLc4a5Uaa92TvzCS11eWuU5rBEksYgkSRCiooYwKbMRp10mxkKbzhI9/2PVL5FLIVQYjxwKq0CC7fvA/+N1bqzA54SVFEkDXi+N8jALhXaBZd5zvY8dpngDBZ+BKb/urDWDmk/R6W4sdAf3bwMV1W1P2gMsdYOjJkE3ZlYK0hEIBeD+jb8oBg7dAz5rXt9Y5Th+ADPUqdQMcHAJjRcpe93l3d2ff/q1p9e8HNl5yjq9GWD8AAA14aVRYdFhNTDpjb20uYWRvYmUueG1wAAAAAAA8P3hwYWNrZXQgYmVnaW49Iu+7vyIgaWQ9Ilc1TTBNcENlaGlIenJlU3pOVGN6a2M5ZCI/Pgo8eDp4bXBtZXRhIHhtbG5zOng9ImFkb2JlOm5zOm1ldGEvIiB4OnhtcHRrPSJYTVAgQ29yZSA0LjQuMC1FeGl2MiI+CiA8cmRmOlJERiB4bWxuczpyZGY9Imh0dHA6Ly93d3cudzMub3JnLzE5OTkvMDIvMjItcmRmLXN5bnRheC1ucyMiPgogIDxyZGY6RGVzY3JpcHRpb24gcmRmOmFib3V0PSIiCiAgICB4bWxuczp4bXBNTT0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wL21tLyIKICAgIHhtbG5zOnN0RXZ0PSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvc1R5cGUvUmVzb3VyY2VFdmVudCMiCiAgICB4bWxuczpkYz0iaHR0cDovL3B1cmwub3JnL2RjL2VsZW1lbnRzLzEuMS8iCiAgICB4bWxuczpHSU1QPSJodHRwOi8vd3d3LmdpbXAub3JnL3htcC8iCiAgICB4bWxuczp0aWZmPSJodHRwOi8vbnMuYWRvYmUuY29tL3RpZmYvMS4wLyIKICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgeG1wTU06RG9jdW1lbnRJRD0iZ2ltcDpkb2NpZDpnaW1wOmYwZWEwMzk0LTJjNzItNGRhZi1iOWNkLTJmODg2MzYzNGEwOSIKICAgeG1wTU06SW5zdGFuY2VJRD0ieG1wLmlpZDphZjAwMDNhOC0yNDU3LTRmYjYtYjNiMy01MmVkOTVhZDdlM2EiCiAgIHhtcE1NOk9yaWdpbmFsRG9jdW1lbnRJRD0ieG1wLmRpZDo5MDM1YmU5ZC04OWJjLTQyN2YtODJjYi03NzRiZjc1MTU2NjQiCiAgIGRjOkZvcm1hdD0iaW1hZ2UvcG5nIgogICBHSU1QOkFQST0iMi4wIgogICBHSU1QOlBsYXRmb3JtPSJMaW51eCIKICAgR0lNUDpUaW1lU3RhbXA9IjE3MDI1NjI4ODc0MzQwMDEiCiAgIEdJTVA6VmVyc2lvbj0iMi4xMC4zNiIKICAgdGlmZjpPcmllbnRhdGlvbj0iMSIKICAgeG1wOkNyZWF0b3JUb29sPSJHSU1QIDIuMTAiCiAgIHhtcDpNZXRhZGF0YURhdGU9IjIwMjM6MTI6MTRUMTQ6MDg6MDcrMDA6MDAiCiAgIHhtcDpNb2RpZnlEYXRlPSIyMDIzOjEyOjE0VDE0OjA4OjA3KzAwOjAwIj4KICAgPHhtcE1NOkhpc3Rvcnk+CiAgICA8cmRmOlNlcT4KICAgICA8cmRmOmxpCiAgICAgIHN0RXZ0OmFjdGlvbj0ic2F2ZWQiCiAgICAgIHN0RXZ0OmNoYW5nZWQ9Ii8iCiAgICAgIHN0RXZ0Omluc3RhbmNlSUQ9InhtcC5paWQ6OTc3NTQ0YTItYjEyMi00NTVmLWJhMDEtZjFkMGI3YTc4N2U5IgogICAgICBzdEV2dDpzb2Z0d2FyZUFnZW50PSJHaW1wIDIuMTAgKExpbnV4KSIKICAgICAgc3RFdnQ6d2hlbj0iMjAyMy0xMi0xNFQxNDowODowNyswMDowMCIvPgogICAgPC9yZGY6U2VxPgogICA8L3htcE1NOkhpc3Rvcnk+CiAgPC9yZGY6RGVzY3JpcHRpb24+CiA8L3JkZjpSREY+CjwveDp4bXBtZXRhPgogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgIAogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgCiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAKICAgICAgICAgICAgICAgICAgICAgICAgICAgCjw/eHBhY2tldCBlbmQ9InciPz6hgEyBAAAAllBMVEXNZFUAAACBgYGBgYGAgICFhYWAgICBgYGAgICAgICOjo6CgoKAgICAgICBgYGAgICAgICBgYGAgICAgICCgoKAgICBgYGAgICAgID/AACAgICDfHyId3fwDw+kW1vrFRX1CgrlGhq6RkbOMjLfICDBPj6yTk6YaGiOcnL8AwOeYWGrVVWTbW3+AQH5BwfZJibIODjUKytFbytpAAAAAXRSTlMAQObYZgAAAAFiS0dEAIgFHUgAAAAJcEhZcwAACxMAAAsTAQCanBgAAAAHdElNRQfnDA4OCAe+mSkJAAAAs0lEQVRIx+2WSwrDMAwFc423MI5BW5H7364hNBCKP9JA6aazziD8Ikveth9hrbguvDQLCPX9+Y3XlaAOM6lpQBsZu4bsXeFwTfCjk9PUOB3L1ejWWRqnEz75IIOmEM+sFWTxz+d9IGXL1LhS4wF/BG1KYJmEnzmXjFKyR7kPoxR/BYUMfiVoGNCWoPnJFQMXmYwLMJTI6AMDloxxsizASiKLj6xXtMTJU+GqlH2QoGfPV3gBX0Gsgyg+EM0AAAAASUVORK5CYII=
  " alt="Red dot" />
  </body>
</html>'''
  with open(html_path, 'w', encoding='utf-8') as out_file:
    out_file.write(html_content)


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
  data['ssl'] = False
  data['smtpauth'] = False
  data['username'] = 'user'
  data['password'] = 'pass'
  data['autoreply'] = []
  data['autoreply'].append({
    'email': 'foo@bar',
    'from': 'Foo Bar <foo@bar>',
    'reply-to': 'foo@bar',
    'subject': 'Subject here (Was: {ORIGINAL_SUBJECT})',
    'body': 'Email body here, autoreplying for {ORIGINAL_DESTINATION}',
    'html': False,
    '_comment': 'If you set html to true, set body to the full path of your html file'
  })
  with open(json_path, 'w', encoding='utf-8') as out_file:
    json.dump(data, out_file, indent=4)
  chmod(json_path, 0o600)


def open_json():
  '''Opens ~/autoreply.json where settings are stored.'''
  try:
    # Opens ~/autoreply.json
    with open(os.path.expanduser('~') + '/autoreply.json', 'r', encoding='utf-8') as json_file:
      data = json.load(json_file)
  # If the file .json doesn't exist, it creates a template
  except FileNotFoundError:
    create_json()
    sys.exit('couldn\'t find ~/autoreply.json. New template created.')
  return data


def generate_email(sender, recipient, original_id, replyto, subject, body, html, attachment_path=None, test=False):
  '''Creates an email message object with an attachement (optional).'''
  message = EmailMessage()
  # Email headers
  message['From'] = sender
  message['To'] = recipient
  message['Subject'] = subject
  message['Message-ID'] = make_msgid()
  message['Reply-to'] = replyto
  if test == False:
    if original_id:
      message['In-Reply-To'] = original_id
    message['Auto-Submitted'] = 'auto-replied'
    message['X-Autoreply'] = 'yes'
    message['X-Auto-Response-Suppress'] = 'All'
    message['Precedence'] = 'auto_reply'
  if html == False:
    message.set_content(body)
  else:
    message.set_content(body, subtype='html')
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
  smtp_class = smtplib.SMTP if settings['ssl'] == False else smtplib.SMTP_SSL
  mail_server = smtp_class(settings['SMTP'], settings['port'])
  if settings['starttls'] == True:
    mail_server.starttls()
  if settings['smtpauth'] == True:
    mail_server.login(settings['username'], settings['password'])
  mail_server.send_message(message)
  mail_server.quit()


def reinject_email(message, sender, recipients, original_id):
  '''Sends original email back to Postfix for final delivery.'''
  # NOTE: According to Postfix's FILTER documentation
  # you must not use -t to re-inject the message
  separator = ','
  r_recipients = separator.join(recipients)
  log('re-injecting ' + str(original_id))
  log('recipients: ' + r_recipients)
  process = Popen(['/usr/sbin/sendmail', '-f', sender, '-G', '-oi', r_recipients], stdin=PIPE)
  process.communicate(message)


def check_autoreply(message, original_id):
  '''Checks if an incoming email is an autoreply itself to avoid loops'''
  '''For more information please see https://www.arp242.net/autoreply.html'''
  # Defined in RFC 3834. ‘Official’ standard to indicate a message is an autoreply
  log('checking autoreply or automated headers on ' + str(original_id))
  if message['Auto-submitted'] != None and message['Auto-submitted'] != 'no':
    log('Auto-submitted present and not \'no\', not sending autoreply')
    return True
  # Defined by Microsoft. Header used by Microsoft Exchange, Outlook, and perhaps others
  elif message['X-Auto-Response-Suppress'] in ('DR', 'AutoReply', 'All'):
    log('X-Auto-Response-Suppress is DR, AutoReply or All, not sending autoreply')
    return True
  # Defined in RFC 2919. Most of the time you don’t want to send autoreplies to mailing lists or newsletters
  elif message['List-Id'] != None or message['List-Unsubscribe'] != None:
    log('List-Id or List-Unsubscribe present, not sending autoreply')
    return True
  # Defined by Google. Gmail uses this header to identify newsletters and uses it to generate statistics
  elif message['Feedback-ID'] != None:
    log('Feedback-ID present, not sending autoreply')
    return True
  # Mentioned in RFC 2076 where its use is discouraged, but this header is commonly encountered
  elif str(message['Precedence']).lower() in ('bulk', 'auto_reply', 'list'):
    log('Precedence is bulk, auto_reply or list, not sending autoreply')
    return True
  # Other non RFC-compliant Auto-submitted headers
  elif message['X-Autoreply'] != None or message['X-Autorespond'] != None:
    log('X-Autoreply or X-Autorespond present, not sending autoreply')
    return True
  else:
    log('no autoreply or automated headers found on ' + str(original_id))
    return False


def autoreply(sender, recipients, original_msg, original_id):
  '''Sends auto-reply email from recipient to sender when the recipient is in ~/autoreply.json.'''
  settings = open_json()
  # Iterates through JSON autoreply objects
  for recipient in settings['autoreply']:
    # Checks if an email in ~/autoreply.json is in the list of recipients of the original email
    emails = recipient['email']
    if not isinstance(emails, list):
      emails = [ emails ]
    for email in emails:
      if email in recipients:
        log('autoreply triggered')
        log('sender is ' + str(sender))
        log('Message-Id is ' + str(original_id))
        log('recipients are ' + str(recipients))
        log('recipient that triggered the script is ' + str(email))
        # Checks if the auto-reply To and From are different to avoid an infinite loop
        if email != sender:
          # Generates and email message with the settings from ~/autoreply.json
          subject = recipient['subject']
          body = recipient['body']
          if recipient['html'] == True:
            try:
              with open(body, encoding='utf-8') as html_body:
                body = html_body.read()
            except FileNotFoundError:
              log(str(body) + ' doesn\'t exist. Check path.')

          # Replace placeholders
          subject = subject.replace("{ORIGINAL_SUBJECT}", original_msg["Subject"])
          body = body.replace("{ORIGINAL_DESTINATION}", email)

          message = generate_email(
            recipient['from'],
            sender,
            original_id,
            recipient['reply-to'],
            subject,
            body,
            recipient['html']
            )
          #Sends auto-reply email
          send_email(message)


def main():
  '''Sends auto-reply email to sender and re-injects original email into Postfix for final delivery.

  - sys.argv[1] is the sender, passed by Postfix as ${sender}
  - sys.argv[2:] are the recipients, passed by Postfix as ${recipient}
  - original email message is piped by Postfix over STDIN

  Use './autoreply.py -b' to generate a sample HTML body.
  Use './autoreply.py -j' to generate a JSON configuration file.
  Use './autoreply.py -l' to show the content of the JSON configuration file.
  Use './autoreply.py -t' to generate a test email text file.
  Use './autoreply.py from@bar to@bar < test.txt' to test autoreply.py. Note: edit test.txt first and replace from@bar and to@bar with your own
  '''
  # If no parameters are passed, it prints some help
  if len(sys.argv) < 2:
    print("Use:\n\
    './autoreply.py -b' to generate a sample HTML body.\n\
    './autoreply.py -j' to generate a JSON configuration file.\n\
    './autoreply.py -l' to show the content of the JSON configuration file.\n\
    './autoreply.py -t' to generate a test email text file.\n\
    './autoreply.py from@bar to@bar < test.txt' to test autoreply.py. Note: edit test.txt first and replace from@bar and to@bar with your own\n")
    exit()
  # Creates ~/autoreply.html if -b is passed
  if '-b' in sys.argv[1:]:
    create_html()
  # Creates ~/autoreply.json if -j is passed
  if '-j' in sys.argv[1:]:
    create_json()
  # Shows the content of ~/autoreply.json if -l is passed
  if '-l' in sys.argv[1:]:
    print(json.dumps(open_json(), indent=4))
  # Creates ~/test.txt if -t is passed
  if '-t' in sys.argv[1:]:
    t_message = generate_email('from@bar', 'to@bar', None, 'from@foo','This is a test email', 'This is an email to test autoreply.py', False, None, test=True)
    with open(os.path.expanduser('~') + '/test.txt', 'w', encoding='utf-8') as t_email:
      t_email.write(str(t_message))
  # Exits if -b, -j, -l or -t were passed
  if '-b' in sys.argv[1:] or '-j' in sys.argv[1:] or '-l' in sys.argv[1:] or '-t' in sys.argv[1:]:
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
  log('autoreply.py has been invoked')
  # Sender and recipients of the source email sent by Postfix as ./autoreply.py ${sender} ${recipient}
  # see README.md
  sender = sys.argv[1]
  # ${recipient} expands to as many recipients as the message contains
  recipients = sys.argv[2:]
  # Original message from STDIN
  binary_msg = sys.stdin.buffer.read()
  # Message object
  original_msg = message_from_bytes(binary_msg)
  try:
    original_id = (original_msg['Message-ID']).replace("\r","").replace("\n", "").replace(" ","")
  except:
    original_id = None
  # Re-injects original email into Postfix.
  # If the purpose of the script was to do something else with the original email, re-injecting should be done later
  reinject_email(binary_msg, sender, recipients, original_id or "without Message-ID")
  auto_submitted = check_autoreply(original_msg, original_id or "without Message-ID")
  if auto_submitted == False:
    # Sends the auto-reply
    autoreply(sender, recipients, original_msg, original_id)


if __name__ == '__main__':
  try:
    main()
  except BaseException as exc:
    import traceback
    log("Unhandled exception: %s\n%s" % (exc.__class__.__name__, traceback.format_exc()))
    raise