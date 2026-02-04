/**
 * Express application for RAG system file ingestion
 */
import express from 'express';
import cors from 'cors';
import multer from 'multer';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';
import { existsSync, mkdirSync, unlinkSync } from 'fs';
import settings from './config.js';
import RAGService from './ragService.js';
import { initDb } from './database.js';
import { authRouter } from './authEndpoints.js';
import { adminRouter } from './adminEndpoints.js';
import { StateMachine, Kernel } from './stateMachine.js';
import logger from './logger.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Initialize Express app
const app = express();

// CORS configuration - Allow all origins
logger.info("CORS configured to allow all origins");
app.use(cors({
  origin: "*",
  methods: ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
  allowedHeaders: "*",
  exposedHeaders: "*",
  credentials: true,
  maxAge: 3600
}));

// Handle preflight requests explicitly
app.options('*', cors());

// Body parsing middleware with UTF-8 support
app.use(express.json({ charset: 'utf-8' }));
app.use(express.urlencoded({ extended: true, charset: 'utf-8' }));

// Set UTF-8 encoding for all responses
app.use((req, res, next) => {
  res.charset = 'utf-8';
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  next();
});

// Initialize database (non-blocking on Vercel)
// On Vercel, skip initialization at startup to avoid blocking
if (!process.env.VERCEL) {
  try {
    await initDb();
  } catch (e) {
    logger.error(`Database initialization failed: ${e.message}`);
    throw e;
  }
} else {
  // On Vercel, database will be initialized on first use (lazy initialization)
  logger.info("Skipping database initialization on Vercel - will initialize on first use");
}

// Register routers
app.use('/auth', authRouter);
app.use('/admin', adminRouter);

// Initialize RAG service (lazy initialization to avoid blocking startup)
let ragService = null;

function getRagService() {
  /**Get or initialize RAG service*/
  if (!ragService) {
    logger.info("Initializing RAG service...");
    ragService = new RAGService();
    logger.info("RAG service initialized");
  }
  return ragService;
}

// Initialize Kernel (lazy initialization)
let kernel = null;

function getKernel() {
  /**Get or initialize Kernel with State Machine*/
  if (!kernel) {
    logger.info("Initializing Kernel...");
    // State machine doesn't need DB session for basic operations (logging only)
    const stateMachine = new StateMachine();
    kernel = new Kernel(getRagService(), stateMachine);
    logger.info("Kernel initialized");
  }
  return kernel;
}

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const dest = process.env.VERCEL ? '/tmp' : settings.UPLOAD_DIR;
    cb(null, dest);
  },
  filename: (req, file, cb) => {
    // Preserve original filename (like Python version did)
    // Add unique prefix to avoid conflicts
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    let originalName = file.originalname;
    
    // Fix encoding if filename is garbled (UTF-8 interpreted as Latin-1)
    try {
      if (originalName.includes('×')) {
        // Fix UTF-8 that was decoded as Latin-1
        const buffer = Buffer.from(originalName, 'latin1');
        originalName = buffer.toString('utf-8');
      }
    } catch (e) {
      // If fixing fails, use as-is
    }
    
    // Keep original filename but add unique prefix
    cb(null, uniqueSuffix + '-' + originalName);
  }
});

const upload = multer({
  storage: storage,
  limits: {
    fileSize: settings.MAX_FILE_SIZE
  }
});

/**
 * Root endpoint
 */
app.get("/", (req, res) => {
  return res.json({
    message: "MATRIYA RAG System API",
    version: "1.0.0",
    status: "running"
  });
});

/**
 * Health check endpoint
 */
app.get("/health", async (req, res) => {
  try {
    const info = await getRagService().getCollectionInfo();
    return res.json({
      status: "healthy",
      vector_db: info
    });
  } catch (e) {
    logger.error(`Health check failed: ${e.message}`);
    return res.status(500).json({
      status: "unhealthy",
      error: e.message
    });
  }
});

/**
 * Upload and ingest a single file
 * 
 * Returns:
 *   Ingestion result
 */
app.post("/ingest/file", upload.single('file'), async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ error: "No file provided" });
  }
  
  const file = req.file;
  if (!file.originalname) {
    return res.status(400).json({ error: "No file selected" });
  }
  
  // Validate file extension
  const fileExt = file.originalname.substring(file.originalname.lastIndexOf('.')).toLowerCase();
  if (!settings.ALLOWED_EXTENSIONS.includes(fileExt)) {
    return res.status(400).json({
      error: `File type ${fileExt} not supported. Allowed: ${settings.ALLOWED_EXTENSIONS.join(', ')}`
    });
  }
  
  // Validate file size
  if (file.size > settings.MAX_FILE_SIZE) {
    return res.status(400).json({
      error: `File size exceeds maximum of ${settings.MAX_FILE_SIZE} bytes`
    });
  }
  
  const tempFilePath = file.path;
  // Get original filename and fix encoding issues
  // Browsers often send filenames in RFC 2231 format or URL-encoded
  let originalFilename = file.originalname;
  
  // Handle different encoding scenarios
  if (Buffer.isBuffer(originalFilename)) {
    originalFilename = originalFilename.toString('utf-8');
  }
  
  // Try to fix garbled UTF-8 (when UTF-8 bytes are interpreted as Latin-1)
  // This happens when browsers send UTF-8 but it's decoded as Latin-1
  try {
    // If filename contains garbled characters (like ×), try to fix it
    if (originalFilename.includes('×')) {
      // Convert to Buffer and re-decode as UTF-8
      const buffer = Buffer.from(originalFilename, 'latin1');
      originalFilename = buffer.toString('utf-8');
      logger.info(`Fixed filename encoding: ${originalFilename}`);
    }
    
    // Also try URL decoding if it contains encoded characters
    if (originalFilename.includes('%') && /%[0-9A-F]{2}/i.test(originalFilename)) {
      originalFilename = decodeURIComponent(originalFilename);
    }
  } catch (e) {
    logger.warn(`Could not fix filename encoding: ${e.message}, using as-is: ${originalFilename}`);
  }
  
  try {
    // Ingest file - pass original filename so it's preserved in metadata
    const result = await getRagService().ingestFile(tempFilePath, originalFilename);
    
    // Clean up temp file
    try {
      if (existsSync(tempFilePath)) {
        unlinkSync(tempFilePath);
      }
    } catch (e) {
      logger.warn(`Failed to delete temp file: ${e.message}`);
    }
    
    if (result.success) {
      return res.json({
        success: true,
        message: "File ingested successfully",
        data: result
      });
    } else {
      return res.status(500).json({
        error: result.error || 'Unknown error during ingestion'
      });
    }
  } catch (e) {
    logger.error(`Error ingesting file: ${e.message}`);
    logger.error(`Stack trace: ${e.stack}`);
    // Clean up temp file on error
    try {
      if (existsSync(tempFilePath)) {
        unlinkSync(tempFilePath);
      }
    } catch (e2) {
      // Ignore cleanup errors
    }
    return res.status(500).json({
      error: `Error ingesting file: ${e.message}`,
      details: process.env.NODE_ENV === 'development' ? e.stack : undefined
    });
  }
});

/**
 * Ingest all supported files from a directory
 * 
 * Returns:
 *   Ingestion results for all files
 */
app.post("/ingest/directory", async (req, res) => {
  const { directory_path } = req.body;
  if (!directory_path) {
    return res.status(400).json({ error: "directory_path is required" });
  }
  
  if (!existsSync(directory_path)) {
    return res.status(404).json({
      error: `Directory not found: ${directory_path}`
    });
  }
  
  try {
    const result = await getRagService().ingestDirectory(directory_path);
    return res.json(result);
  } catch (e) {
    logger.error(`Error ingesting directory: ${e.message}`);
    return res.status(500).json({
      error: `Error ingesting directory: ${e.message}`
    });
  }
});

/**
 * Search for relevant documents and optionally generate an answer
 * 
 * Query params:
 *   query: Search query (required)
 *   n_results: Number of results to return (default: 5)
 *   filename: Optional filename filter
 *   generate_answer: Whether to generate AI answer from results (default: true)
 * 
 * Returns:
 *   Search results and generated answer
 */
app.get("/search", async (req, res) => {
  const query = req.query.query;
  if (!query) {
    return res.status(400).json({ error: "query parameter is required" });
  }
  
  let nResults = parseInt(req.query.n_results) || 5;
  if (nResults < 1 || nResults > 50) {
    nResults = 5;
  }
  
  const filename = req.query.filename || null;
  const generateAnswer = req.query.generate_answer !== 'false';
  
  const filterMetadata = filename ? { filename } : null;
  
  try {
    if (generateAnswer) {
      // Process through Kernel (State Machine flow)
      // Flow: User Intent → Kernel → Agents → Kernel → Decision
      const kernel = getKernel();
      const kernelResult = await kernel.processUserIntent(
        query,
        null,  // Can be added from auth if needed
        null,  // Will be generated by Doc Agent
        filterMetadata  // Pass filename filter to Kernel
      );
      
      // If blocked or stopped, return appropriate response
      if (kernelResult.decision === 'block' || kernelResult.decision === 'stop') {
        return res.json({
          query: query,
          results_count: 0,
          results: [],
          answer: null,
          context_sources: 0,
          context: "",
          error: kernelResult.reason || 'תשובה נחסמה',
          decision: kernelResult.decision,
          state: kernelResult.state,
          blocked: true,
          block_reason: kernelResult.reason || ''
        });
      }
      
      // If allowed (with or without warnings)
      return res.json({
        query: query,
        results_count: kernelResult.agent_results.doc_agent.results_count || 0,
        results: kernelResult.search_results || [],
        answer: kernelResult.answer,
        context_sources: kernelResult.agent_results.doc_agent.context_sources || 0,
        context: kernelResult.context || '',  // Include context for agent checks
        error: null,
        decision: kernelResult.decision,
        state: kernelResult.state,
        warning: kernelResult.warning,
        agent_results: {
          contradiction: kernelResult.agent_results.contradiction_agent,
          risk: kernelResult.agent_results.risk_agent
        }
      });
    } else {
      // Just return search results
      const results = await getRagService().search(query, nResults, filterMetadata);
      return res.json({
        query: query,
        results_count: results.length,
        results: results,
        answer: null
      });
    }
  } catch (e) {
    logger.error(`Error searching: ${e.message}`);
    return res.status(500).json({
      error: `Error searching: ${e.message}`
    });
  }
});

/**
 * Contradiction Agent - Checks for contradictions in the answer
 * 
 * JSON body:
 *   answer: The answer from Doc Agent
 *   context: The context used to generate the answer
 *   query: Original user query
 * 
 * Returns:
 *   Contradiction analysis results
 */
app.post("/agent/contradiction", async (req, res) => {
  const { answer, context, query } = req.body;
  
  if (!answer || !context || !query) {
    return res.status(400).json({ error: "answer, context, and query are required" });
  }
  
  try {
    const result = await getRagService().checkContradictions(answer, context, query);
    return res.json(result);
  } catch (e) {
    logger.error(`Error checking contradictions: ${e.message}`);
    return res.status(500).json({
      error: `Error checking contradictions: ${e.message}`
    });
  }
});

/**
 * Risk Agent - Identifies risks in the answer
 * 
 * JSON body:
 *   answer: The answer from Doc Agent
 *   context: The context used for the answer
 *   query: Original user query
 * 
 * Returns:
 *   Risk analysis results
 */
app.post("/agent/risk", async (req, res) => {
  const { answer, context, query } = req.body;
  
  if (!answer || !context || !query) {
    return res.status(400).json({ error: "answer, context, and query are required" });
  }
  
  try {
    const result = await getRagService().checkRisks(answer, context, query);
    return res.json(result);
  } catch (e) {
    logger.error(`Error checking risks: ${e.message}`);
    return res.status(500).json({
      error: `Error checking risks: ${e.message}`
    });
  }
});

/**
 * Get information about the vector database collection
 */
app.get("/collection/info", async (req, res) => {
  try {
    const info = await getRagService().getCollectionInfo();
    return res.json(info);
  } catch (e) {
    logger.error(`Error getting collection info: ${e.message}`);
    return res.status(500).json({
      error: `Error getting collection info: ${e.message}`
    });
  }
});

/**
 * Get list of all uploaded files
 */
app.get("/files", async (req, res) => {
  try {
    const filenames = await getRagService().getAllFilenames();
    return res.json({
      files: filenames,
      count: filenames.length
    });
  } catch (e) {
    logger.error(`Error getting files: ${e.message}`);
    return res.status(500).json({
      error: `Error getting files: ${e.message}`
    });
  }
});

/**
 * Delete documents by IDs
 * 
 * JSON body:
 *   ids: List of document IDs to delete
 * 
 * Returns:
 *   Deletion result
 */
app.delete("/documents", async (req, res) => {
  const { ids } = req.body;
  if (!ids || !Array.isArray(ids)) {
    return res.status(400).json({ error: "ids array is required" });
  }
  
  try {
    const success = await getRagService().deleteDocuments(ids);
    if (success) {
      return res.json({
        success: true,
        message: `Deleted ${ids.length} documents`,
        deleted_ids: ids
      });
    } else {
      return res.status(500).json({
        error: "Failed to delete documents"
      });
    }
  } catch (e) {
    logger.error(`Error deleting documents: ${e.message}`);
    return res.status(500).json({
      error: `Error deleting documents: ${e.message}`
    });
  }
});

/**
 * Reset the entire vector database (WARNING: This deletes all data)
 * 
 * Returns:
 *   Reset result
 */
app.post("/reset", async (req, res) => {
  try {
    const success = await getRagService().resetDatabase();
    if (success) {
      return res.json({
        success: true,
        message: "Database reset successfully"
      });
    } else {
      return res.status(500).json({
        error: "Failed to reset database"
      });
    }
  } catch (e) {
    logger.error(`Error resetting database: ${e.message}`);
    return res.status(500).json({
      error: `Error resetting database: ${e.message}`
    });
  }
});

// Start server
if (!process.env.VERCEL) {
  app.listen(settings.API_PORT, settings.API_HOST, () => {
    logger.info(`Server running on http://${settings.API_HOST}:${settings.API_PORT}`);
  });
}

export default app;
