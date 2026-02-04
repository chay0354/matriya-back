/**
 * Database setup for user management - Supabase PostgreSQL only
 */
import { Sequelize, DataTypes } from 'sequelize';
import settings from './config.js';
import logger from './logger.js';

// Get database URL - Supabase only
function getDatabaseUrl() {
  // ALWAYS prefer pooler connection for serverless (Vercel)
  // Check for POSTGRES_URL (pooler) first - this is the pooler connection
  const poolerUrl = process.env.POSTGRES_URL || process.env.POSTGRES_PRISMA_URL;
  if (poolerUrl) {
    // Use pooler connection (supports IPv4, better for serverless)
    if (process.env.VERCEL) {
      logger.info("Using Supabase pooler connection (serverless-optimized)");
    } else {
      logger.info("Using Supabase pooler connection");
    }
    return poolerUrl;
  }
  
  // On Vercel, REQUIRE pooler connection - direct connections will fail
  if (process.env.VERCEL) {
    const errorMsg = "POSTGRES_URL (pooler connection) is REQUIRED on Vercel. Direct connections (SUPABASE_DB_URL) will fail. Set POSTGRES_URL in Vercel environment variables with format: postgresql://postgres:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres?sslmode=require&pgbouncer=true";
    logger.error(errorMsg);
    throw new Error(errorMsg);
  }
  
  // Fallback to SUPABASE_DB_URL if POSTGRES_URL not set (only for non-Vercel)
  if (!settings.SUPABASE_DB_URL) {
    const errorMsg = "POSTGRES_URL or SUPABASE_DB_URL must be set.";
    logger.error(errorMsg);
    throw new Error(errorMsg);
  }
  
  return settings.SUPABASE_DB_URL;
}

// Create Sequelize instance
let sequelize;
let DATABASE_URL;

try {
  DATABASE_URL = getDatabaseUrl();
  
  // Clean connection string - remove all SSL-related parameters (we'll handle SSL in dialectOptions)
  let dbUrl = DATABASE_URL;
  // Remove sslmode and ssl parameters from URL if they exist
  dbUrl = dbUrl.replace(/[?&](sslmode|ssl)=[^&]*/gi, '');
  // Clean up any double separators
  dbUrl = dbUrl.replace(/\?&/, '?').replace(/&&/, '&');
  // Remove trailing ? or & if present
  dbUrl = dbUrl.replace(/[?&]$/, '');
  
  // For serverless (Vercel), use smaller pool and faster timeouts
  const poolConfig = process.env.VERCEL ? {
    max: 1,
    min: 0,
    idle: 10000,
    acquire: 5000,
    evict: 1000
  } : {
    max: 5,
    min: 0,
    idle: 10000,
    acquire: 10000,
    evict: 60000
  };
  
  sequelize = new Sequelize(dbUrl, {
    dialect: 'postgres',
    logging: false,
    dialectOptions: {
      ssl: {
        require: true,
        rejectUnauthorized: false  // Allow self-signed certificates for Supabase
      },
      connectTimeout: process.env.VERCEL ? 5000 : 10000
    },
    pool: poolConfig
  });
  
  if (process.env.VERCEL) {
    logger.info("Using Supabase PostgreSQL database (serverless-optimized)");
  } else {
    logger.info("Using Supabase PostgreSQL database");
  }
} catch (e) {
  logger.error(`Failed to get database URL: ${e.message}`);
  // On Vercel, we can continue without DB connection for now
  // It will be retried when actually needed
  if (process.env.VERCEL) {
    DATABASE_URL = null;
    sequelize = null;
    logger.warn("Database URL not available on Vercel startup, will retry on first use");
  } else {
    throw e;
  }
}

// Define User model
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
    logger.warn("Database engine not available, skipping initialization");
    return;
  }
  
  try {
    await sequelize.authenticate();
    await sequelize.sync({ alter: false }); // Use sync for simplicity, alter: false to avoid modifying existing tables
    logger.info("Database tables initialized successfully");
  } catch (e) {
    logger.error(`Error initializing database: ${e.message}`);
    // On Vercel, don't fail if database connection isn't ready yet
    // Tables will be created on first use
    if (process.env.VERCEL) {
      logger.warn("Database initialization failed on Vercel, will retry on first use");
    } else {
      throw e;
    }
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
