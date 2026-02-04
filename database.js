/**
 * Database setup for user management - Supabase PostgreSQL only
 */
import { Sequelize, DataTypes } from 'sequelize';
import logger from './logger.js';

// Get database URL - Supabase only
function getDatabaseUrl() {
  // Prefer POSTGRES_URL (pooler connection, best for Vercel)
  // Fallback to SUPABASE_DB_URL (direct connection, OK for local)
  const dbUrl = process.env.POSTGRES_URL || process.env.POSTGRES_PRISMA_URL || process.env.SUPABASE_DB_URL;
  if (!dbUrl) {
    const errorMsg = "POSTGRES_URL or SUPABASE_DB_URL environment variable is required. Use POSTGRES_URL (pooler) for Vercel, SUPABASE_DB_URL (direct) for local.";
    logger.error(errorMsg);
    throw new Error(errorMsg);
  }
  if (dbUrl.includes('pooler.supabase.com')) {
    logger.info("Using Supabase PostgreSQL pooler connection");
  } else {
    logger.info("Using Supabase PostgreSQL direct connection");
  }
  return dbUrl;
}

// Create Sequelize instance
let sequelize;
let DATABASE_URL;

try {
  DATABASE_URL = getDatabaseUrl();
  
  // Clean connection string - remove SSL parameters (handled in dialectOptions)
  let dbUrl = DATABASE_URL.replace(/[?&](sslmode|ssl)=[^&]*/gi, '').replace(/\?&/, '?').replace(/&&/, '&').replace(/[?&]$/, '');
  
  // Pool configuration (optimized for serverless)
  const poolConfig = {
    max: process.env.VERCEL ? 1 : 5,
    min: 0,
    idle: 10000,
    acquire: process.env.VERCEL ? 5000 : 10000,
    evict: process.env.VERCEL ? 1000 : 60000
  };
  
  sequelize = new Sequelize(dbUrl, {
    dialect: 'postgres',
    logging: false,
    dialectOptions: {
      ssl: {
        require: true,
        rejectUnauthorized: false
      },
      connectTimeout: process.env.VERCEL ? 5000 : 10000
    },
    pool: poolConfig
  });
  
  logger.info("Supabase database connection configured");
} catch (e) {
  logger.error(`Database setup failed: ${e.message}`);
  DATABASE_URL = null;
  sequelize = null;
}

// Define User model - will be null if sequelize is null (connection failed)
const User = sequelize ? sequelize.define('User', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  username: {
    type: DataTypes.STRING,
    unique: true,
    allowNull: false
  },
  email: {
    type: DataTypes.STRING,
    unique: true,
    allowNull: false
  },
  hashed_password: {
    type: DataTypes.STRING,
    allowNull: false
  },
  full_name: {
    type: DataTypes.STRING,
    allowNull: true
  },
  is_active: {
    type: DataTypes.BOOLEAN,
    defaultValue: true
  },
  is_admin: {
    type: DataTypes.BOOLEAN,
    defaultValue: false
  },
  created_at: {
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW
  },
  last_login: {
    type: DataTypes.DATE,
    allowNull: true
  }
}, {
  tableName: 'users',
  timestamps: false
}) : null;

// Define FilePermission model
const FilePermission = sequelize ? sequelize.define('FilePermission', {
  id: {
    type: DataTypes.INTEGER,
    primaryKey: true,
    autoIncrement: true
  },
  user_id: {
    type: DataTypes.INTEGER,
    allowNull: false
  },
  filename: {
    type: DataTypes.STRING,
    allowNull: false
  },
  created_at: {
    type: DataTypes.DATE,
    defaultValue: DataTypes.NOW
  }
}, {
  tableName: 'file_permissions',
  timestamps: false
}) : null;

// Initialize database
async function initDb() {
  if (!sequelize) {
    const errorMsg = "Database connection not available. Check POSTGRES_URL environment variable.";
    logger.error(errorMsg);
    throw new Error(errorMsg);
  }
  
  try {
    await sequelize.authenticate();
    logger.info("Database connection authenticated");
    await sequelize.sync({ alter: false }); // Use sync for simplicity, alter: false to avoid modifying existing tables
    logger.info("Database tables initialized successfully");
  } catch (e) {
    logger.error(`Error initializing database: ${e.message}`);
    logger.error(`Stack: ${e.stack}`);
    throw e;
  }
}

// Get database connection (for direct queries if needed)
function getDb() {
  return sequelize;
}

export {
  User,
  FilePermission,
  sequelize,
  initDb,
  getDb,
  DATABASE_URL,
  getDatabaseUrl
};
