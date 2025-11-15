// Smart Supply Chain Risk Intelligence - Frontend JavaScript

const API_BASE = '';

// Load dashboard metrics on home page
document.addEventListener('DOMContentLoaded', function() {
  const page = document.body.getAttribute('data-page');
  
  if (page === 'home') {
    loadDashboardMetrics();
    setInterval(loadDashboardMetrics, 30000); // Refresh every 30 seconds
  } else if (page === 'suppliers') {
    loadSuppliers();
  } else if (page === 'analytics') {
    loadShipments();
    loadSupplierRisk();
    loadDelayedShipments();
    // Don't load form options on page load, only when form is opened
  } else if (page === 'alerts') {
    loadAlerts(false);
  }
});

// ==================== DASHBOARD ====================

async function loadDashboardMetrics() {
  try {
    const response = await fetch(`${API_BASE}/api/dashboard/metrics`);
    const result = await response.json();
    
    if (result.success) {
      const data = result.data;
      document.getElementById('metricSuppliers').textContent = data.suppliers || 0;
      document.getElementById('metricTransit').textContent = data.transit || 0;
      document.getElementById('metricAlerts').textContent = data.alerts || 0;
      document.getElementById('metricInventory').textContent = data.inventory || 'OK';
    }
  } catch (error) {
    console.error('Error loading metrics:', error);
  }
}

// ==================== SUPPLIERS ====================

async function loadSuppliers() {
  try {
    console.log('Loading suppliers...');
    const tbody = document.getElementById('suppliersTable');
    if (!tbody) {
      console.error('Suppliers table body not found!');
      return;
    }
    
    tbody.innerHTML = '<tr><td colspan="8">Loading suppliers...</td></tr>';
    
    const response = await fetch(`${API_BASE}/api/suppliers`);
    console.log('Suppliers response status:', response.status);
    console.log('Suppliers response headers:', response.headers);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Response error text:', errorText);
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }
    
    const result = await response.json();
    console.log('Suppliers API result:', result);
    console.log('Suppliers data type:', typeof result.data);
    console.log('Suppliers data:', result.data);
    
    if (result.success) {
      if (!result.data) {
        console.warn('Result data is null or undefined');
        tbody.innerHTML = '<tr><td colspan="8">No data returned from server</td></tr>';
        return;
      }
      
      if (result.data.length === 0) {
        console.log('No suppliers found in database');
        tbody.innerHTML = '<tr><td colspan="8">No suppliers found. Add a new supplier to get started.</td></tr>';
        return;
      }
      
      console.log(`Displaying ${result.data.length} suppliers`);
      tbody.innerHTML = result.data.map(supplier => {
        // Convert risk_score to number if it's a string or Decimal
        const riskScore = parseFloat(supplier.risk_score) || 0;
        const riskLevel = (supplier.risk_level || 'LOW').toUpperCase();
        
        return `
        <tr>
          <td>${supplier.supplier_id}</td>
          <td>${supplier.name || '-'}</td>
          <td>${supplier.contact_email || '-'}</td>
          <td>${supplier.phone || '-'}</td>
          <td>${supplier.rating || 0}</td>
          <td>${riskScore.toFixed(1)}</td>
          <td><span class="status ${riskLevel}">${riskLevel}</span></td>
          <td>
            <button class="btn" onclick="computeRisk(${supplier.supplier_id})">Compute Risk</button>
          </td>
        </tr>
      `;
      }).join('');
    } else {
      console.error('API returned success=false:', result.error);
      tbody.innerHTML = `<tr><td colspan="8">Error: ${result.error || 'Failed to load suppliers'}</td></tr>`;
    }
  } catch (error) {
    console.error('Error loading suppliers:', error);
    console.error('Error stack:', error.stack);
    const tbody = document.getElementById('suppliersTable');
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="8">Error loading suppliers: ${error.message}. Check browser console (F12) for details.</td></tr>`;
    }
  }
}

function showAddSupplierForm() {
  document.getElementById('addSupplierForm').style.display = 'block';
}

function closeAddSupplierForm() {
  document.getElementById('addSupplierForm').style.display = 'none';
  document.getElementById('supplierForm').reset();
}

async function addSupplier(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const data = {
    name: formData.get('name'),
    contact_email: formData.get('contact_email'),
    phone: formData.get('phone'),
    rating: parseFloat(formData.get('rating')) || 0
  };
  
  try {
    const response = await fetch(`${API_BASE}/api/suppliers`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    if (result.success) {
      alert('Supplier added successfully!');
      closeAddSupplierForm();
      loadSuppliers();
    } else {
      alert('Error: ' + result.error);
    }
  } catch (error) {
    console.error('Error adding supplier:', error);
    alert('Error adding supplier');
  }
}

async function computeRisk(supplierId) {
  try {
    const response = await fetch(`${API_BASE}/api/suppliers/${supplierId}/compute-risk`, {
      method: 'POST'
    });
    
    const result = await response.json();
    if (result.success) {
      alert('Risk score computed successfully!');
      loadSuppliers();
    } else {
      alert('Error: ' + result.error);
    }
  } catch (error) {
    console.error('Error computing risk:', error);
    alert('Error computing risk');
  }
}

// ==================== SHIPMENTS ====================

async function loadShipments() {
  try {
    console.log('Loading shipments...');
    const tbody = document.getElementById('shipmentsTable');
    if (!tbody) {
      console.error('Shipments table body not found!');
      return;
    }
    
    tbody.innerHTML = '<tr><td colspan="10">Loading shipments...</td></tr>';
    
    const response = await fetch(`${API_BASE}/api/shipments`);
    console.log('Shipments response status:', response.status);
    console.log('Shipments response headers:', response.headers);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Response error text:', errorText);
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }
    
    const result = await response.json();
    console.log('Shipments API result:', result);
    console.log('Shipments data type:', typeof result.data);
    console.log('Shipments data:', result.data);
    
    if (result.success) {
      if (!result.data) {
        console.warn('Result data is null or undefined');
        tbody.innerHTML = '<tr><td colspan="10">No data returned from server</td></tr>';
        return;
      }
      
      if (result.data.length === 0) {
        console.log('No shipments found in database');
        tbody.innerHTML = '<tr><td colspan="10">No shipments found. Add a new shipment to get started.</td></tr>';
        return;
      }
      
      console.log(`Displaying ${result.data.length} shipments`);
      tbody.innerHTML = result.data.map(shipment => {
        // Convert delay_days to number if it's a string or Decimal
        const delayDays = parseFloat(shipment.delay_days) || 0;
        const status = (shipment.status || 'CREATED').replace('_', '');
        
        return `
        <tr>
          <td>${shipment.shipment_id || '-'}</td>
          <td>${shipment.supplier_name || '-'}</td>
          <td>${shipment.product_name || '-'}</td>
          <td>${shipment.warehouse_name || '-'}</td>
          <td>${shipment.quantity || 0}</td>
          <td>${shipment.ship_date || '-'}</td>
          <td>${shipment.expected_arrival_date || '-'}</td>
          <td>${shipment.actual_arrival_date || '-'}</td>
          <td><span class="status ${status}">${shipment.status || 'CREATED'}</span></td>
          <td>${delayDays}</td>
        </tr>
      `;
      }).join('');
    } else {
      console.error('API returned success=false:', result.error);
      tbody.innerHTML = `<tr><td colspan="10">Error: ${result.error || 'Failed to load shipments'}</td></tr>`;
    }
  } catch (error) {
    console.error('Error loading shipments:', error);
    console.error('Error stack:', error.stack);
    const tbody = document.getElementById('shipmentsTable');
    if (tbody) {
      tbody.innerHTML = `<tr><td colspan="10">Error loading shipments: ${error.message}. Check browser console (F12) for details.</td></tr>`;
    }
  }
}

async function loadFormOptions() {
  // Load suppliers
  try {
    const suppliersRes = await fetch(`${API_BASE}/api/suppliers`);
    const suppliersData = await suppliersRes.json();
    if (suppliersData.success) {
      const select = document.getElementById('supplierSelect');
      if (select) {
        if (suppliersData.data && suppliersData.data.length > 0) {
          select.innerHTML = '<option value="">Select Supplier</option>' +
            suppliersData.data.map(s => `<option value="${s.supplier_id}">${s.name}</option>`).join('');
        } else {
          select.innerHTML = '<option value="">No suppliers available</option>';
        }
      }
    } else {
      console.error('Failed to load suppliers:', suppliersData.error);
    }
  } catch (error) {
    console.error('Error loading suppliers:', error);
    const select = document.getElementById('supplierSelect');
    if (select) {
      select.innerHTML = '<option value="">Error loading suppliers</option>';
    }
  }
  
  // Load products
  try {
    const productsRes = await fetch(`${API_BASE}/api/products`);
    const productsData = await productsRes.json();
    if (productsData.success) {
      const select = document.getElementById('productSelect');
      if (select) {
        if (productsData.data && productsData.data.length > 0) {
          select.innerHTML = '<option value="">Select Product</option>' +
            productsData.data.map(p => `<option value="${p.product_id}">${p.name} (${p.sku})</option>`).join('');
        } else {
          select.innerHTML = '<option value="">No products available</option>';
        }
      }
    } else {
      console.error('Failed to load products:', productsData.error);
    }
  } catch (error) {
    console.error('Error loading products:', error);
    const select = document.getElementById('productSelect');
    if (select) {
      select.innerHTML = '<option value="">Error loading products</option>';
    }
  }
  
  // Load warehouses
  try {
    console.log('Loading warehouses...');
    const warehousesRes = await fetch(`${API_BASE}/api/warehouses`);
    console.log('Warehouses response status:', warehousesRes.status);
    const warehousesData = await warehousesRes.json();
    console.log('Warehouses data:', warehousesData);
    
    if (warehousesData.success) {
      const select = document.getElementById('warehouseSelect');
      if (select) {
        if (warehousesData.data && warehousesData.data.length > 0) {
          select.innerHTML = '<option value="">Select Warehouse</option>' +
            warehousesData.data.map(w => `<option value="${w.warehouse_id}">${w.name} - ${w.location}</option>`).join('');
          console.log('Warehouses loaded successfully:', warehousesData.data.length);
        } else {
          select.innerHTML = '<option value="">No warehouses available. Please add warehouses first.</option>';
          console.warn('No warehouses found in database');
        }
      } else {
        console.error('Warehouse select element not found!');
      }
    } else {
      console.error('Failed to load warehouses:', warehousesData.error);
      const select = document.getElementById('warehouseSelect');
      if (select) {
        select.innerHTML = '<option value="">Error loading warehouses</option>';
      }
    }
  } catch (error) {
    console.error('Error loading warehouses:', error);
    const select = document.getElementById('warehouseSelect');
    if (select) {
      select.innerHTML = '<option value="">Error loading warehouses</option>';
    }
  }
}

async function showAddShipmentForm() {
  document.getElementById('addShipmentForm').style.display = 'block';
  await loadFormOptions();
}

function closeAddShipmentForm() {
  document.getElementById('addShipmentForm').style.display = 'none';
  document.getElementById('shipmentForm').reset();
}

async function addShipment(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const data = {
    supplier_id: parseInt(formData.get('supplier_id')),
    product_id: parseInt(formData.get('product_id')),
    warehouse_id: parseInt(formData.get('warehouse_id')),
    quantity: parseInt(formData.get('quantity')),
    ship_date: formData.get('ship_date'),
    expected_arrival_date: formData.get('expected_arrival_date'),
    status: formData.get('status')
  };
  
  try {
    const response = await fetch(`${API_BASE}/api/shipments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    if (result.success) {
      alert('Shipment added successfully!');
      closeAddShipmentForm();
      loadShipments();
    } else {
      alert('Error: ' + result.error);
    }
  } catch (error) {
    console.error('Error adding shipment:', error);
    alert('Error adding shipment');
  }
}

async function loadSupplierRisk() {
  try {
    console.log('Loading supplier risk...');
    const container = document.getElementById('riskChart');
    if (!container) {
      console.error('Risk chart container not found!');
      return;
    }
    
    container.innerHTML = '<p>Loading supplier risk data...</p>';
    
    const response = await fetch(`${API_BASE}/api/dashboard/supplier-risk`);
    console.log('Supplier risk response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Response error text:', errorText);
      throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
    }
    
    const result = await response.json();
    console.log('Supplier risk API result:', result);
    console.log('Supplier risk data type:', typeof result.data);
    console.log('Supplier risk data:', result.data);
    
    if (result.success) {
      if (result.data && result.data.length > 0) {
        console.log(`Displaying ${result.data.length} supplier risk records`);
        container.innerHTML = '<h4>Supplier Risk Summary</h4>' +
          result.data.map(s => {
            // Convert all numeric values to numbers
            const riskScore = parseFloat(s.risk_score) || 0;
            const onTimeRate = parseFloat(s.on_time_rate) || 0;
            const avgDelay = parseFloat(s.avg_delay_days) || 0;
            const riskLevel = (s.risk_level || 'LOW').toUpperCase();
            
            return `
            <div style="margin: 0.75rem 0; padding: 0.5rem; background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%); border-radius: 8px; border-left: 4px solid #667eea;">
              <strong style="color: #764ba2;">${s.name || 'Unknown'}:</strong> 
              <span class="status ${riskLevel}" style="float: right;">
                Score: ${riskScore.toFixed(1)} (${riskLevel})
              </span>
              <div style="font-size: 0.85rem; color: #666; margin-top: 0.25rem;">
                On-time Rate: ${(onTimeRate * 100).toFixed(1)}% | 
                Avg Delay: ${avgDelay.toFixed(1)} days
              </div>
            </div>
          `;
          }).join('');
      } else {
        console.log('No supplier risk data available');
        container.innerHTML = '<p>No supplier risk data available. Compute risk scores for suppliers to see data here.</p>';
      }
    } else {
      console.error('API returned success=false:', result.error);
      container.innerHTML = `<p>Error loading supplier risk: ${result.error || 'Unknown error'}</p>`;
    }
  } catch (error) {
    console.error('Error loading supplier risk:', error);
    console.error('Error stack:', error.stack);
    const container = document.getElementById('riskChart');
    if (container) {
      container.innerHTML = `<p>Error loading supplier risk data: ${error.message}. Check browser console (F12) for details.</p>`;
    }
  }
}

async function loadDelayedShipments() {
  try {
    console.log('Loading delayed shipments...');
    const response = await fetch(`${API_BASE}/api/dashboard/delayed-shipments`);
    console.log('Delayed shipments response status:', response.status);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('Delayed shipments data:', result);
    
    const container = document.getElementById('delayChart');
    if (!container) {
      console.error('Delay chart container not found!');
      return;
    }
    
    if (result.success) {
      if (result.data && result.data.length > 0) {
        container.innerHTML = '<h4>Delayed Shipments Overview</h4>' +
          result.data.map(s => {
            // Convert delay_days to number if it's a string or Decimal
            const delayDays = parseFloat(s.delay_days) || 0;
            const status = (s.status || 'DELAYED').replace('_', '');
            
            return `
            <div style="margin: 0.75rem 0; padding: 0.75rem; background: linear-gradient(135deg, rgba(245, 87, 108, 0.1) 0%, rgba(240, 147, 251, 0.1) 100%); border-left: 4px solid #f5576c; border-radius: 8px;">
              <strong style="color: #764ba2;">Shipment #${s.shipment_id || 'N/A'}</strong>
              <div style="margin-top: 0.5rem;">
                <div>Status: <span class="status ${status}">${s.status || 'DELAYED'}</span></div>
                <div>Delay: <strong style="color: #f5576c;">${delayDays} days</strong></div>
                <div style="font-size: 0.85rem; color: #666; margin-top: 0.25rem;">
                  Expected: ${s.expected_arrival_date || 'N/A'} | 
                  Actual: ${s.actual_arrival_date || 'Not arrived'}
                </div>
              </div>
            </div>
          `;
          }).join('');
      } else {
        container.innerHTML = '<p style="color: #667eea; font-weight: 600;">✓ No delayed shipments. All shipments are on time!</p>';
      }
    } else {
      container.innerHTML = `<p>Error loading delayed shipments: ${result.error || 'Unknown error'}</p>`;
    }
  } catch (error) {
    console.error('Error loading delayed shipments:', error);
    const container = document.getElementById('delayChart');
    if (container) {
      container.innerHTML = '<p>Error loading delayed shipments data. Please check console for details.</p>';
    }
  }
}

// Warehouse management functions
function showAddWarehouseForm() {
  document.getElementById('addWarehouseForm').style.display = 'block';
}

function closeAddWarehouseForm() {
  document.getElementById('addWarehouseForm').style.display = 'none';
  document.getElementById('warehouseForm').reset();
}

async function addWarehouse(event) {
  event.preventDefault();
  const formData = new FormData(event.target);
  const data = {
    name: formData.get('name'),
    location: formData.get('location')
  };
  
  try {
    const response = await fetch(`${API_BASE}/api/warehouses`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    const result = await response.json();
    if (result.success) {
      alert('Warehouse added successfully!');
      closeAddWarehouseForm();
      // Reload form options to include the new warehouse
      await loadFormOptions();
    } else {
      alert('Error: ' + result.error);
    }
  } catch (error) {
    console.error('Error adding warehouse:', error);
    alert('Error adding warehouse');
  }
}

// ==================== ALERTS ====================

async function loadAlerts(resolved = false) {
  try {
    console.log('Loading alerts (resolved:', resolved, ')...');
    const response = await fetch(`${API_BASE}/api/alerts?resolved=${resolved}`);
    console.log('Alerts response status:', response.status);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const result = await response.json();
    console.log('Alerts data:', result);
    
    const tbody = document.getElementById('alertsTable');
    if (!tbody) {
      console.error('Alerts table body not found!');
      return;
    }
    
    if (result.success) {
      if (!result.data || result.data.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8">No ${resolved ? 'resolved' : 'open'} alerts found.</td></tr>`;
        return;
      }
      
      tbody.innerHTML = result.data.map(alert => `
        <tr>
          <td>${alert.alert_id || '-'}</td>
          <td>${alert.created_at ? new Date(alert.created_at).toLocaleString() : '-'}</td>
          <td>${alert.alert_type || '-'}</td>
          <td><span class="severity ${(alert.severity || 'INFO').toUpperCase()}">${alert.severity || 'INFO'}</span></td>
          <td>${alert.entity_type || '-'} #${alert.entity_id || '-'}</td>
          <td>${alert.message || '-'}</td>
          <td><span class="status ${alert.resolved ? 'DELIVERED' : 'INTRANSIT'}">${alert.resolved ? 'Resolved' : 'Open'}</span></td>
          <td>
            ${!alert.resolved ? 
              `<button class="btn" onclick="resolveAlert(${alert.alert_id})">Resolve</button>` : 
              alert.resolved_at ? `Resolved: ${new Date(alert.resolved_at).toLocaleDateString()}` : '-'
            }
          </td>
        </tr>
      `).join('');
    } else {
      tbody.innerHTML = `<tr><td colspan="8">Error: ${result.error || 'Failed to load alerts'}</td></tr>`;
    }
  } catch (error) {
    console.error('Error loading alerts:', error);
    const tbody = document.getElementById('alertsTable');
    if (tbody) {
      tbody.innerHTML = '<tr><td colspan="8">Error loading alerts. Please check console for details.</td></tr>';
    }
  }
}

async function resolveAlert(alertId) {
  try {
    const response = await fetch(`${API_BASE}/api/alerts/${alertId}/resolve`, {
      method: 'POST'
    });
    
    const result = await response.json();
    if (result.success) {
      alert('Alert resolved successfully!');
      loadAlerts(false);
    } else {
      alert('Error: ' + result.error);
    }
  } catch (error) {
    console.error('Error resolving alert:', error);
    alert('Error resolving alert');
  }
}

async function generateTestAlerts() {
  if (!confirm('This will create test alerts for demonstration. Continue?')) {
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE}/api/alerts/generate-test`, {
      method: 'POST'
    });
    
    const result = await response.json();
    if (result.success) {
      alert(`Success! Created ${result.alerts.length} test alerts:\n- ${result.alerts.join('\n- ')}`);
      loadAlerts(false);
    } else {
      alert('Error: ' + result.error);
    }
  } catch (error) {
    console.error('Error generating test alerts:', error);
    alert('Error generating test alerts');
  }
}

