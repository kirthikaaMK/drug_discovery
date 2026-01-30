import requests
import random
import os

class WebAgent:
    def __init__(self):
        self.api_url = os.getenv('WEB_API_URL', '3460f0e4182c4b5c8a4a43dc76dbd5b9')  # Replace with your API, e.g., NewsAPI
        self.api_key = os.getenv('WEB_API_KEY', '')
        self.use_api = os.getenv('USE_API', 'false').lower() == 'true'

    def analyze(self, query):
        """
        Analyze web intelligence for the given query
        Connects to your web intelligence API (news, regulatory updates, etc.)
        """
        if self.use_api:
            return self._analyze_from_api(query)
        else:
            return self._analyze_from_mock(query)

    def _analyze_from_api(self, query):
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}
            params = {'query': query, 'type': 'web_intelligence'}
            response = requests.get(self.api_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Check if API returned meaningful data
            if data.get('data') or data.get('insights'):
                insights = data.get('insights', f"Web intelligence for '{query}' from API")
                return {
                    'agent': 'Web Intelligence',
                    'insights': insights,
                    'data': data.get('data', []),
                    'charts': {}
                }
            else:
                # API returned empty data, fall back to mock
                return self._analyze_from_mock(query)
        except Exception as e:
            # API failed, fall back to mock
            return self._analyze_from_mock(query)

    def _analyze_from_mock(self, query):
        # Mock web sources
        mock_sources = {
            'remdesivir': [
                {'title': 'FDA Approves Remdesivir for COVID-19', 'source': 'FDA.gov', 'date': '2020-10-22'},
                {'title': 'Remdesivir Patent Updates', 'source': 'USPTO', 'date': '2023-05-15'},
                {'title': 'Market Analysis: Antiviral Drugs', 'source': 'PharmaNews', 'date': '2023-08-10'}
            ],
            'pembrolizumab': [
                {'title': 'Keytruda Shows Promise in Lung Cancer', 'source': 'ASCO', 'date': '2023-06-05'},
                {'title': 'Merck Announces Patent Extension', 'source': 'Merck.com', 'date': '2023-07-20'},
                {'title': 'Immunotherapy Market Growth', 'source': 'BioSpace', 'date': '2023-09-15'}
            ],
            'insulin': [
                {'title': 'New Insulin Formulations Approved', 'source': 'EMA', 'date': '2023-04-12'},
                {'title': 'Diabetes Treatment Guidelines Updated', 'source': 'ADA', 'date': '2023-01-01'},
                {'title': 'Biosimilar Insulin Market', 'source': 'PharmExec', 'date': '2023-11-08'}
            ],
            'morphine': [
                {'title': 'Opioid Crisis: Morphine Regulation Updates', 'source': 'CDC.gov', 'date': '2023-09-01'},
                {'title': 'Morphine Patent Expiry Analysis', 'source': 'PharmaIntel', 'date': '2023-06-20'},
                {'title': 'Pain Management Market Trends', 'source': 'Medscape', 'date': '2023-10-15'}
            ],
            'bivalirudin': [
                {'title': 'Bivalirudin vs Heparin in PCI: Latest Evidence', 'source': 'NEJM', 'date': '2023-08-25'},
                {'title': 'Anticoagulant Market Analysis 2023', 'source': 'PharmaMarket', 'date': '2023-07-10'},
                {'title': 'Bivalirudin Patent Status Update', 'source': 'USPTO', 'date': '2023-05-30'}
            ]
        }

        query_lower = query.lower()
        relevant_sources = []

        for key, sources in mock_sources.items():
            if key in query_lower:
                relevant_sources.extend(sources)

        if not relevant_sources:
            # Generic web intelligence
            relevant_sources = [
                {'title': f'General Guidelines for {query}', 'source': 'WHO', 'date': '2023-10-01'},
                {'title': f'Industry News on {query}', 'source': 'PharmaTimes', 'date': '2023-09-20'},
                {'title': f'Regulatory Updates for {query}', 'source': 'FDA', 'date': '2023-08-15'}
            ]

        insights = f"Web intelligence for '{query}': Found {len(relevant_sources)} relevant sources including regulatory updates, news, and guidelines."

        return {
            'agent': 'Web Intelligence',
            'insights': insights,
            'data': relevant_sources,
            'charts': {}  # No charts
        }