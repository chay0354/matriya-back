/**
 * Admin endpoints for file management and user permissions
 */
import express from 'express';
import { User, FilePermission, SearchHistory } from './database.js';
import { getCurrentUser } from './authEndpoints.js';
import RAGService from './ragService.js';
import logger from './logger.js';

const router = express.Router();

// Lazy initialization of RAG service
let _ragService = null;

function getRagService() {
  /**Get or initialize RAG service (lazy initialization)*/
  if (!_ragService) {
    logger.info("Initializing RAG service for admin...");
    _ragService = new RAGService();
    logger.info("RAG service initialized");
  }
  return _ragService;
}

/**
 * Middleware to verify that the current user is an admin
 */
async function verifyAdmin(req, res, next) {
  const user = await getCurrentUser(req);
  if (!user) {
    return res.status(401).json({ error: "Authentication required" });
  }
  
  // Check both is_admin flag and username
  if (!(user.is_admin || user.username === "admin")) {
    return res.status(403).json({ error: "Admin access required" });
  }
  
  req.user = user;
  next();
}

/**
 * Get all files in the database (admin only)
 */
router.get("/files", verifyAdmin, async (req, res) => {
  try {
    const ragService = getRagService();
    const filenames = await ragService.getAllFilenames();
    return res.json({
      files: filenames,
      count: filenames.length
    });
  } catch (e) {
    logger.error(`Error getting files: ${e.message}`);
    return res.status(500).json({ error: `Error getting files: ${e.message}` });
  }
});

/**
 * Delete a file and all its chunks from the database (admin only)
 */
router.delete("/files/:filename", verifyAdmin, async (req, res) => {
  try {
    const { filename } = req.params;
    const ragService = getRagService();
    // Delete documents with matching filename in metadata
    const result = await ragService.vectorStore.deleteDocuments(
      null,
      { filename: filename }
    );
    return res.json({
      success: true,
      message: `File '${filename}' deleted successfully`,
      deleted_count: result.deleted_count || 0
    });
  } catch (e) {
    logger.error(`Error deleting file: ${e.message}`);
    return res.status(500).json({ error: `Error deleting file: ${e.message}` });
  }
});

/**
 * Get all users (admin only)
 */
router.get("/users", verifyAdmin, async (req, res) => {
  try {
    const users = await User.findAll();
    return res.json({
      users: users.map(user => ({
        id: user.id,
        username: user.username,
        email: user.email,
        full_name: user.full_name,
        is_active: user.is_active,
        is_admin: user.is_admin,
        created_at: user.created_at ? user.created_at.toISOString() : null
      })),
      count: users.length
    });
  } catch (e) {
    logger.error(`Error getting users: ${e.message}`);
    return res.status(500).json({ error: `Error getting users: ${e.message}` });
  }
});

/**
 * Get file permissions for a specific user (admin only)
 */
router.get("/users/:user_id/permissions", verifyAdmin, async (req, res) => {
  try {
    const userId = parseInt(req.params.user_id);
    const targetUser = await User.findByPk(userId);
    if (!targetUser) {
      return res.status(404).json({ error: "User not found" });
    }
    
    // Check if user has a special "access_all" permission (no specific file permissions = access all)
    const permissions = await FilePermission.findAll({
      where: { user_id: userId }
    });
    
    // If no permissions exist, user has access to all files
    const accessAllFiles = permissions.length === 0;
    const allowedFiles = accessAllFiles ? [] : permissions.map(p => p.filename);
    
    return res.json({
      user_id: targetUser.id,
      username: targetUser.username,
      access_all_files: accessAllFiles,
      allowed_files: allowedFiles
    });
  } catch (e) {
    logger.error(`Error getting user permissions: ${e.message}`);
    return res.status(500).json({ error: `Error getting user permissions: ${e.message}` });
  }
});

/**
 * Set file permissions for a specific user (admin only)
 */
router.post("/users/:user_id/permissions", verifyAdmin, async (req, res) => {
  try {
    const userId = parseInt(req.params.user_id);
    const { access_all_files, allowed_files } = req.body;
    
    if (access_all_files === undefined) {
      return res.status(400).json({ error: "access_all_files is required" });
    }
    
    if (!Array.isArray(allowed_files)) {
      return res.status(400).json({ error: "allowed_files must be a list" });
    }
    
    const targetUser = await User.findByPk(userId);
    if (!targetUser) {
      return res.status(404).json({ error: "User not found" });
    }
    
    // Delete existing permissions
    await FilePermission.destroy({ where: { user_id: userId } });
    
    // If access_all_files is True, don't add any permissions (empty list = access all)
    // If False, add permissions for each allowed file
    if (!access_all_files && allowed_files && allowed_files.length > 0) {
      for (const filename of allowed_files) {
        await FilePermission.create({
          user_id: userId,
          filename: filename
        });
      }
    }
    
    return res.json({
      success: true,
      message: `Permissions updated for user ${targetUser.username}`,
      user_id: targetUser.id,
      access_all_files: access_all_files,
      allowed_files: allowed_files || []
    });
  } catch (e) {
    logger.error(`Error setting user permissions: ${e.message}`);
    return res.status(500).json({ error: `Error setting user permissions: ${e.message}` });
  }
});

/**
 * Get all search history - questions and answers from all users (admin only)
 */
router.get("/search-history", verifyAdmin, async (req, res) => {
  try {
    if (!SearchHistory) {
      return res.json({ history: [], count: 0 });
    }
    const limit = Math.min(parseInt(req.query.limit) || 100, 500);
    const history = await SearchHistory.findAll({
      order: [['created_at', 'DESC']],
      limit
    });
    return res.json({
      history: history.map(h => ({
        id: h.id,
        user_id: h.user_id,
        username: h.username || 'אורח',
        question: h.question,
        answer: h.answer,
        created_at: h.created_at ? h.created_at.toISOString() : null
      })),
      count: history.length
    });
  } catch (e) {
    logger.error(`Error getting search history: ${e.message}`);
    return res.status(500).json({ error: `Error getting search history: ${e.message}` });
  }
});

export { router as adminRouter };
