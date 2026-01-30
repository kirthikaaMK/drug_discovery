from flask import Flask, render_template, request, jsonify, send_file
import time
import uuid
import os
import io
import traceback
from pathlib import Path

# Import our robust utilities
from config import config
from utils.robust_utils import (
    logger, safe_api_call, safe_model_operation,
    create_error_response, health_check, validate_data_structure
)
from agents.master_agent import MasterAgent
from utils.pdf_generator import PDFGenerator

# Initialize Flask app with config
app = Flask(__name__)
app.config.update({
    'SECRET_KEY': config.get('app', 'secret_key'),
    'DEBUG': config.get('app', 'debug')
})

# Initialize components with error handling
try:
    master_agent = MasterAgent()
    logger.info("Master agent initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize master agent: {e}")
    master_agent = None

try:
    pdf_generator = PDFGenerator()
    logger.info("PDF generator initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize PDF generator: {e}")
    pdf_generator = None

# Store analysis jobs with cleanup
jobs = {}
MAX_JOBS = 100

def cleanup_old_jobs():
    """Clean up old completed jobs"""
    current_time = time.time()
    to_remove = []

    for job_id, job in jobs.items():
        # Remove jobs older than 1 hour
        if current_time - job.get('created_at', 0) > 3600:
            to_remove.append(job_id)

    for job_id in to_remove:
        del jobs[job_id]
        logger.debug(f"Cleaned up old job: {job_id}")

    # Limit total jobs
    if len(jobs) > MAX_JOBS:
        # Remove oldest jobs
        sorted_jobs = sorted(jobs.items(), key=lambda x: x[1].get('created_at', 0))
        for job_id, _ in sorted_jobs[:len(jobs) - MAX_JOBS]:
            del jobs[job_id]
            logger.debug(f"Removed excess job: {job_id}")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        # Clean up old jobs periodically
        cleanup_old_jobs()

        # Validate input
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400

        query = data.get('query', '').strip()
        analysis_type = data.get('analysis_type', 'comprehensive')

        if not query:
            logger.warning("Analysis request missing query")
            return jsonify({'error': 'Query is required'}), 400

        if len(query) > 500:
            logger.warning(f"Query too long: {len(query)} characters")
            return jsonify({'error': 'Query too long (max 500 characters)'}), 400

        # Check if master agent is available
        if master_agent is None:
            logger.error("Master agent not initialized")
            return jsonify({'error': 'Analysis system not available'}), 503

        # Create job
        job_id = str(uuid.uuid4())
        jobs[job_id] = {
            'status': 'running',
            'progress': 0,
            'results': None,
            'summary': None,
            'created_at': time.time(),
            'query': query,
            'analysis_type': analysis_type
        }

        logger.info(f"Starting analysis job {job_id} for query: {query[:50]}...")

        # Run analysis with error handling
        def progress_callback(message, progress):
            jobs[job_id]['progress'] = min(100, max(0, progress * 100))
            jobs[job_id]['status'] = message
            logger.debug(f"Job {job_id} progress: {progress:.1%} - {message}")

        try:
            results, summary = master_agent.run_analysis(query, analysis_type, progress_callback)

            # Validate and clean results
            cleaned_results = {}
            for agent_name, result in results.items():
                try:
                    cleaned_results[agent_name] = validate_data_structure(result)
                except Exception as e:
                    logger.warning(f"Failed to validate result for {agent_name}: {e}")
                    cleaned_results[agent_name] = create_error_response(agent_name, e)

            jobs[job_id].update({
                'status': 'completed',
                'progress': 100,
                'results': cleaned_results,
                'summary': summary
            })

            logger.info(f"Analysis job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Analysis job {job_id} failed: {e}")
            jobs[job_id].update({
                'status': 'error',
                'progress': 0,
                'error': str(e)
            })
            return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

        return jsonify({'job_id': job_id})

    except Exception as e:
        logger.error(f"Unexpected error in analyze endpoint: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'Internal server error'}), 500
        jobs[job_id]['summary'] = summary
        jobs[job_id]['progress'] = 1.0
    except Exception as e:
        jobs[job_id]['status'] = 'error'
        jobs[job_id]['error'] = str(e)

    return jsonify({'job_id': job_id})

@app.route('/status/<job_id>')
def status(job_id):
    try:
        if job_id not in jobs:
            logger.warning(f"Status request for unknown job: {job_id}")
            return jsonify({'error': 'Job not found'}), 404

        job = jobs[job_id]

        # Ensure progress is a valid number
        progress = job.get('progress', 0)
        if not isinstance(progress, (int, float)) or progress < 0 or progress > 100:
            progress = 0

        response = {
            'status': job.get('status', 'unknown'),
            'progress': progress
        }

        # Add error message if present
        if 'error' in job:
            response['error'] = job['error']

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in status endpoint for job {job_id}: {e}")
        return jsonify({'error': 'Internal server error', 'status': 'error'}), 500

@app.route('/results/<job_id>')
def results(job_id):
    try:
        if job_id not in jobs:
            logger.warning(f"Results request for unknown job: {job_id}")
            return jsonify({'error': 'Job not found'}), 404

        job = jobs[job_id]

        if job.get('status') != 'completed':
            return jsonify({
                'error': 'Analysis not completed',
                'status': job.get('status', 'unknown'),
                'progress': job.get('progress', 0)
            }), 400

        if 'results' not in job or job['results'] is None:
            return jsonify({'error': 'No results available'}), 500

        # Validate results before returning
        try:
            validated_results = validate_data_structure(job['results'])
        except Exception as e:
            logger.error(f"Failed to validate results for job {job_id}: {e}")
            return jsonify({'error': 'Results validation failed'}), 500

        return jsonify({
            'results': validated_results,
            'summary': job.get('summary', 'No summary available')
        })

    except Exception as e:
        logger.error(f"Error in results endpoint for job {job_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/download/<job_id>')
def download(job_id):
    try:
        if job_id not in jobs:
            logger.warning(f"Download request for unknown job: {job_id}")
            return jsonify({'error': 'Job not found'}), 404

        job = jobs[job_id]

        if job.get('status') != 'completed':
            return jsonify({
                'error': 'Analysis not completed',
                'status': job.get('status', 'unknown')
            }), 400

        if pdf_generator is None:
            return jsonify({'error': 'PDF generation not available'}), 503

        # Get query from job data
        query = job.get('query', 'Drug Discovery Analysis')

        # Generate PDF with error handling
        try:
            pdf_buffer = io.BytesIO()
            pdf_generator.generate_report(query, job['results'], job.get('summary', ''), pdf_buffer)
            pdf_buffer.seek(0)

            return send_file(
                pdf_buffer,
                as_attachment=True,
                download_name=f'drug_discovery_report_{job_id}.pdf',
                mimetype='application/pdf'
            )

        except Exception as pdf_error:
            logger.error(f"PDF generation failed for job {job_id}: {pdf_error}")
            return jsonify({'error': 'PDF generation failed'}), 500

    except Exception as e:
        logger.error(f"Error in download endpoint for job {job_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    try:
        health_status = health_check()
        status_code = 200 if health_status['overall'] == 'healthy' else 503
        return jsonify(health_status), status_code
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'overall': 'error',
            'error': str(e),
            'timestamp': time.time()
        }), 500

@app.route('/config')
def get_config():
    """Get current configuration (without sensitive data)"""
    try:
        # Return safe config info
        safe_config = {
            'app': {
                'host': config.get('app', 'host'),
                'port': config.get('app', 'port'),
                'debug': config.get('app', 'debug')
            },
            'ml': {
                'enable_ml_prediction': config.is_ml_enabled('prediction'),
                'enable_generative_ai': config.is_ml_enabled('generative_ai'),
                'enable_nlp_analysis': config.is_ml_enabled('nlp_analysis'),
                'max_memory_gb': config.get_memory_limit()
            },
            'agents_count': 10 if config.is_ml_enabled('prediction') else 7
        }
        return jsonify(safe_config)
    except Exception as e:
        logger.error(f"Config endpoint failed: {e}")
        return jsonify({'error': 'Configuration retrieval failed'}), 500

if __name__ == '__main__':
    try:
        # Use config values
        host = config.get('app', 'host', '0.0.0.0')
        port = config.get('app', 'port', 5000)
        debug = config.get('app', 'debug', True)

        logger.info(f"Starting Drug Discovery AI System on {host}:{port}")
        app.run(debug=debug, host=host, port=port)

    except Exception as e:
        logger.critical(f"Failed to start application: {e}")
        print(f"CRITICAL: Failed to start application: {e}")
        sys.exit(1)