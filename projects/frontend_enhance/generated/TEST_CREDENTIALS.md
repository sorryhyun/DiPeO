# Test Credentials for Development

The application includes mock authentication for development purposes. Use these test accounts to log in:

## Available Test Accounts

### Admin Account
- **Email:** admin@example.com
- **Password:** admin123
- **Role:** Administrator
- **Permissions:** Full access (read, write, delete, admin)

### Regular User Account
- **Email:** user@example.com
- **Password:** user123
- **Role:** User
- **Permissions:** Standard access (read, write)

### Test Account
- **Email:** test@test.com
- **Password:** test123
- **Role:** User
- **Permissions:** Standard access (read, write)

## Notes

- Mock authentication only works when running on localhost or 127.0.0.1
- The mock tokens expire after 24 hours
- Authentication state is stored in localStorage
- If you have a backend API running, the app will try to use real authentication first

## Running the Application

```bash
# Install dependencies
pnpm install

# Start development server
pnpm dev
```

The application will be available at http://localhost:3001

Navigate to `/signin` or you'll be automatically redirected there if not authenticated.