# Smart Supply Chain Risk Intelligence (SCRI) - Flask Application

A complete Flask-based web application for managing supply chain risks, suppliers, shipments, inventory, and alerts.

> 📖 **For detailed project description, see [PROJECT_DESCRIPTION.md](PROJECT_DESCRIPTION.md)**

## Features

- **Dashboard**: Real-time metrics and overview
- **Suppliers Management**: Add, view, and manage suppliers with risk scoring
- **Shipments Tracking**: Monitor shipments and their status
- **Alerts System**: View and manage system alerts
- **Analytics**: Supplier risk analysis and delayed shipments overview
- **Inventory Management**: Track inventory levels across warehouses

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Database Setup

1. Make sure MySQL is running
2. Create the database by running the SQL file:
   ```bash
   mysql -u root -p < SCRI/db/smart_supply_chain.sql
   ```

### 3. Configure Database Connection

You can set database credentials in two ways:

**Option 1: Environment Variables**
```bash
export DB_HOST=localhost
export DB_NAME=smart_supply_chain
export DB_USER=root
export DB_PASSWORD=your_password
export DB_PORT=3306
```

**Option 2: Edit app.py directly**
Edit the `DB_CONFIG` dictionary in `app.py` with your credentials.

### 4. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## Project Structure

```
.
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── templates/            # HTML templates
│   ├── index.html
│   ├── suppliers.html
│   ├── analytics.html
│   ├── alerts.html
│   └── 404.html
└── static/              # Static files (CSS, JS)
    ├── styles.css
    └── script.js
```

## API Endpoints

- `GET /api/suppliers` - Get all suppliers
- `POST /api/suppliers` - Create a new supplier
- `GET /api/shipments` - Get all shipments
- `POST /api/shipments` - Create a new shipment
- `GET /api/alerts` - Get all alerts
- `GET /api/dashboard/metrics` - Get dashboard metrics
- And more...

## Usage

1. Start the application: `python app.py`
2. Open your browser to `http://localhost:5000`
3. Navigate through the different sections:
   - **Home**: Dashboard with key metrics
   - **Suppliers**: Manage suppliers and view risk scores
   - **Shipments**: Track shipments and view analytics
   - **Alerts**: Monitor and resolve system alerts

## Database Schema

The application uses the following main tables:
- `suppliers` - Supplier information
- `products` - Product catalog
- `shipments` - Shipment tracking
- `inventory` - Inventory levels
- `alerts` - System alerts
- `supplier_metrics` - Supplier performance metrics
- `warehouses` - Warehouse locations

See `SCRI/db/smart_supply_chain.sql` for the complete schema.

"# Smart-Supply-Chain-Risk-Intelligence-SCRI-" 
"# Smart-Supply-Chain-Risk-Intelligence-SCRI-" 
"# Smart-Supply-Chain-Risk-Intelligence-SCRI-" 
