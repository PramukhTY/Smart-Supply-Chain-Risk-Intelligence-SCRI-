"""
Smart Supply Chain Risk Intelligence - Flask Application
Main application file that connects to MySQL and serves frontend templates
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector
from mysql.connector import Error
from datetime import datetime, date
import json
import os
from functools import wraps

app = Flask(__name__)

# Database configuration - will be set via environment or user input
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'smart_supply_chain'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'pammi@2005'),
    'port': int(os.getenv('DB_PORT', 3306))
}

# Global database connection
db_connection = None

def get_db_connection():
    """Get database connection with automatic reconnection"""
    global db_connection
    try:
        # Always check if connection is alive and reconnect if needed
        if db_connection is None:
            print(f"Creating new MySQL connection: {DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
            db_connection = mysql.connector.connect(
                host=DB_CONFIG['host'],
                database=DB_CONFIG['database'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                port=DB_CONFIG['port'],
                autocommit=False,
                connect_timeout=10,
                pool_reset_session=True
            )
            print("✓ Database connection established")
        else:
            # Check if connection is still alive
            try:
                db_connection.ping(reconnect=True, attempts=3, delay=1)
            except Error:
                # Connection is dead, recreate it
                print("Connection lost, recreating...")
                try:
                    db_connection.close()
                except:
                    pass
                db_connection = None
                return get_db_connection()  # Recursive call to create new connection
        
        return db_connection
    except Error as e:
        print(f"✗ Error connecting to MySQL: {e}")
        # Reset connection on error
        db_connection = None
        import traceback
        traceback.print_exc()
        return None
    except Exception as e:
        print(f"✗ Unexpected error connecting to MySQL: {e}")
        db_connection = None
        import traceback
        traceback.print_exc()
        return None

def init_db_connection():
    """Initialize database connection on startup"""
    conn = get_db_connection()
    if conn:
        print(f"✓ Connected to MySQL database: {DB_CONFIG['database']}")
        return True
    else:
        print("✗ Failed to connect to MySQL database")
        return False

def db_query(query, params=None, fetch=True):
    """Execute database query safely with automatic reconnection"""
    global db_connection
    max_retries = 2
    retry_count = 0
    
    while retry_count <= max_retries:
        try:
            conn = get_db_connection()
            if not conn:
                print("No database connection available")
                if retry_count < max_retries:
                    retry_count += 1
                    print(f"Retrying connection (attempt {retry_count}/{max_retries})...")
                    import time
                    time.sleep(0.5)
                    continue
                return None
            
            # Test connection with ping
            try:
                conn.ping(reconnect=True, attempts=1, delay=0.5)
            except Error as ping_error:
                print(f"Connection ping failed: {ping_error}, reconnecting...")
                db_connection = None
                if retry_count < max_retries:
                    retry_count += 1
                    continue
                return None
            
            cursor = conn.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
            else:
                conn.commit()
                result = cursor.rowcount
            
            cursor.close()
            return result
            
        except Error as e:
            error_msg = str(e)
            print(f"Database error: {e}")
            print(f"Query: {query[:100]}...")  # Print first 100 chars of query
            print(f"Params: {params}")
            
            # Check if it's a connection error
            if "Lost connection" in error_msg or "connection" in error_msg.lower() or "2006" in error_msg or "2055" in error_msg:
                print("Connection error detected, will retry...")
                db_connection = None
                if retry_count < max_retries:
                    retry_count += 1
                    print(f"Retrying query (attempt {retry_count}/{max_retries})...")
                    import time
                    time.sleep(0.5)
                    continue
                else:
                    if conn:
                        try:
                            conn.rollback()
                        except:
                            pass
                    return None
            else:
                # Other database errors, don't retry
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                return None
                
        except Exception as e:
            print(f"Unexpected error in db_query: {e}")
            import traceback
            traceback.print_exc()
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
            return None
    
    return None

# ==================== FRONTEND ROUTES ====================

@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')

@app.route('/suppliers')
def suppliers():
    """Suppliers page"""
    return render_template('suppliers.html')

@app.route('/shipments')
def shipments():
    """Shipments page"""
    return render_template('analytics.html')

@app.route('/alerts')
def alerts():
    """Alerts page"""
    return render_template('alerts.html')

@app.route('/analytics')
def analytics():
    """Analytics page"""
    return render_template('analytics.html')

# ==================== API ROUTES ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    conn = get_db_connection()
    db_status = "connected" if conn and conn.is_connected() else "disconnected"
    return jsonify({
        'success': True,
        'status': 'ok',
        'database': db_status
    })

# ==================== SUPPLIERS API ====================

@app.route('/api/suppliers', methods=['GET'])
def get_suppliers():
    """Get all suppliers"""
    try:
        # First try the complex query with metrics
        query = """
            SELECT s.*, 
                   COALESCE(m.risk_score, 0) as risk_score,
                   COALESCE(m.risk_level, 'LOW') as risk_level
            FROM suppliers s
            LEFT JOIN supplier_metrics m ON s.supplier_id = m.supplier_id
            AND m.record_date = (
                SELECT MAX(record_date) 
                FROM supplier_metrics 
                WHERE supplier_id = s.supplier_id
            )
            ORDER BY s.supplier_id
        """
        result = db_query(query)
        
        # If that fails, try a simpler query
        if result is None:
            print("Complex query failed, trying simple query...")
            query = "SELECT s.*, 0 as risk_score, 'LOW' as risk_level FROM suppliers s ORDER BY s.supplier_id"
            result = db_query(query)
        
        if result is not None:
            # Ensure result is a list
            if isinstance(result, list):
                return jsonify({'success': True, 'data': result})
            else:
                return jsonify({'success': True, 'data': []})
        else:
            print("Both queries failed")
            return jsonify({'success': False, 'error': 'Database query failed - unable to fetch suppliers'}), 500
    except Exception as e:
        import traceback
        print(f"Error in get_suppliers: {e}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/suppliers', methods=['POST'])
def create_supplier():
    """Create a new supplier"""
    data = request.json
    query = """
        INSERT INTO suppliers (name, contact_email, phone, rating)
        VALUES (%s, %s, %s, %s)
    """
    params = (
        data.get('name'),
        data.get('contact_email'),
        data.get('phone'),
        data.get('rating', 0)
    )
    result = db_query(query, params, fetch=False)
    if result is not None:
        return jsonify({'success': True, 'message': 'Supplier created successfully'})
    return jsonify({'success': False, 'error': 'Failed to create supplier'}), 500

@app.route('/api/suppliers/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    """Get a specific supplier"""
    query = "SELECT * FROM suppliers WHERE supplier_id = %s"
    result = db_query(query, (supplier_id,))
    if result and len(result) > 0:
        return jsonify({'success': True, 'data': result[0]})
    return jsonify({'success': False, 'error': 'Supplier not found'}), 404

@app.route('/api/suppliers/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    """Update a supplier"""
    data = request.json
    query = """
        UPDATE suppliers 
        SET name = %s, contact_email = %s, phone = %s, rating = %s
        WHERE supplier_id = %s
    """
    params = (
        data.get('name'),
        data.get('contact_email'),
        data.get('phone'),
        data.get('rating'),
        supplier_id
    )
    result = db_query(query, params, fetch=False)
    if result is not None:
        return jsonify({'success': True, 'message': 'Supplier updated successfully'})
    return jsonify({'success': False, 'error': 'Failed to update supplier'}), 500

@app.route('/api/suppliers/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    """Delete a supplier"""
    query = "DELETE FROM suppliers WHERE supplier_id = %s"
    result = db_query(query, (supplier_id,), fetch=False)
    if result is not None:
        return jsonify({'success': True, 'message': 'Supplier deleted successfully'})
    return jsonify({'success': False, 'error': 'Failed to delete supplier'}), 500

@app.route('/api/suppliers/<int:supplier_id>/metrics', methods=['GET'])
def get_supplier_metrics(supplier_id):
    """Get supplier metrics"""
    query = """
        SELECT * FROM supplier_metrics
        WHERE supplier_id = %s
        ORDER BY record_date DESC
        LIMIT 30
    """
    result = db_query(query, (supplier_id,))
    if result is not None:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': 'Failed to fetch metrics'}), 500

@app.route('/api/suppliers/<int:supplier_id>/compute-risk', methods=['POST'])
def compute_supplier_risk(supplier_id):
    """Compute supplier risk score"""
    query = "CALL compute_supplier_risk(%s)"
    result = db_query(query, (supplier_id,), fetch=False)
    if result is not None:
        return jsonify({'success': True, 'message': 'Risk score computed successfully'})
    return jsonify({'success': False, 'error': 'Failed to compute risk score'}), 500

# ==================== PRODUCTS API ====================

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products"""
    query = """
        SELECT p.*, s.name as supplier_name
        FROM products p
        JOIN suppliers s ON p.supplier_id = s.supplier_id
        ORDER BY p.product_id
    """
    result = db_query(query)
    if result is not None:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': 'Database query failed'}), 500

@app.route('/api/products', methods=['POST'])
def create_product():
    """Create a new product"""
    data = request.json
    query = """
        INSERT INTO products (supplier_id, name, sku, category, unit_cost, lead_time_days)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    params = (
        data.get('supplier_id'),
        data.get('name'),
        data.get('sku'),
        data.get('category'),
        data.get('unit_cost', 0),
        data.get('lead_time_days', 0)
    )
    result = db_query(query, params, fetch=False)
    if result is not None:
        return jsonify({'success': True, 'message': 'Product created successfully'})
    return jsonify({'success': False, 'error': 'Failed to create product'}), 500

# ==================== SHIPMENTS API ====================

@app.route('/api/shipments', methods=['GET'])
def get_shipments():
    """Get all shipments"""
    try:
        # Try the full query with joins first
        query = """
            SELECT sh.*, 
                   s.name as supplier_name,
                   p.name as product_name,
                   w.name as warehouse_name,
                   GREATEST(DATEDIFF(COALESCE(sh.actual_arrival_date, CURDATE()), sh.expected_arrival_date), 0) as delay_days
            FROM shipments sh
            JOIN suppliers s ON sh.supplier_id = s.supplier_id
            JOIN products p ON sh.product_id = p.product_id
            JOIN warehouses w ON sh.warehouse_id = w.warehouse_id
            ORDER BY sh.ship_date DESC
        """
        result = db_query(query)
        
        # If that fails, try a simpler query without delay calculation
        if result is None:
            print("Complex shipments query failed, trying simple query...")
            query = """
                SELECT sh.*, 
                       s.name as supplier_name,
                       p.name as product_name,
                       w.name as warehouse_name,
                       0 as delay_days
                FROM shipments sh
                JOIN suppliers s ON sh.supplier_id = s.supplier_id
                JOIN products p ON sh.product_id = p.product_id
                JOIN warehouses w ON sh.warehouse_id = w.warehouse_id
                ORDER BY sh.ship_date DESC
            """
            result = db_query(query)
        
        if result is not None:
            # Ensure result is a list
            if isinstance(result, list):
                return jsonify({'success': True, 'data': result})
            else:
                return jsonify({'success': True, 'data': []})
        else:
            print("Both shipments queries failed")
            return jsonify({'success': False, 'error': 'Database query failed - unable to fetch shipments'}), 500
    except Exception as e:
        import traceback
        print(f"Error in get_shipments: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/shipments', methods=['POST'])
def create_shipment():
    """Create a new shipment"""
    data = request.json
    query = """
        INSERT INTO shipments (supplier_id, product_id, warehouse_id, quantity, 
                              ship_date, expected_arrival_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    params = (
        data.get('supplier_id'),
        data.get('product_id'),
        data.get('warehouse_id'),
        data.get('quantity'),
        data.get('ship_date'),
        data.get('expected_arrival_date'),
        data.get('status', 'CREATED')
    )
    result = db_query(query, params, fetch=False)
    if result is not None:
        # Create shipment event
        event_query = """
            INSERT INTO shipment_events (shipment_id, event_time, event_type, details)
            VALUES (LAST_INSERT_ID(), NOW(), 'CREATED', 'created')
        """
        db_query(event_query, fetch=False)
        return jsonify({'success': True, 'message': 'Shipment created successfully'})
    return jsonify({'success': False, 'error': 'Failed to create shipment'}), 500

@app.route('/api/shipments/<int:shipment_id>', methods=['PUT'])
def update_shipment(shipment_id):
    """Update a shipment"""
    data = request.json
    query = """
        UPDATE shipments 
        SET supplier_id = %s, product_id = %s, warehouse_id = %s, quantity = %s,
            ship_date = %s, expected_arrival_date = %s, actual_arrival_date = %s, status = %s
        WHERE shipment_id = %s
    """
    params = (
        data.get('supplier_id'),
        data.get('product_id'),
        data.get('warehouse_id'),
        data.get('quantity'),
        data.get('ship_date'),
        data.get('expected_arrival_date'),
        data.get('actual_arrival_date'),
        data.get('status'),
        shipment_id
    )
    result = db_query(query, params, fetch=False)
    if result is not None:
        # Create event if status changed
        if 'status' in data:
            event_query = """
                INSERT INTO shipment_events (shipment_id, event_time, event_type, details)
                VALUES (%s, NOW(), %s, %s)
            """
            db_query(event_query, (shipment_id, data.get('status'), 'status updated'), fetch=False)
        return jsonify({'success': True, 'message': 'Shipment updated successfully'})
    return jsonify({'success': False, 'error': 'Failed to update shipment'}), 500

@app.route('/api/shipments/<int:shipment_id>/events', methods=['GET'])
def get_shipment_events(shipment_id):
    """Get events for a shipment"""
    query = """
        SELECT * FROM shipment_events
        WHERE shipment_id = %s
        ORDER BY event_time DESC
    """
    result = db_query(query, (shipment_id,))
    if result is not None:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': 'Failed to fetch events'}), 500

# ==================== INVENTORY API ====================

@app.route('/api/inventory', methods=['GET'])
def get_inventory():
    """Get all inventory"""
    query = """
        SELECT i.*, 
               p.name as product_name,
               p.sku,
               w.name as warehouse_name,
               CASE 
                   WHEN i.quantity < i.safety_stock THEN 'CRITICAL'
                   WHEN i.quantity < i.reorder_threshold THEN 'LOW'
                   ELSE 'OK'
               END as status
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN warehouses w ON i.warehouse_id = w.warehouse_id
        ORDER BY i.last_updated DESC
    """
    result = db_query(query)
    if result is not None:
        return jsonify({'success': True, 'data': result})
    return jsonify({'success': False, 'error': 'Database query failed'}), 500

@app.route('/api/inventory', methods=['POST'])
def create_inventory():
    """Create or update inventory"""
    data = request.json
    query = """
        INSERT INTO inventory (product_id, warehouse_id, quantity, reorder_threshold, safety_stock)
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE 
            quantity = VALUES(quantity),
            reorder_threshold = VALUES(reorder_threshold),
            safety_stock = VALUES(safety_stock),
            last_updated = CURRENT_TIMESTAMP
    """
    params = (
        data.get('product_id'),
        data.get('warehouse_id'),
        data.get('quantity'),
        data.get('reorder_threshold'),
        data.get('safety_stock')
    )
    result = db_query(query, params, fetch=False)
    if result is not None:
        return jsonify({'success': True, 'message': 'Inventory updated successfully'})
    return jsonify({'success': False, 'error': 'Failed to update inventory'}), 500

@app.route('/api/inventory/<int:inventory_id>', methods=['PUT'])
def update_inventory(inventory_id):
    """Update inventory"""
    data = request.json
    query = """
        UPDATE inventory 
        SET quantity = %s, reorder_threshold = %s, safety_stock = %s
        WHERE inventory_id = %s
    """
    params = (
        data.get('quantity'),
        data.get('reorder_threshold'),
        data.get('safety_stock'),
        inventory_id
    )
    result = db_query(query, params, fetch=False)
    if result is not None:
        return jsonify({'success': True, 'message': 'Inventory updated successfully'})
    return jsonify({'success': False, 'error': 'Failed to update inventory'}), 500

# ==================== ALERTS API ====================

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get all alerts"""
    try:
        resolved = request.args.get('resolved', 'false').lower() == 'true'
        query = """
            SELECT * FROM alerts
            WHERE resolved = %s
            ORDER BY created_at DESC
        """
        result = db_query(query, (1 if resolved else 0,))
        if result is not None:
            return jsonify({'success': True, 'data': result if result else []})
        return jsonify({'success': False, 'error': 'Database query failed'}), 500
    except Exception as e:
        print(f"Error in get_alerts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    """Resolve an alert"""
    query = """
        UPDATE alerts 
        SET resolved = 1, resolved_at = NOW()
        WHERE alert_id = %s
    """
    result = db_query(query, (alert_id,), fetch=False)
    if result is not None:
        return jsonify({'success': True, 'message': 'Alert resolved successfully'})
    return jsonify({'success': False, 'error': 'Failed to resolve alert'}), 500

@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """Create a new alert manually (for testing)"""
    data = request.json
    query = """
        INSERT INTO alerts (created_at, alert_type, severity, entity_type, entity_id, message, resolved)
        VALUES (NOW(), %s, %s, %s, %s, %s, 0)
    """
    params = (
        data.get('alert_type', 'CUSTOM'),
        data.get('severity', 'INFO'),
        data.get('entity_type', 'SYSTEM'),
        data.get('entity_id', 0),
        data.get('message', 'Custom alert')
    )
    result = db_query(query, params, fetch=False)
    if result is not None:
        return jsonify({'success': True, 'message': 'Alert created successfully'})
    return jsonify({'success': False, 'error': 'Failed to create alert'}), 500

@app.route('/api/alerts/generate-test', methods=['POST'])
def generate_test_alerts():
    """Generate test alerts for demonstration"""
    try:
        alerts_created = []
        
        # Create a shipment delay alert
        query1 = """
            INSERT INTO alerts (created_at, alert_type, severity, entity_type, entity_id, message, resolved)
            VALUES (NOW(), 'SHIPMENT_DELAY', 'WARN', 'SHIPMENT', 1, 'Test: Shipment #1 is delayed', 0)
        """
        if db_query(query1, fetch=False) is not None:
            alerts_created.append('Shipment delay alert')
        
        # Create a low inventory alert
        query2 = """
            INSERT INTO alerts (created_at, alert_type, severity, entity_type, entity_id, message, resolved)
            VALUES (NOW(), 'LOW_INVENTORY', 'WARN', 'INVENTORY', 1, 'Test: Inventory low for product at warehouse', 0)
        """
        if db_query(query2, fetch=False) is not None:
            alerts_created.append('Low inventory alert')
        
        # Create a critical alert
        query3 = """
            INSERT INTO alerts (created_at, alert_type, severity, entity_type, entity_id, message, resolved)
            VALUES (NOW(), 'LOW_INVENTORY', 'CRITICAL', 'INVENTORY', 2, 'Test: CRITICAL - Inventory below safety stock', 0)
        """
        if db_query(query3, fetch=False) is not None:
            alerts_created.append('Critical inventory alert')
        
        return jsonify({
            'success': True, 
            'message': f'Created {len(alerts_created)} test alerts',
            'alerts': alerts_created
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== DASHBOARD METRICS API ====================

@app.route('/api/dashboard/metrics', methods=['GET'])
def get_dashboard_metrics():
    """Get dashboard metrics"""
    metrics = {}
    
    # Active suppliers count
    query = "SELECT COUNT(*) as count FROM suppliers"
    result = db_query(query)
    if result:
        metrics['suppliers'] = result[0]['count']
    
    # Shipments in transit
    query = "SELECT COUNT(*) as count FROM shipments WHERE status = 'IN_TRANSIT'"
    result = db_query(query)
    if result:
        metrics['transit'] = result[0]['count']
    
    # Open alerts
    query = "SELECT COUNT(*) as count FROM alerts WHERE resolved = 0"
    result = db_query(query)
    if result:
        metrics['alerts'] = result[0]['count']
    
    # Inventory health
    query = """
        SELECT COUNT(*) as count FROM inventory 
        WHERE quantity < safety_stock
    """
    result = db_query(query)
    if result:
        critical_count = result[0]['count']
        if critical_count > 0:
            metrics['inventory'] = f'{critical_count} Critical'
        else:
            metrics['inventory'] = 'OK'
    
    return jsonify({'success': True, 'data': metrics})

@app.route('/api/dashboard/supplier-risk', methods=['GET'])
def get_supplier_risk_summary():
    """Get supplier risk summary"""
    try:
        # Try using the view first
        query = """
            SELECT * FROM supplier_risk_summary
            ORDER BY risk_score DESC
        """
        result = db_query(query)
        
        # If view doesn't exist or query fails, use a direct query
        if result is None:
            print("View query failed, trying direct query...")
            query = """
                SELECT s.supplier_id, s.name, 
                       COALESCE(m.record_date, CURDATE()) as record_date,
                       COALESCE(m.risk_score, 0) as risk_score,
                       COALESCE(m.risk_level, 'LOW') as risk_level,
                       COALESCE(m.on_time_rate, 1.0) as on_time_rate,
                       COALESCE(m.avg_delay_days, 0) as avg_delay_days,
                       COALESCE(m.defect_rate, 0) as defect_rate
                FROM suppliers s
                LEFT JOIN supplier_metrics m ON s.supplier_id = m.supplier_id
                AND m.record_date = (
                    SELECT MAX(record_date) 
                    FROM supplier_metrics 
                    WHERE supplier_id = s.supplier_id
                )
                ORDER BY COALESCE(m.risk_score, 0) DESC
            """
            result = db_query(query)
        
        if result is not None:
            return jsonify({'success': True, 'data': result if result else []})
        return jsonify({'success': False, 'error': 'Database query failed'}), 500
    except Exception as e:
        import traceback
        print(f"Error in get_supplier_risk_summary: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dashboard/delayed-shipments', methods=['GET'])
def get_delayed_shipments():
    """Get delayed shipments overview"""
    try:
        query = """
            SELECT * FROM delayed_shipments_overview
            ORDER BY delay_days DESC
        """
        result = db_query(query)
        if result is not None:
            return jsonify({'success': True, 'data': result if result else []})
        return jsonify({'success': False, 'error': 'Database query failed'}), 500
    except Exception as e:
        print(f"Error in get_delayed_shipments: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== WAREHOUSES API ====================

@app.route('/api/warehouses', methods=['GET'])
def get_warehouses():
    """Get all warehouses"""
    try:
        query = "SELECT * FROM warehouses ORDER BY warehouse_id"
        result = db_query(query)
        if result is not None:
            # If no warehouses exist, return empty array instead of error
            return jsonify({'success': True, 'data': result if result else []})
        return jsonify({'success': False, 'error': 'Database query failed'}), 500
    except Exception as e:
        print(f"Error in get_warehouses: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/warehouses', methods=['POST'])
def create_warehouse():
    """Create a new warehouse"""
    data = request.json
    query = "INSERT INTO warehouses (name, location) VALUES (%s, %s)"
    params = (data.get('name'), data.get('location'))
    result = db_query(query, params, fetch=False)
    if result is not None:
        return jsonify({'success': True, 'message': 'Warehouse created successfully'})
    return jsonify({'success': False, 'error': 'Failed to create warehouse'}), 500

# ==================== MAIN APPLICATION ====================

if __name__ == '__main__':
    print("=" * 60)
    print("Smart Supply Chain Risk Intelligence - Flask Application")
    print("=" * 60)
    
    # Try to initialize database connection
    if not init_db_connection():
        print("\n⚠ Warning: Database connection failed!")
        print("Please ensure MySQL is running and credentials are correct.")
        print("You can set environment variables:")
        print("  DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT")
        print("\nContinuing anyway... You can configure later.\n")
    
    # Run the application
    port = int(os.getenv('PORT', 5000))
    print(f"\n🚀 Starting Flask server on http://localhost:{port}")
    print(f"📊 Database: {DB_CONFIG['database']} @ {DB_CONFIG['host']}")
    print("\nPress CTRL+C to stop the server\n")
    
    app.run(host='0.0.0.0', port=port, debug=True)

