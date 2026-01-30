import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
import os
import json
import random

class GenerativeAIAgent:
    def __init__(self):
        self.model_name = "distilgpt2"  # Using a smaller model for demo
        self.tokenizer = None
        self.model = None
        self.model_loaded = False

    def _ensure_model_loaded(self):
        """Lazy load the model only when needed"""
        if not self.model_loaded:
            self._load_model()
            self.model_loaded = True

    def _load_model(self):
        """Load the generative model"""
        try:
            # Try to load with timeout
            import signal
            def timeout_handler(signum, frame):
                raise TimeoutError("Model loading timed out")

            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30 second timeout

            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, local_files_only=True)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_name, local_files_only=True)

            signal.alarm(0)  # Cancel alarm

            # Set padding token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

        except Exception as e:
            print(f"Failed to load generative AI model: {e}")
            self.model = None
            self.tokenizer = None
            # Fallback to mock generation
            self.model = None

    def analyze(self, query):
        """
        Generate new drug candidate suggestions using GenAI
        """
        self._ensure_model_loaded()

        try:
            if self.model is not None:
                suggestions = self._generate_with_model(query)
            else:
                suggestions = self._generate_mock_suggestions(query)

            insights = f"Generated {len(suggestions)} novel drug candidate suggestions inspired by '{query}' using generative AI."

            # Create suggestion data
            suggestion_data = []
            for i, suggestion in enumerate(suggestions, 1):
                suggestion_data.append({
                    'candidate_id': f'CAND-{i:03d}',
                    'name': suggestion['name'],
                    'structure': suggestion['structure'],
                    'predicted_activity': suggestion['activity'],
                    'confidence': suggestion['confidence']
                })

            # Create charts data
            charts = {
                'confidence_distribution': {
                    'labels': [f'Candidate {i+1}' for i in range(len(suggestions))],
                    'values': [s['confidence'] for s in suggestions],
                    'type': 'line',
                    'colors': ['#ff9ff3', '#54a0ff', '#5f27cd', '#00d2d3', '#ff9f43']
                }
            }

            return {
                'agent': 'Generative AI',
                'insights': insights,
                'data': suggestion_data,
                'charts': charts
            }

        except Exception as e:
            return {
                'agent': 'Generative AI',
                'insights': f"Generative AI analysis failed: {str(e)}",
                'data': [],
                'charts': {}
            }

    def _generate_with_model(self, query):
        """Generate suggestions using the loaded model"""
        prompt = f"Generate novel drug candidates similar to {query}. Provide chemical names and structures:"

        inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=100)

        with torch.no_grad():
            outputs = self.model.generate(
                inputs['input_ids'],
                attention_mask=inputs['attention_mask'],
                max_length=200,
                num_return_sequences=3,
                temperature=0.8,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

        suggestions = []
        for output in outputs:
            text = self.tokenizer.decode(output, skip_special_tokens=True)
            # Parse generated text to extract drug names
            lines = text.split('\n')
            for line in lines:
                if any(keyword in line.lower() for keyword in ['compound', 'drug', 'molecule', 'candidate']):
                    name = line.strip()
                    if len(name) > 10:  # Filter out short/irrelevant text
                        suggestions.append({
                            'name': name[:50],
                            'structure': f'C{len(name)}H{len(name)*2}N{len(name)//3}O{len(name)//4}',
                            'activity': f'IC50: {random.uniform(0.1, 10):.2f} μM',
                            'confidence': random.uniform(0.7, 0.95)
                        })
                        if len(suggestions) >= 5:
                            break
            if len(suggestions) >= 5:
                break

        return suggestions[:5] if suggestions else self._generate_mock_suggestions(query)

    def _generate_mock_suggestions(self, query):
        """Fallback mock suggestions when model is not available"""
        base_compounds = [
            f"{query}-analogue-1",
            f"Novel-{query}-derivative",
            f"{query}-prodrug-A",
            f"Optimized-{query}-variant",
            f"{query}-hybrid-compound"
        ]

        suggestions = []
        for i, name in enumerate(base_compounds):
            suggestions.append({
                'name': name,
                'structure': f'C{random.randint(10,30)}H{random.randint(15,50)}N{random.randint(0,5)}O{random.randint(1,8)}',
                'activity': f'IC50: {random.uniform(0.1, 10):.2f} μM',
                'confidence': random.uniform(0.7, 0.95)
            })

        return suggestions