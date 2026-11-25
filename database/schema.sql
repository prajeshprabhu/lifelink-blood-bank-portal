CREATE TABLE IF NOT EXISTS admin_users (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  username VARCHAR(100) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_admin_username (username)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS blood_bank_profile (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  blood_bank_name VARCHAR(255) NOT NULL,
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(30) NOT NULL,
  address VARCHAR(255) NOT NULL,
  city VARCHAR(100) NOT NULL,
  state VARCHAR(100) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS inventory (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  blood_group VARCHAR(3) NOT NULL,
  component_type VARCHAR(50) NOT NULL,
  units_collected INT UNSIGNED NOT NULL,
  available_units INT UNSIGNED NOT NULL DEFAULT 0,
  reserved_units INT UNSIGNED NOT NULL DEFAULT 0,
  donor_name VARCHAR(255) NOT NULL,
  donor_phone VARCHAR(30) NOT NULL,
  city VARCHAR(100) NOT NULL,
  source VARCHAR(100) NOT NULL,
  donation_date DATE NOT NULL,
  collection_date DATE NOT NULL,
  expiry_date DATE NOT NULL,
  status VARCHAR(30) NOT NULL DEFAULT 'Available',
  remarks TEXT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_inventory_blood_group (blood_group),
  INDEX idx_inventory_city (city),
  INDEX idx_inventory_status (status),
  INDEX idx_inventory_expiry (expiry_date),
  INDEX idx_inventory_available (available_units),
  INDEX idx_inventory_component (component_type),
  CONSTRAINT chk_inventory_units CHECK (available_units <= units_collected),
  CONSTRAINT chk_inventory_nonnegative CHECK (
    units_collected >= 0 AND available_units >= 0 AND reserved_units >= 0
  )
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS inventory_history (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  inventory_id INT UNSIGNED NOT NULL,
  previous_units INT UNSIGNED NOT NULL,
  updated_units INT UNSIGNED NOT NULL,
  previous_status VARCHAR(30) NOT NULL,
  updated_status VARCHAR(30) NOT NULL,
  change_reason VARCHAR(255) NOT NULL,
  changed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_history_inventory (inventory_id),
  INDEX idx_history_changed_at (changed_at),
  CONSTRAINT fk_history_inventory FOREIGN KEY (inventory_id)
    REFERENCES inventory(id) ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS api_logs (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  endpoint VARCHAR(255) NOT NULL,
  request_method VARCHAR(10) NOT NULL,
  response_status INT NOT NULL,
  timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  INDEX idx_api_logs_timestamp (timestamp)
) ENGINE=InnoDB;
