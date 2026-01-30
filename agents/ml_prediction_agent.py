import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import os
import json

class MLPredictionAgent:
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self._load_or_train_models()

    def _load_or_train_models(self):
        """Load pre-trained models or train new ones"""
        # Mock drug property data for training
        drug_data = {
            'molecular_weight': np.random.uniform(100, 500, 1000),
            'logp': np.random.uniform(-2, 6, 1000),
            'hbd': np.random.randint(0, 10, 1000),
            'hba': np.random.randint(0, 15, 1000),
            'tpsa': np.random.uniform(0, 200, 1000),
            'toxicity': np.random.uniform(0, 1, 1000),
            'solubility': np.random.uniform(-10, 2, 1000),
            'bioavailability': np.random.uniform(0, 100, 1000)
        }

        df = pd.DataFrame(drug_data)

        # Train models for different properties
        properties = ['toxicity', 'solubility', 'bioavailability']
        for prop in properties:
            X = df[['molecular_weight', 'logp', 'hbd', 'hba', 'tpsa']]
            y = df[prop]

            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)

            model = RandomForestRegressor(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)

            self.models[prop] = model
            self.scalers[prop] = scaler

    def analyze(self, query):
        """
        Predict drug properties using ML models
        """
        try:
            # Generate mock molecular descriptors for the query
            # In production, this would use actual molecular structure
            descriptors = self._get_molecular_descriptors(query)

            predictions = {}
            for prop, model in self.models.items():
                # Ensure descriptors are in the correct order for the scaler
                feature_order = ['molecular_weight', 'logp', 'hbd', 'hba', 'tpsa']
                feature_values = [descriptors[feat] for feat in feature_order]
                
                scaled_features = self.scalers[prop].transform([feature_values])
                prediction = model.predict(scaled_features)[0]
                
                # Ensure prediction is a number
                if isinstance(prediction, (int, float, np.number)):
                    predictions[prop] = float(prediction)
                else:
                    raise ValueError(f"Model returned non-numeric prediction: {type(prediction)}")

            insights = f"ML predictions for '{query}': Toxicity risk: {predictions['toxicity']:.2f}, Solubility: {predictions['solubility']:.2f}, Bioavailability: {predictions['bioavailability']:.1f}%"

            # Create prediction data
            prediction_data = [
                {'property': 'Toxicity Risk', 'value': predictions['toxicity'], 'unit': 'score (0-1)'},
                {'property': 'Solubility', 'value': predictions['solubility'], 'unit': 'logS'},
                {'property': 'Bioavailability', 'value': predictions['bioavailability'], 'unit': '%'},
            ]

            # Create charts data
            charts = {
                'predictions': {
                    'labels': ['Toxicity Risk', 'Solubility (logS)', 'Bioavailability (%)'],
                    'values': [predictions['toxicity'], predictions['solubility'], predictions['bioavailability']],
                    'type': 'bar',
                    'colors': ['#ff6b6b', '#4ecdc4', '#45b7d1']
                }
            }

            return {
                'agent': 'ML Predictions',
                'insights': insights,
                'data': prediction_data,
                'charts': charts
            }

        except Exception as e:
            return {
                'agent': 'ML Predictions',
                'insights': f"ML prediction failed: {str(e)}",
                'data': [],
                'charts': {}
            }

    def _get_molecular_descriptors(self, query):
        """Generate mock molecular descriptors based on drug name"""
        # Simple hash-based approach to generate consistent descriptors
        query_hash = hash(query) % 10000

        return {
            'molecular_weight': 200 + (query_hash % 300),
            'logp': -1 + (query_hash % 7),
            'hbd': query_hash % 8,
            'hba': 2 + (query_hash % 10),
            'tpsa': 40 + (query_hash % 120)
        }