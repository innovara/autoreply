#!/usr/bin/env python3
import sys
import os
import json
from autoreply import autoreply, send_autoreply_message

# Mock objects for testing
class MockMessage:
    def __init__(self, subject):
        self.subject = subject
        
    def __getitem__(self, key):
        if key == 'Subject':
            return self.subject
        return None

# Test function
def test_domain_matching():
    print("Testing domain matching functionality...")
    
    # Create test data
    sender = "test@external.com"
    recipients = ["user1@example.com", "user2@example.com", "someone@otherdomain.com"]
    original_msg = MockMessage("Test Subject")
    original_id = "test123"
    
    # Create a test JSON config
    test_config = {
        "logging": True,
        "SMTP": "localhost",
        "port": 25,
        "autoreply": [
            {
                "domain": "example.com",
                "from": "Example Company <noreply@example.com>",
                "reply-to": "support@example.com",
                "subject": "RE: {ORIGINAL_SUBJECT}",
                "body": "Domain test: Thank you for contacting Example Company. Your email to {ORIGINAL_DESTINATION} has been received.",
                "html": False
            },
            {
                "email": "someone@otherdomain.com",
                "from": "Other Domain <noreply@otherdomain.com>",
                "reply-to": "info@otherdomain.com",
                "subject": "RE: {ORIGINAL_SUBJECT}",
                "body": "Email test: Thank you for your email to {ORIGINAL_DESTINATION}",
                "html": False
            }
        ]
    }
    
    # Save test config
    test_json_path = os.path.expanduser('~/autoreply_test.json')
    with open(test_json_path, 'w') as f:
        json.dump(test_config, f, indent=4)
    
    # Mock the open_json function to return our test config
    def mock_open_json():
        return test_config
    
    # Mock the send_email function to print instead of sending
    def mock_send_email(message):
        print("\nWould send email:")
        print(f"From: {message['From']}")
        print(f"To: {message['To']}")
        print(f"Subject: {message['Subject']}")
        print(f"Body: {message.get_content()}")
        print("-" * 50)
    
    # Patch the functions
    import autoreply
    autoreply.open_json = mock_open_json
    autoreply.send_email = mock_send_email
    
    # Run the test
    print("\nTesting with recipients:", recipients)
    autoreply.autoreply(sender, recipients, original_msg, original_id)
    
    # Clean up
    os.remove(test_json_path)
    print("\nTest completed!")

if __name__ == "__main__":
    # Set global logging variable
    import autoreply
    autoreply.logging = True
    
    test_domain_matching() 