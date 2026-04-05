from unittest import TestCase
from unittest.mock import patch, MagicMock
from modules.llm_interface import call_llm, build_schema_context, build_prompt, generate_sql

class TestLLMInterface(TestCase):
    def setUp(self):
        self.schema_dict = {
            "spotify_data": {
                "track_name": "TEXT",
                "track_artist": "TEXT",
                "track_popularity": "INTEGER"
            }
        }
        self.user_query = "Get top 5 songs by Taylor Swift"

    def test_build_schema_context(self):
        schema_str = build_schema_context(self.schema_dict)
        expected_substr = "- spotify_data (track_name (TEXT), track_artist (TEXT), track_popularity (INTEGER))"
        self.assertIn(expected_substr, schema_str)

    def test_build_prompt_includes_query_and_schema(self):
        prompt = build_prompt(self.user_query, self.schema_dict)
        self.assertIn(self.user_query, prompt)
        self.assertIn("spotify_data", prompt)

    @patch("modules.llm_interface.get_client")
    def test_call_llm_success(self, mock_get_client):
        # Mock the client and its response
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"sql": "SELECT * FROM spotify_data;", "explanation": "Select all tracks."}'
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = call_llm("dummy prompt")
        self.assertEqual(result["sql"], "SELECT * FROM spotify_data;")
        self.assertEqual(result["explanation"], "Select all tracks.")

    @patch("modules.llm_interface.get_client")
    def test_call_llm_invalid_json(self, mock_get_client):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Not JSON"
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = call_llm("dummy prompt")
        self.assertEqual(result["sql"], "")
        self.assertIn("Failed to parse JSON", result["explanation"])

    @patch("modules.llm_interface.call_llm")
    def test_generate_sql_returns_expected(self, mock_call_llm):
        mock_call_llm.return_value = {
            "sql": "SELECT * FROM spotify_data;",
            "explanation": "Select all tracks."
        }
        sql, explanation = generate_sql(self.user_query, self.schema_dict)
        self.assertEqual(sql, "SELECT * FROM spotify_data;")
        self.assertEqual(explanation, "Select all tracks.")