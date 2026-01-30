from sentence_transformers import SentenceTransformer
import numpy as np
import pandas as pd
import json
import os

class NLPAnalysisAgent:
    def __init__(self):
        self.model = None
        self.model_loaded = False

    def _ensure_model_loaded(self):
        """Lazy load the model only when needed"""
        if not self.model_loaded:
            self._load_model()
            self.model_loaded = True

    def _load_model(self):
        """Load the NLP model"""
        try:
            # Try to load with timeout
            import signal
            def timeout_handler(signum, frame):
                raise TimeoutError("Model loading timed out")

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30 second timeout

            self.model = SentenceTransformer('all-MiniLM-L6-v2', local_files_only=True)

            signal.alarm(0)  # Cancel alarm

        except Exception as e:
            print(f"Failed to load NLP model: {e}")
            self.model = None

    def analyze(self, query):
        """
        Analyze literature using NLP techniques
        """
        self._ensure_model_loaded()

        try:
            # Mock research abstracts for analysis
            abstracts = self._get_mock_abstracts(query)

            if self.model is not None:
                analysis_results = self._analyze_with_model(query, abstracts)
            else:
                analysis_results = self._analyze_mock(query, abstracts)

            insights = f"NLP analysis of {len(abstracts)} research abstracts related to '{query}'. Key themes: {', '.join(analysis_results['themes'][:3])}"

            # Create analysis data
            analysis_data = []
            for theme, score in analysis_results['theme_scores'].items():
                analysis_data.append({
                    'theme': theme,
                    'relevance_score': round(score, 3),
                    'frequency': analysis_results['theme_frequencies'].get(theme, 0)
                })

            # Create charts data
            charts = {
                'theme_analysis': {
                    'labels': list(analysis_results['theme_scores'].keys())[:8],
                    'values': list(analysis_results['theme_scores'].values())[:8],
                    'type': 'doughnut',
                    'colors': ['#ff6b6b', '#4ecdc4', '#45b7d1', '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3']
                },
                'sentiment_trend': {
                    'labels': ['Positive', 'Neutral', 'Negative'],
                    'values': [analysis_results['sentiment']['positive'],
                             analysis_results['sentiment']['neutral'],
                             analysis_results['sentiment']['negative']],
                    'type': 'pie',
                    'colors': ['#00d2d3', '#feca57', '#ff6b6b']
                }
            }

            return {
                'agent': 'NLP Analysis',
                'insights': insights,
                'data': analysis_data,
                'charts': charts
            }

        except Exception as e:
            return {
                'agent': 'NLP Analysis',
                'insights': f"NLP analysis failed: {str(e)}",
                'data': [],
                'charts': {}
            }

    def _analyze_with_model(self, query, abstracts):
        """Analyze abstracts using the NLP model"""
        # Encode query and abstracts
        query_embedding = self.model.encode([query])[0]
        abstract_embeddings = self.model.encode(abstracts)

        # Calculate similarities
        similarities = np.dot(abstract_embeddings, query_embedding) / (
            np.linalg.norm(abstract_embeddings, axis=1) * np.linalg.norm(query_embedding)
        )

        # Mock themes based on common drug discovery themes
        themes = [
            'clinical efficacy', 'safety profile', 'mechanism of action', 'drug resistance',
            'pharmacokinetics', 'toxicity', 'biomarkers', 'combination therapy',
            'patient outcomes', 'molecular targets'
        ]

        theme_scores = {}
        theme_frequencies = {}

        for theme in themes:
            theme_embedding = self.model.encode([theme])[0]
            theme_similarities = np.dot(abstract_embeddings, theme_embedding) / (
                np.linalg.norm(abstract_embeddings, axis=1) * np.linalg.norm(theme_embedding)
            )
            theme_scores[theme] = float(np.mean(theme_similarities))  # Convert to Python float
            theme_frequencies[theme] = int(np.sum(theme_similarities > 0.3))  # Convert to Python int

        # Mock sentiment analysis
        sentiment = {
            'positive': np.sum(similarities > 0.5),
            'neutral': np.sum((similarities <= 0.5) & (similarities > 0.2)),
            'negative': len(abstracts) - np.sum(similarities > 0.2)
        }

        return {
            'themes': sorted(theme_scores.keys(), key=lambda x: theme_scores[x], reverse=True),
            'theme_scores': theme_scores,
            'theme_frequencies': theme_frequencies,
            'sentiment': sentiment
        }

    def _analyze_mock(self, query, abstracts):
        """Fallback mock analysis"""
        themes = [
            'clinical efficacy', 'safety profile', 'mechanism of action', 'drug resistance',
            'pharmacokinetics', 'toxicity', 'biomarkers', 'combination therapy'
        ]

        theme_scores = {theme: float(np.random.uniform(0.3, 0.9)) for theme in themes}
        theme_frequencies = {theme: int(np.random.randint(1, 10)) for theme in themes}

        sentiment = {
            'positive': len(abstracts) * 0.6,
            'neutral': len(abstracts) * 0.3,
            'negative': len(abstracts) * 0.1
        }

        return {
            'themes': sorted(theme_scores.keys(), key=lambda x: theme_scores[x], reverse=True),
            'theme_scores': theme_scores,
            'theme_frequencies': theme_frequencies,
            'sentiment': sentiment
        }

    def _get_mock_abstracts(self, query):
        """Generate mock research abstracts"""
        templates = [
            f"This study investigates the {query} compound in relation to therapeutic efficacy and safety profiles.",
            f"Recent advances in {query} research show promising results for clinical applications.",
            f"Molecular analysis of {query} reveals novel mechanisms of action against target proteins.",
            f"Clinical trials demonstrate significant improvements in patient outcomes with {query} treatment.",
            f"Pharmacokinetic studies of {query} indicate favorable drug distribution and metabolism.",
            f"Toxicity assessment of {query} shows acceptable safety margins for therapeutic use.",
            f"Biomarker discovery related to {query} treatment provides new diagnostic opportunities.",
            f"Combination therapies involving {query} show synergistic effects in preclinical models."
        ]

        return templates * 3  # Repeat for more data