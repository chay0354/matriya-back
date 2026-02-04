# User Authentication System - Summary

## What Was Added

### 1. **Local SQLite Database** (`back/database.py`)
- SQLite database for user management
- Located at: `back/chroma_db/../users.db`
- User model with: username, email, password, full_name, is_admin, etc.

### 2. **Authentication System** (`back/auth.py`)
- Password hashing with bcrypt
- JWT token generation and verification
- User authentication functions
- Token expiration: 30 days

### 3. **Authentication Endpoints** (`back/auth_endpoints.py`)
- `POST /auth/signup` - Create new user account
- `POST /auth/login` - Login and get token
- `GET /auth/me` - Get current user info (protected)

### 4. **Frontend Login/Signup** (`front/src/components/LoginTab.js`)
- Login form
- Signup form
- Toggle between login/signup
- Error handling

### 5. **Frontend Authentication** (`front/src/App.js`)
- Checks for existing token on load
- Shows login screen if not authenticated
- Shows main app if authenticated
- Logout functionality
- User info display in header

### 6. **API Utility** (`front/src/utils/api.js`)
- Centralized axios instance
- Automatic token injection
- 401 error handling (auto-logout)

### 7. **Updated Components**
- All components now use authenticated API calls
- Token automatically included in requests

## Database Structure

**Users Table:**
- `id` - Primary key
- `username` - Unique username
- `email` - Unique email
- `hashed_password` - Bcrypt hashed password
- `full_name` - Optional full name
- `is_active` - Account status
- `is_admin` - Admin flag
- `created_at` - Registration timestamp
- `last_login` - Last login timestamp

## Security Features

✅ **Password Hashing** - Bcrypt with salt
✅ **JWT Tokens** - Secure token-based authentication
✅ **Token Expiration** - 30 days
✅ **Protected Routes** - API endpoints can require authentication
✅ **Auto Token Refresh** - Frontend checks token validity

## How It Works

1. **Signup**: User creates account → Password hashed → User saved to DB → Token returned
2. **Login**: Username/password verified → Token generated → Token stored in localStorage
3. **API Calls**: Token automatically added to Authorization header
4. **Token Validation**: Backend verifies token on protected endpoints

## Next Steps (Optional)

- Add password reset functionality
- Add email verification
- Add role-based permissions
- Add user profile management
- Add session management
- Protect RAG endpoints (currently open)

## Testing

Test the authentication:
1. Start backend: `cd back && python main.py`
2. Start frontend: `cd front && npm start`
3. You'll see login screen
4. Click "הירשם כאן" to signup
5. After signup/login, you'll see the main app

The system is ready to use!
