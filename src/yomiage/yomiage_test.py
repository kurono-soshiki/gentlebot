import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import discord
from yomiage.yomiage import dict_db, voice_queues, processing_queues

class TestYomiageFunctions(unittest.TestCase):
    def setUp(self):
        # Reset the global state before each test
        dict_db["server_settings"] = {}
        dict_db["user_settings"] = {}
        voice_queues.clear()
        processing_queues.clear()

    def test_dict_db_structure(self):
        """Test the initial structure of the dict_db dictionary"""
        self.assertIn("server_settings", dict_db)
        self.assertIn("user_settings", dict_db)
        self.assertEqual(dict_db["server_settings"], {})
        self.assertEqual(dict_db["user_settings"], {})

    @patch('discord.app_commands.CommandTree')
    @patch('discord.Client')
    def test_setup_registers_commands(self, mock_client, mock_tree):
        """Test that setup registers the expected commands"""
        from yomiage.yomiage import setup
        
        # Call setup
        setup(mock_tree, mock_client)
        
        # Check that commands were registered
        # We can't directly check the decorated functions, but we can check the call count
        # Each @tree.command() decorator calls mock_tree.command()
        self.assertGreaterEqual(mock_tree.command.call_count, 1)

    # Additional tests for specific commands would go here, but they require more
    # complex mocking of Discord's Interaction object

class TestVoiceQueueProcessing(unittest.TestCase):
    def setUp(self):
        # Reset the global state before each test
        dict_db["server_settings"] = {}
        dict_db["user_settings"] = {}
        voice_queues.clear()
        processing_queues.clear()

    @patch('discord.Client')
    def test_process_voice_queue_empty_queue(self, mock_client):
        """Test processing an empty voice queue"""
        from yomiage.yomiage import setup
        
        # Setup the mock client
        mock_guild = MagicMock()
        mock_client.get_guild.return_value = mock_guild
        mock_voice_client = MagicMock()
        mock_guild.voice_client = mock_voice_client
        
        # Import the function after patching
        import yomiage.yomiage as yomiage
        
        # Add a function to extract the process_voice_queue function
        # This is a bit hacky but necessary since the function is defined inside setup()
        process_voice_queue_func = None
        def extract_func(tree, client):
            nonlocal process_voice_queue_func
            # Call the original setup which defines process_voice_queue
            result = yomiage.setup(tree, client)
            # Extract the process_voice_queue function from the yomiage module
            # This assumes setup assigns it to a global or we need to find another way
            return result
        
        # We cannot easily test the process_voice_queue function as it's defined inside setup()
        # and not exposed. In a real implementation, you might want to refactor the code
        # to make testing easier, or use integration tests instead.
        self.skipTest("Cannot easily test process_voice_queue as it's defined inside setup()")
        
if __name__ == '__main__':
    unittest.main()