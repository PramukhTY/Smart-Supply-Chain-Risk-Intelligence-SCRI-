CREATE DATABASE IF NOT EXISTS smart_supply_chain;
USE smart_supply_chain;

DROP TABLE IF EXISTS alerts;
DROP TABLE IF EXISTS audit_logs;
DROP TABLE IF EXISTS shipment_events;
DROP TABLE IF EXISTS shipments;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS supplier_metrics;
DROP TABLE IF EXISTS warehouses;
DROP TABLE IF EXISTS suppliers;

CREATE TABLE suppliers (
  supplier_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  contact_email VARCHAR(128),
  phone VARCHAR(32),
  rating DECIMAL(3,2) DEFAULT 0
);

CREATE TABLE warehouses (
  warehouse_id INT AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(128) NOT NULL,
  location VARCHAR(128) NOT NULL
);

CREATE TABLE products (
  product_id INT AUTO_INCREMENT PRIMARY KEY,
  supplier_id INT NOT NULL,
  name VARCHAR(128) NOT NULL,
  sku VARCHAR(64) UNIQUE NOT NULL,
  category VARCHAR(64),
  unit_cost DECIMAL(10,2) DEFAULT 0,
  lead_time_days INT DEFAULT 0,
  CONSTRAINT fk_products_suppliers FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

CREATE TABLE inventory (
  inventory_id INT AUTO_INCREMENT PRIMARY KEY,
  product_id INT NOT NULL,
  warehouse_id INT NOT NULL,
  quantity INT NOT NULL,
  reorder_threshold INT NOT NULL,
  safety_stock INT NOT NULL,
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_inventory_products FOREIGN KEY (product_id) REFERENCES products(product_id),
  CONSTRAINT fk_inventory_warehouses FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id),
  UNIQUE KEY uq_inventory_product_warehouse (product_id, warehouse_id)
);

CREATE TABLE shipments (
  shipment_id INT AUTO_INCREMENT PRIMARY KEY,
  supplier_id INT NOT NULL,
  product_id INT NOT NULL,
  warehouse_id INT NOT NULL,
  quantity INT NOT NULL,
  ship_date DATE NOT NULL,
  expected_arrival_date DATE NOT NULL,
  actual_arrival_date DATE,
  status ENUM('CREATED','IN_TRANSIT','DELIVERED','DELAYED','CANCELLED') DEFAULT 'CREATED',
  CONSTRAINT fk_shipments_suppliers FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
  CONSTRAINT fk_shipments_products FOREIGN KEY (product_id) REFERENCES products(product_id),
  CONSTRAINT fk_shipments_warehouses FOREIGN KEY (warehouse_id) REFERENCES warehouses(warehouse_id)
);

CREATE TABLE shipment_events (
  event_id INT AUTO_INCREMENT PRIMARY KEY,
  shipment_id INT NOT NULL,
  event_time DATETIME NOT NULL,
  event_type VARCHAR(64) NOT NULL,
  details VARCHAR(256),
  CONSTRAINT fk_shipment_events_shipments FOREIGN KEY (shipment_id) REFERENCES shipments(shipment_id)
);

CREATE TABLE supplier_metrics (
  metrics_id INT AUTO_INCREMENT PRIMARY KEY,
  supplier_id INT NOT NULL,
  record_date DATE NOT NULL,
  on_time_rate DECIMAL(6,4) DEFAULT 1.0000,
  avg_delay_days DECIMAL(10,2) DEFAULT 0,
  defect_rate DECIMAL(6,4) DEFAULT 0,
  risk_score DECIMAL(10,2) DEFAULT 0,
  risk_level VARCHAR(16) DEFAULT 'LOW',
  notes VARCHAR(256),
  CONSTRAINT fk_supplier_metrics_suppliers FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id),
  UNIQUE KEY uq_supplier_metrics_supplier_date (supplier_id, record_date)
);

CREATE TABLE alerts (
  alert_id INT AUTO_INCREMENT PRIMARY KEY,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  alert_type ENUM('SHIPMENT_DELAY','LOW_INVENTORY','RESTOCK_NEEDED','CUSTOM') NOT NULL,
  severity ENUM('INFO','WARN','CRITICAL') NOT NULL,
  entity_type ENUM('SHIPMENT','INVENTORY','SUPPLIER','SYSTEM') NOT NULL,
  entity_id INT NOT NULL,
  message VARCHAR(256) NOT NULL,
  resolved TINYINT(1) DEFAULT 0,
  resolved_at DATETIME NULL
);

CREATE TABLE audit_logs (
  audit_id INT AUTO_INCREMENT PRIMARY KEY,
  occurred_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  action VARCHAR(64) NOT NULL,
  entity_type VARCHAR(32) NOT NULL,
  entity_id INT NOT NULL,
  details VARCHAR(256)
);

INSERT INTO suppliers(name, contact_email, phone, rating) VALUES
('Alpha Manufacturing','alpha@example.com','+1-202-555-0101',4.5),
('Beta Logistics','beta@example.com','+1-202-555-0102',3.9),
('Gamma Components','gamma@example.com','+1-202-555-0103',4.2);

INSERT INTO warehouses(name, location) VALUES
('North Hub','Chicago, IL'),
('South Hub','Dallas, TX');

INSERT INTO products(supplier_id,name,sku,category,unit_cost,lead_time_days) VALUES
(1,'Widget A','W-A-001','Widgets',12.50,7),
(1,'Widget B','W-B-002','Widgets',9.75,5),
(3,'Gizmo C','G-C-003','Gizmos',22.10,10);

INSERT INTO inventory(product_id, warehouse_id, quantity, reorder_threshold, safety_stock) VALUES
(1,1,120,60,40),
(1,2,35,60,40),
(2,1,200,100,60),
(2,2,95,100,60),
(3,1,30,50,40),
(3,2,80,50,40);

INSERT INTO shipments(supplier_id, product_id, warehouse_id, quantity, ship_date, expected_arrival_date, actual_arrival_date, status) VALUES
(1,1,1,100, DATE_SUB(CURDATE(), INTERVAL 20 DAY), DATE_SUB(CURDATE(), INTERVAL 12 DAY), DATE_SUB(CURDATE(), INTERVAL 11 DAY), 'DELIVERED'),
(1,2,2,120, DATE_SUB(CURDATE(), INTERVAL 14 DAY), DATE_SUB(CURDATE(), INTERVAL 5 DAY), NULL, 'IN_TRANSIT'),
(3,3,1,80, DATE_SUB(CURDATE(), INTERVAL 18 DAY), DATE_SUB(CURDATE(), INTERVAL 8 DAY), NULL, 'DELAYED'),
(2,2,1,150, DATE_SUB(CURDATE(), INTERVAL 10 DAY), DATE_SUB(CURDATE(), INTERVAL 2 DAY), DATE_SUB(CURDATE(), INTERVAL 1 DAY), 'DELIVERED');

INSERT INTO shipment_events(shipment_id, event_time, event_type, details) VALUES
(1, DATE_SUB(NOW(), INTERVAL 19 DAY), 'CREATED', 'created'),
(1, DATE_SUB(NOW(), INTERVAL 12 DAY), 'ARRIVED', 'arrived'),
(2, DATE_SUB(NOW(), INTERVAL 13 DAY), 'CREATED', 'created'),
(2, DATE_SUB(NOW(), INTERVAL 2 DAY), 'DELAY_RISK', 'weather'),
(3, DATE_SUB(NOW(), INTERVAL 17 DAY), 'CREATED', 'created'),
(3, DATE_SUB(NOW(), INTERVAL 7 DAY), 'DELAYED', 'carrier capacity'),
(4, DATE_SUB(NOW(), INTERVAL 9 DAY), 'CREATED', 'created'),
(4, DATE_SUB(NOW(), INTERVAL 1 DAY), 'ARRIVED', 'arrived');

INSERT INTO supplier_metrics(supplier_id, record_date, on_time_rate, avg_delay_days, defect_rate, risk_score, risk_level, notes) VALUES
(1, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 0.95, 0.5, 0.015, 20.0, 'LOW', 'baseline'),
(2, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 0.80, 1.2, 0.020, 35.0, 'MEDIUM', 'baseline'),
(3, DATE_SUB(CURDATE(), INTERVAL 1 DAY), 0.70, 2.5, 0.030, 55.0, 'MEDIUM', 'baseline');

DELIMITER //
CREATE TRIGGER tr_shipment_delay_alert AFTER UPDATE ON shipments FOR EACH ROW
BEGIN
  IF NEW.status = 'DELAYED' AND OLD.status <> 'DELAYED' THEN
    INSERT INTO alerts(created_at, alert_type, severity, entity_type, entity_id, message, resolved)
    VALUES (NOW(), 'SHIPMENT_DELAY', 'WARN', 'SHIPMENT', NEW.shipment_id, CONCAT('Shipment ', NEW.shipment_id, ' delayed'), 0);
  END IF;
  IF NEW.expected_arrival_date < CURDATE() AND NEW.status <> 'DELIVERED' THEN
    INSERT INTO alerts(created_at, alert_type, severity, entity_type, entity_id, message, resolved)
    VALUES (NOW(), 'SHIPMENT_DELAY', 'WARN', 'SHIPMENT', NEW.shipment_id, CONCAT('Shipment ', NEW.shipment_id, ' behind schedule'), 0);
  END IF;
END//
DELIMITER ;

DELIMITER //
CREATE TRIGGER tr_inventory_threshold AFTER UPDATE ON inventory FOR EACH ROW
BEGIN
  IF NEW.quantity < NEW.reorder_threshold THEN
    INSERT INTO alerts(created_at, alert_type, severity, entity_type, entity_id, message, resolved)
    VALUES (NOW(), 'LOW_INVENTORY', IF(NEW.quantity < NEW.safety_stock, 'CRITICAL', 'WARN'), 'INVENTORY', NEW.inventory_id, CONCAT('Inventory low for product ', NEW.product_id, ' at warehouse ', NEW.warehouse_id), 0);
  END IF;
END//
DELIMITER ;

DELIMITER //
CREATE PROCEDURE compute_supplier_risk(IN p_supplier_id INT)
BEGIN
  DECLARE v_total_delivered INT DEFAULT 0;
  DECLARE v_delayed INT DEFAULT 0;
  DECLARE v_on_time_rate DECIMAL(6,4) DEFAULT 1.0000;
  DECLARE v_avg_delay DECIMAL(10,2) DEFAULT 0;
  DECLARE v_defect_rate DECIMAL(6,4) DEFAULT 0.0000;
  DECLARE v_score DECIMAL(10,2) DEFAULT 0.00;
  DECLARE v_level VARCHAR(16) DEFAULT 'LOW';

  SELECT COUNT(*) INTO v_total_delivered
  FROM shipments
  WHERE supplier_id = p_supplier_id
    AND ship_date >= CURDATE() - INTERVAL 90 DAY
    AND status IN ('DELIVERED','DELAYED');

  SELECT COUNT(*) INTO v_delayed
  FROM shipments
  WHERE supplier_id = p_supplier_id
    AND ship_date >= CURDATE() - INTERVAL 90 DAY
    AND (status = 'DELAYED' OR (actual_arrival_date IS NOT NULL AND actual_arrival_date > expected_arrival_date));

  IF v_total_delivered > 0 THEN
    SET v_on_time_rate = (v_total_delivered - v_delayed) / v_total_delivered;
  ELSE
    SET v_on_time_rate = 1.0000;
  END IF;

  SELECT AVG(GREATEST(DATEDIFF(COALESCE(actual_arrival_date, CURDATE()), expected_arrival_date),0)) INTO v_avg_delay
  FROM shipments
  WHERE supplier_id = p_supplier_id
    AND ship_date >= CURDATE() - INTERVAL 90 DAY
    AND status IN ('DELIVERED','DELAYED');

  SELECT defect_rate INTO v_defect_rate
  FROM supplier_metrics
  WHERE supplier_id = p_supplier_id
  ORDER BY record_date DESC
  LIMIT 1;

  IF v_defect_rate IS NULL THEN
    SET v_defect_rate = 0.0200;
  END IF;

  SET v_score = LEAST(100, GREATEST(0, 50*(1 - v_on_time_rate) + 30*(v_avg_delay/10) + 20*(v_defect_rate)));

  IF v_score < 30 THEN
    SET v_level = 'LOW';
  ELSEIF v_score < 60 THEN
    SET v_level = 'MEDIUM';
  ELSE
    SET v_level = 'HIGH';
  END IF;

  INSERT INTO supplier_metrics(supplier_id, record_date, on_time_rate, avg_delay_days, defect_rate, risk_score, risk_level, notes)
  VALUES(p_supplier_id, CURDATE(), v_on_time_rate, v_avg_delay, v_defect_rate, v_score, v_level, 'auto')
  ON DUPLICATE KEY UPDATE on_time_rate=VALUES(on_time_rate), avg_delay_days=VALUES(avg_delay_days), defect_rate=VALUES(defect_rate), risk_score=VALUES(risk_score), risk_level=VALUES(risk_level), notes=VALUES(notes);

  INSERT INTO audit_logs(occurred_at, action, entity_type, entity_id, details)
  VALUES (NOW(), 'COMPUTE_SUPPLIER_RISK', 'SUPPLIER', p_supplier_id, CONCAT('score=', v_score, ', level=', v_level));
END//
DELIMITER ;

DELIMITER //
CREATE PROCEDURE daily_update_supplier_risks()
BEGIN
  DECLARE done INT DEFAULT 0;
  DECLARE s_id INT;
  DECLARE cur CURSOR FOR SELECT supplier_id FROM suppliers;
  DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = 1;

  OPEN cur;
  read_loop: LOOP
    FETCH cur INTO s_id;
    IF done = 1 THEN LEAVE read_loop; END IF;
    CALL compute_supplier_risk(s_id);
  END LOOP;
  CLOSE cur;

  INSERT INTO audit_logs(occurred_at, action, entity_type, entity_id, details)
  VALUES (NOW(), 'DAILY_RISK_UPDATE', 'SYSTEM', 0, 'completed');
END//
DELIMITER ;

CREATE OR REPLACE VIEW supplier_risk_summary AS
SELECT s.supplier_id, s.name, m.record_date, m.risk_score, m.risk_level, m.on_time_rate, m.avg_delay_days, m.defect_rate
FROM suppliers s
LEFT JOIN supplier_metrics m
  ON m.supplier_id = s.supplier_id
 AND m.record_date = (
   SELECT MAX(m2.record_date) FROM supplier_metrics m2 WHERE m2.supplier_id = s.supplier_id
 );

CREATE OR REPLACE VIEW delayed_shipments_overview AS
SELECT sh.shipment_id, sh.supplier_id, sh.product_id, sh.warehouse_id, sh.expected_arrival_date, sh.actual_arrival_date, sh.status,
       GREATEST(DATEDIFF(COALESCE(sh.actual_arrival_date, CURDATE()), sh.expected_arrival_date),0) AS delay_days
FROM shipments sh
WHERE sh.status='DELAYED' OR (sh.expected_arrival_date < CURDATE() AND sh.status <> 'DELIVERED');

CREATE OR REPLACE VIEW inventory_health AS
SELECT i.inventory_id, p.name AS product_name, w.name AS warehouse_name, i.quantity, i.reorder_threshold, i.safety_stock,
       CASE WHEN i.quantity < i.safety_stock THEN 'CRITICAL'
            WHEN i.quantity < i.reorder_threshold THEN 'LOW'
            ELSE 'OK' END AS status
FROM inventory i
JOIN products p ON p.product_id = i.product_id
JOIN warehouses w ON w.warehouse_id = i.warehouse_id;