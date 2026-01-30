import json
import requests
import os

class InternalAgent:
    def __init__(self):
        self.api_url = os.getenv('INTERNAL_API_URL', 'https://api.example.com/internal')  # Replace with your API
        self.api_key = os.getenv('INTERNAL_API_KEY', '')
        # Fallback to local data
        self.data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'internal_docs.json')
        self.use_api = os.getenv('USE_API', 'false').lower() == 'true'

    def analyze(self, query):
        """
        Search internal knowledge base for the given query
        Connects to your internal database API
        """
        if self.use_api:
            return self._analyze_from_api(query)
        else:
            return self._analyze_from_file(query)

    def _analyze_from_api(self, query):
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}
            params = {'query': query, 'type': 'internal_knowledge'}
            response = requests.get(self.api_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Check if API returned meaningful data
            if data.get('data') or data.get('insights'):
                insights = data.get('insights', f"Internal knowledge for '{query}' from API")
                return {
                    'agent': 'Internal Knowledge',
                    'insights': insights,
                    'data': data.get('data', []),
                    'charts': {}
                }
            else:
                # API returned empty data, fall back to local
                return self._analyze_from_file(query)
        except Exception as e:
            # API failed, fall back to local
            return self._analyze_from_file(query)

    def _analyze_from_file(self, query):
        # Original file-based logic
        with open(self.data_path, 'r') as f:
            self.data = json.load(f)
        query_lower = query.lower()
        matching_docs = []

        for doc in self.data:
            if (query_lower in doc['title'].lower() or
                query_lower in doc['content'].lower()):
                matching_docs.append(doc)

        if matching_docs:
            insights = f"Found {len(matching_docs)} relevant internal documents for '{query}': "
            insights += ", ".join([doc['title'] for doc in matching_docs[:3]])  # Top 3
            if len(matching_docs) > 3:
                insights += f" and {len(matching_docs) - 3} more"
            data = matching_docs
        else:
            insights = f"No internal documents found for '{query}'. "
            insights += f"Total documents in knowledge base: {len(self.data)}"
            data = self.data[:3]  # Show some examples

        return {
            'agent': 'Internal Knowledge',
            'insights': insights,
            'data': data,
            'charts': {}  # No charts for documents
        }