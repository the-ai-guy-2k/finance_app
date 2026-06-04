from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.utils import secure_filename
import os
from app.utils.storage import load_transactions, save_transactions, get_default_goals, reset_demo_data
from app.utils.normalize import normalize_transaction
from app.utils.config_manager import config
from app.services.openai_service import OpenAIService
from app.services.openai_receipt_service import OpenAIReceiptParsingService
from app.utils.logging_service import log_error, log_info, ErrorCategory

bp = Blueprint('main', __name__)

ai = OpenAIService()
receipt_parser = OpenAIReceiptParsingService()

# Default goal for MVP testing
DEFAULT_GOAL = {
    'id': 'goal_emergency_fund',
    'name': 'Emergency Fund Goal',
    'target': 5000.0,
    'description': 'Build emergency fund'
}


@bp.route('/')
def dashboard():
    if not current_app.config.get('PREFLIGHT_SUCCESS'):
        errors = current_app.config.get('PREFLIGHT_ERRORS', [])
        return render_template('error.html', errors=errors, title='Preflight Validation Failed'), 500
    
    txs = load_transactions()
    goals = get_default_goals()
    return render_template('dashboard.html', transactions=txs, goals=goals)


@bp.route('/upload_receipt', methods=['GET', 'POST'])
def upload_receipt():
    if not current_app.config.get('PREFLIGHT_SUCCESS'):
        flash('Application preflight validation failed', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        f = request.files.get('receipt')
        if not f or f.filename == '':
            flash('No file selected', 'warning')
            return redirect(url_for('main.upload_receipt'))
        
        # Validate file format
        allowed_formats = config.get('upload.allowed_receipt_formats', ['png', 'jpg', 'jpeg', 'webp'])
        ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
        if ext not in allowed_formats:
            log_error(ErrorCategory.FILE_UPLOAD_ERROR, f"Invalid receipt format: {ext}")
            flash(f'Invalid format. Allowed: {", ".join(allowed_formats)}', 'error')
            return redirect(url_for('main.upload_receipt'))
        
        # Validate file size
        max_size_mb = config.get('upload.max_size_mb', 10)
        f.seek(0, os.SEEK_END)
        size_bytes = f.tell()
        f.seek(0)
        if size_bytes > max_size_mb * 1024 * 1024:
            log_error(ErrorCategory.FILE_UPLOAD_ERROR, f"File too large: {size_bytes} bytes")
            flash(f'File too large. Max: {max_size_mb}MB', 'error')
            return redirect(url_for('main.upload_receipt'))
        
        # Save file
        upload_dir = os.path.join(os.path.dirname(__file__), '..', '..', config.get('upload.folder', 'uploads'))
        os.makedirs(upload_dir, exist_ok=True)
        filename = secure_filename(f.filename)
        path = os.path.join(upload_dir, filename)
        try:
            f.save(path)
            log_info(f"Receipt uploaded: {filename}")
        except Exception as e:
            log_error(ErrorCategory.FILE_UPLOAD_ERROR, "Failed to save receipt", e)
            flash('Failed to save receipt', 'error')
            return redirect(url_for('main.upload_receipt'))
        
        # Parse receipt using OpenAI
        parsed = receipt_parser.parse_receipt_image(path)
        txs = load_transactions()
        tx = normalize_transaction(parsed)
        txs.append(tx)
        if save_transactions(txs):
            log_info(f"Receipt parsed and transaction created: {parsed.get('merchant', 'unknown')} - ${parsed.get('amount', '0.00')}")
            flash(f"Receipt parsed: {parsed.get('merchant', 'Receipt')} - ${parsed.get('amount', '0.00')}", 'success')
        else:
            flash('Receipt parsed but failed to save transaction', 'warning')
        return redirect(url_for('main.dashboard'))
    
    return render_template('upload_receipt.html')


@bp.route('/upload_csv', methods=['GET', 'POST'])
def upload_csv():
    if not current_app.config.get('PREFLIGHT_SUCCESS'):
        flash('Application preflight validation failed', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        f = request.files.get('csvfile')
        if not f or f.filename == '':
            flash('No file selected', 'warning')
            return redirect(url_for('main.upload_csv'))
        
        # Validate CSV format
        ext = f.filename.rsplit('.', 1)[-1].lower() if '.' in f.filename else ''
        if ext != 'csv':
            log_error(ErrorCategory.CSV_PARSE_ERROR, f"Invalid CSV format: {ext}")
            flash('Invalid format. Please upload a .csv file', 'error')
            return redirect(url_for('main.upload_csv'))
        
        # Validate file size
        max_size_mb = config.get('upload.max_size_mb', 10)
        f.seek(0, os.SEEK_END)
        size_bytes = f.tell()
        f.seek(0)
        if size_bytes > max_size_mb * 1024 * 1024:
            log_error(ErrorCategory.FILE_UPLOAD_ERROR, f"CSV file too large: {size_bytes} bytes")
            flash(f'File too large. Max: {max_size_mb}MB', 'error')
            return redirect(url_for('main.upload_csv'))
        
        try:
            content = f.read().decode('utf-8').splitlines()
            if not content:
                flash('CSV file is empty', 'warning')
                return redirect(url_for('main.upload_csv'))
            
            # Parse CSV: first row is header
            headers = [h.strip().lower() for h in content[0].split(',')]
            txs = load_transactions()
            added = 0
            
            for row in content[1:]:
                if not row.strip():
                    continue
                vals = [v.strip() for v in row.split(',')]
                item = dict(zip(headers, vals))
                try:
                    tx = normalize_transaction(item)
                    txs.append(tx)
                    added += 1
                except Exception as e:
                    log_error(ErrorCategory.CSV_PARSE_ERROR, f"Failed to parse row: {row[:50]}...", e)
                    continue
            
            if save_transactions(txs):
                log_info(f"CSV uploaded with {added} transactions")
                flash(f'CSV ingested: {added} transactions added', 'success')
            else:
                flash(f'CSV ingested but failed to save ({added} transactions)', 'warning')
        except Exception as e:
            log_error(ErrorCategory.CSV_PARSE_ERROR, "Failed to parse CSV", e)
            flash('Failed to parse CSV file', 'error')
        
        return redirect(url_for('main.dashboard'))
    
    return render_template('upload_csv.html')


@bp.route('/add_transaction', methods=['GET', 'POST'])
def add_transaction():
    if not current_app.config.get('PREFLIGHT_SUCCESS'):
        flash('Application preflight validation failed', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            form = request.form.to_dict()
            tx = normalize_transaction(form)
            txs = load_transactions()
            txs.append(tx)
            if save_transactions(txs):
                log_info(f"Transaction added: {tx['merchant']} - {tx['amount']}")
                flash('Transaction added', 'success')
            else:
                flash('Failed to save transaction', 'error')
        except Exception as e:
            log_error(ErrorCategory.VALIDATION_ERROR, "Failed to add transaction", e)
            flash('Invalid transaction data', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('add_transaction.html')


@bp.route('/demo_reset', methods=['GET', 'POST'])
def demo_reset():
    if request.method == 'POST':
        if request.form.get('confirm') != 'yes':
            flash('Confirmation required. Check the box to proceed.', 'warning')
            return redirect(url_for('main.demo_reset'))
        upload_folder = config.get('upload.folder', 'uploads')
        summary = reset_demo_data(upload_folder)
        log_info(f"Demo reset completed: {summary}")
        flash(
            'Demo data reset. Transactions, uploads, and demo logs cleared. Configuration unchanged.',
            'success',
        )
        return redirect(url_for('main.dashboard'))
    return render_template('demo_reset.html')


@bp.route('/insights')
def insights():
    if not current_app.config.get('PREFLIGHT_SUCCESS'):
        flash('Application preflight validation failed', 'error')
        return redirect(url_for('main.dashboard'))
    
    txs = load_transactions()
    insight_text = ai.generate_insights(txs) if txs else 'No transactions to analyze.'
    return render_template('insights.html', insights=insight_text)
