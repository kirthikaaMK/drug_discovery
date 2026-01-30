import time
from .market_agent import MarketIntelligenceAgent
from .exim_agent import EXIMAgent
from .patent_agent import PatentAgent
from .clinical_agent import ClinicalAgent
from .internal_agent import InternalAgent
from .web_agent import WebAgent
from .literature_agent import LiteratureAgent
from config import config
from utils.robust_utils import logger, create_error_response, check_memory_usage

class MasterAgent:
    def __init__(self):
        self.agents = {}

        # Initialize core agents (always available)
        core_agents = {
            'market': MarketIntelligenceAgent,
            'exim': EXIMAgent,
            'patent': PatentAgent,
            'clinical': ClinicalAgent,
            'internal': InternalAgent,
            'web': WebAgent,
            'literature': LiteratureAgent
        }

        for name, agent_class in core_agents.items():
            try:
                self.agents[name] = agent_class()
                logger.debug(f"Initialized {name} agent")
            except Exception as e:
                logger.error(f"Failed to initialize {name} agent: {e}")
                # Create a fallback agent that returns error responses
                self.agents[name] = self._create_fallback_agent(name, e)

        # Initialize ML agents conditionally
        ml_agents = {
            'ml_prediction': ('ml_prediction_agent', 'prediction', 'MLPredictionAgent'),
            'generative_ai': ('generative_ai_agent', 'generative_ai', 'GenerativeAIAgent'),
            'nlp_analysis': ('nlp_analysis_agent', 'nlp_analysis', 'NLPAnalysisAgent')
        }

        for agent_name, (module_name, feature, class_name) in ml_agents.items():
            if config.is_ml_enabled(feature):
                try:
                    module = __import__(f'agents.{module_name}', fromlist=[module_name])
                    agent_class = getattr(module, class_name)
                    self.agents[agent_name] = agent_class()
                    logger.debug(f"Initialized {agent_name} agent")
                except Exception as e:
                    logger.warning(f"ML agent {agent_name} disabled: {e}")
                    self.agents[agent_name] = self._create_fallback_agent(agent_name, e)
            else:
                logger.info(f"ML agent {agent_name} disabled in config")
                self.agents[agent_name] = self._create_fallback_agent(
                    agent_name,
                    Exception(f"{agent_name} disabled in configuration")
                )

        logger.info(f"Initialized {len(self.agents)} agents total")

    def _create_fallback_agent(self, name, error):
        """Create a fallback agent that returns error responses"""
        class FallbackAgent:
            def __init__(self, agent_name, exception):
                self.agent_name = agent_name
                self.exception = exception

            def analyze(self, query):
                return create_error_response(self.agent_name, self.exception)

        return FallbackAgent(name, error)

    def run_analysis(self, query, analysis_type, progress_callback=None):
        """
        Run analysis based on type with robust error handling
        analysis_type: 'comprehensive', 'patent_focus', 'clinical_focus', 'market_focus'
        """
        if not query or not isinstance(query, str):
            raise ValueError("Invalid query provided")

        if analysis_type not in ['comprehensive', 'patent_focus', 'clinical_focus', 'market_focus']:
            analysis_type = 'comprehensive'
            logger.warning(f"Invalid analysis type, defaulting to comprehensive")

        # Check memory before starting
        if not check_memory_usage():
            logger.warning("High memory usage detected, proceeding cautiously")

        agent_configs = {
            'comprehensive': ['market', 'exim', 'patent', 'clinical', 'internal', 'web', 'literature', 'ml_prediction', 'generative_ai', 'nlp_analysis'],
            'patent_focus': ['patent', 'clinical', 'internal', 'literature', 'nlp_analysis'],
            'clinical_focus': ['clinical', 'market', 'internal', 'literature', 'ml_prediction', 'nlp_analysis'],
            'market_focus': ['market', 'exim', 'web', 'literature', 'ml_prediction']
        }

        selected_agents = agent_configs.get(analysis_type, agent_configs['comprehensive'])

        # Filter to only available agents
        available_agents = [name for name in selected_agents if name in self.agents]
        if len(available_agents) != len(selected_agents):
            missing = set(selected_agents) - set(available_agents)
            logger.warning(f"Some agents not available: {missing}")

        results = {}
        total_agents = len(available_agents)

        if progress_callback:
            progress_callback("Starting analysis...", 0)

        for i, agent_name in enumerate(available_agents):
            try:
                if progress_callback:
                    progress_callback(f"Running {agent_name.replace('_', ' ').title()} agent...", i / total_agents)

                agent = self.agents[agent_name]
                start_time = time.time()

                result = agent.analyze(query)

                elapsed = time.time() - start_time
                logger.debug(f"{agent_name} agent completed in {elapsed:.2f}s")

                # Validate result structure
                if not isinstance(result, dict) or 'agent' not in result:
                    logger.warning(f"Invalid result structure from {agent_name}")
                    result = create_error_response(agent_name, Exception("Invalid result structure"))

                results[agent_name] = result

            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {e}")
                results[agent_name] = create_error_response(agent_name, e)

            # Periodic memory check
            if i % 3 == 0:  # Check every 3 agents
                check_memory_usage()

        if progress_callback:
            progress_callback("Synthesizing results...", 0.95)

        # Synthesize summary
        try:
            summary = self._synthesize_results(results, query)
        except Exception as e:
            logger.error(f"Failed to synthesize results: {e}")
            summary = f"## Analysis Summary for '{query}'\n\nError synthesizing results: {e}"

        if progress_callback:
            progress_callback("Analysis complete!", 1.0)

        logger.info(f"Analysis completed for query '{query[:50]}...' with {len(results)} results")
        return results, summary

        return results, summary

    def _synthesize_results(self, results, query):
        """Synthesize a comprehensive summary from all agent results"""
        summary = f"## Analysis Summary for '{query}'\n\n"

        # Executive summary
        summary += "### Executive Summary\n"
        summary += f"This analysis covers {len(results)} aspects of the query '{query}'.\n\n"

        # Key findings from each agent
        for agent_name, result in results.items():
            if 'insights' in result:
                summary += f"**{agent_name.title()} Insights:** {result['insights'][:200]}...\n\n"

        # Recommendations
        summary += "### Strategic Recommendations\n"
        summary += "- Review patent landscape for IP opportunities\n"
        summary += "- Monitor clinical trial progress\n"
        summary += "- Assess market potential and competition\n"
        summary += "- Consider regulatory and trade implications\n"
        summary += "- Review latest scientific literature\n\n"

        return summary