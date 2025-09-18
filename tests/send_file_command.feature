Feature: Telegram Manager send_file Command
  As a user of the telegram_manager.sh script
  I want to send files to Telegram users and channels
  So that I can share documents, images, and other files with captions

  Background:
    Given the telegram_manager.sh script is located at "/home/almaz/MCP/FALLBACK_SCRIPTS/telegram_manager.sh"
    And valid Telegram credentials are configured in the .env file
    And the test user "@almazom" is available

  # Happy Path Scenarios
  Scenario: Send a text file with a custom caption
    Given I have a text file at "/tmp/test_file.txt" with content "Test content"
    When I execute the command "./telegram_manager.sh send_file @almazom /tmp/test_file.txt 'Test document'"
    Then the command should succeed with exit code 0
    And the output should contain "✅ File sent successfully: test_file.txt"
    And the file should be received by the target with the caption "Test document"

  Scenario: Send a file without specifying a caption
    Given I have a text file at "/tmp/test_no_caption.txt"
    When I execute the command "./telegram_manager.sh send_file @almazom /tmp/test_no_caption.txt"
    Then the command should succeed with exit code 0
    And the output should contain "✅ File sent successfully"
    And the file should be received with the default caption "📎 File attached"

  Scenario: Send an image file (JPEG)
    Given I have an image file at "/tmp/test_image.jpg"
    When I execute the command "./telegram_manager.sh send_file @almazom /tmp/test_image.jpg '📷 Test photo'"
    Then the command should succeed with exit code 0
    And the output should contain "✅ File sent successfully: test_image.jpg"
    And the image should be received with proper preview

  Scenario: Send a PDF document
    Given I have a PDF file at "/tmp/test_document.pdf"
    When I execute the command "./telegram_manager.sh send_file @almazom /tmp/test_document.pdf '📄 Important document'"
    Then the command should succeed with exit code 0
    And the output should contain "✅ File sent successfully: test_document.pdf"

  Scenario: Send a file with special characters in caption
    Given I have a file at "/tmp/test_special.txt"
    When I execute the command "./telegram_manager.sh send_file @almazom /tmp/test_special.txt '🎯 Special: !@#$%^&*()_+-=[]{}|;:\"<>?,./'"
    Then the command should succeed with exit code 0
    And the caption should be properly escaped and displayed

  # Error Handling Scenarios
  Scenario: Attempt to send a non-existent file
    When I execute the command "./telegram_manager.sh send_file @almazom /tmp/non_existent_file.txt 'Test caption'"
    Then the command should fail
    And the output should contain "❌ File not found: /tmp/non_existent_file.txt"

  Scenario: Missing required parameters - no target
    When I execute the command "./telegram_manager.sh send_file"
    Then the command should fail with exit code 1
    And the output should contain "Usage: ./telegram_manager.sh send_file <target> <file_path> [caption]"

  Scenario: Missing required parameters - no file path
    When I execute the command "./telegram_manager.sh send_file @almazom"
    Then the command should fail with exit code 1
    And the output should contain "Usage: ./telegram_manager.sh send_file <target> <file_path> [caption]"

  Scenario: Send to invalid target
    Given I have a file at "/tmp/test_invalid_target.txt"
    When I execute the command "./telegram_manager.sh send_file @nonexistentuser12345678 /tmp/test_invalid_target.txt"
    Then the command should fail
    And the error output should indicate the target cannot be found

  # Edge Cases
  Scenario: Send an empty file
    Given I have an empty file at "/tmp/empty_file.txt"
    When I execute the command "./telegram_manager.sh send_file @almazom /tmp/empty_file.txt 'Empty file test'"
    Then the command should succeed with exit code 0
    And the output should contain "✅ File sent successfully"

  Scenario: Send a file with spaces in the path
    Given I have a file at "/tmp/file with spaces.txt"
    When I execute the command "./telegram_manager.sh send_file @almazom '/tmp/file with spaces.txt' 'Space test'"
    Then the command should succeed with exit code 0
    And the output should contain "✅ File sent successfully: file with spaces.txt"

  Scenario: Send a file with unicode characters in name
    Given I have a file at "/tmp/файл_тест_文件.txt"
    When I execute the command "./telegram_manager.sh send_file @almazom /tmp/файл_тест_文件.txt 'Unicode filename test'"
    Then the command should succeed with exit code 0
    And the output should contain "✅ File sent successfully"

  Scenario: Send a large file (size boundary test)
    Given I have a file at "/tmp/large_file.bin" with size 50MB
    When I execute the command "./telegram_manager.sh send_file @almazom /tmp/large_file.bin 'Large file test'"
    Then the command should handle the file appropriately
    And either succeed if within Telegram's limits or fail gracefully with appropriate error

  Scenario: Send a file with very long caption
    Given I have a file at "/tmp/long_caption.txt"
    And I have a caption that is 1024 characters long
    When I execute the command with the long caption
    Then the command should handle caption length limits appropriately

  # Security and Permission Tests
  Scenario: Attempt to send a file without read permission
    Given I have a file at "/tmp/no_read_permission.txt" with permissions 000
    When I execute the command "./telegram_manager.sh send_file @almazom /tmp/no_read_permission.txt"
    Then the command should fail
    And the error should indicate permission denied

  Scenario: Attempt path traversal attack
    When I execute the command "./telegram_manager.sh send_file @almazom ../../../etc/passwd 'Security test'"
    Then the system should handle this safely
    And sensitive system files should not be exposed

  Scenario: Send a symbolic link
    Given I have a symbolic link at "/tmp/test_link.txt" pointing to "/tmp/real_file.txt"
    When I execute the command "./telegram_manager.sh send_file @almazom /tmp/test_link.txt 'Symlink test'"
    Then the command should follow the link and send the actual file
    And the output should indicate success

  # Integration Tests
  Scenario: Send file command doesn't break existing send command
    When I execute the command "./telegram_manager.sh send @almazom 'Test message'"
    Then the command should succeed with exit code 0
    And the output should contain "✅ Message sent"

  Scenario: Send file command doesn't break existing read command
    When I execute the command "./telegram_manager.sh read @aiclubsweggs today"
    Then the command should succeed with exit code 0
    And the read functionality should work normally

  Scenario: Help text includes send_file command
    When I execute the command "./telegram_manager.sh help"
    Then the output should contain "send_file <target> <file_path> [caption]"
    And the output should contain "Send file attachment"

  # Performance Tests
  Scenario: Send multiple files in sequence
    Given I have files "/tmp/file1.txt", "/tmp/file2.txt", "/tmp/file3.txt"
    When I send all three files sequentially
    Then all files should be sent successfully
    And no file handles should be leaked

  Scenario: Handle interrupted connection gracefully
    Given I have a file at "/tmp/test_interrupt.txt"
    When I execute the send_file command and interrupt the network connection
    Then the command should fail gracefully
    And provide appropriate error message
    And clean up any temporary resources