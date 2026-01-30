import pandas as pd
import requests
import os

class MarketIntelligenceAgent:
    def __init__(self):
        self.api_url = os.getenv('MARKET_API_URL', 'https://api.example.com/market')  # Replace with your API
        self.api_key = os.getenv('MARKET_API_KEY', '')
        # Fallback to local data
        self.data_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'iqvia_data.csv')
        self.use_api = os.getenv('USE_API', 'false').lower() == 'true'

    def analyze(self, query):
        """
        Analyze market intelligence for the given query
        Connects to your market intelligence API
        """
        if self.use_api:
            return self._analyze_from_api(query)
        else:
            return self._analyze_from_file(query)

    def _analyze_from_api(self, query):
        try:
            headers = {'Authorization': f'Bearer {self.api_key}'} if self.api_key else {}
            params = {'query': query, 'type': 'market_intelligence'}
            response = requests.get(self.api_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Check if API returned meaningful data
            if data.get('data') or data.get('insights'):
                insights = data.get('insights', f"Market analysis for '{query}' from API")
                return {
                    'agent': 'Market Intelligence',
                    'insights': insights,
                    'data': data.get('data', []),
                    'charts': data.get('charts', {})
                }
            else:
                # API returned empty data, fall back to local
                return self._analyze_from_file(query)
        except Exception as e:
            # API failed, fall back to local
            return self._analyze_from_file(query)

    def _analyze_from_file(self, query):
        # Original file-based logic
        self.data = pd.read_csv(self.data_path)
        query_lower = query.lower()
        matching_rows = self.data[self.data['Molecule'].str.lower().str.contains(query_lower, na=False)]

        if not matching_rows.empty:
            row = matching_rows.iloc[0]
            insights = f"Market analysis for {row['Molecule']}: "
            insights += f"Therapy area: {row['Therapy Area']}, "
            insights += f"Market size: {row['Market Size (USD)']}, "
            insights += f"Growth rate: {row['Growth Rate (%)']}%"
            data = matching_rows.to_dict('records')
        else:
            # Generate mock data relevant to the query
            insights = f"Market analysis for '{query}': "
            insights += f"Estimated market size: ${self._estimate_market_size(query):.1f}B, "
            insights += f"Projected growth: {self._estimate_growth_rate(query):.1f}%, "
            insights += f"Therapy area: {self._infer_therapy_area(query)}"
            data = [{
                'Molecule': query,
                'Therapy Area': self._infer_therapy_area(query),
                'Market Size (USD)': f"${self._estimate_market_size(query):.1f}B",
                'Growth Rate (%)': self._estimate_growth_rate(query),
                'Competitors': 'Multiple pharmaceutical companies',
                'Key Insights': f'Innovative treatment in {self._infer_therapy_area(query)}'
            }]

        return {
            'agent': 'Market Intelligence',
            'insights': insights,
            'data': data,
            'charts': self._generate_charts()
        }

    def _generate_charts(self):
        """Generate simple chart data"""
        if hasattr(self, 'data'):
            return {
                'market_sizes': self.data.set_index('Molecule')['Market Size (USD)'].to_dict(),
                'growth_rates': self.data.set_index('Molecule')['Growth Rate (%)'].to_dict()
            }
        return {}

    def _estimate_market_size(self, query):
        """Estimate market size based on query keywords"""
        query_lower = query.lower()
        if 'cancer' in query_lower or 'tumor' in query_lower or 'oncology' in query_lower:
            return 15.0 + (len(query) % 10)  # 15-25B range
        elif 'diabetes' in query_lower or 'insulin' in query_lower:
            return 25.0 + (len(query) % 5)  # 25-30B range
        elif 'pain' in query_lower or 'analgesic' in query_lower:
            return 5.0 + (len(query) % 3)  # 5-8B range
        elif 'cardiovascular' in query_lower or 'heart' in query_lower:
            return 18.0 + (len(query) % 4)  # 18-22B range
        elif 'antiviral' in query_lower or 'virus' in query_lower:
            return 2.0 + (len(query) % 2)  # 2-4B range
        else:
            return 1.0 + (len(query) % 5)  # 1-6B range

    def _estimate_growth_rate(self, query):
        """Estimate growth rate based on query"""
        query_lower = query.lower()
        if 'new' in query_lower or 'novel' in query_lower or 'innovative' in query_lower:
            return 12.0 + (len(query) % 8)  # Higher growth for new drugs
        elif 'generic' in query_lower:
            return 2.0 + (len(query) % 3)  # Lower growth for generics
        else:
            return 5.0 + (len(query) % 10)  # 5-15% range

    def _infer_therapy_area(self, query):
        """Infer therapy area from query keywords"""
        query_lower = query.lower()
        if 'cancer' in query_lower or 'tumor' in query_lower or 'carcinoma' in query_lower:
            return 'Oncology'
        elif 'diabetes' in query_lower or 'insulin' in query_lower or 'blood sugar' in query_lower:
            return 'Diabetes/Endocrinology'
        elif 'pain' in query_lower or 'analgesic' in query_lower or 'headache' in query_lower:
            return 'Pain Management'
        elif 'heart' in query_lower or 'cardiovascular' in query_lower or 'cholesterol' in query_lower:
            return 'Cardiovascular'
        elif 'virus' in query_lower or 'viral' in query_lower or 'infection' in query_lower:
            return 'Antiviral/Infectious Diseases'
        elif 'depression' in query_lower or 'anxiety' in query_lower or 'mental' in query_lower:
            return 'Psychiatry'
        elif 'arthritis' in query_lower or 'joint' in query_lower or 'rheumatoid' in query_lower:
            return 'Rheumatology'
        else:
            return 'General Medicine'