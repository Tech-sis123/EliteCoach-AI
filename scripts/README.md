# Admin Scripts

## Creating a Platform Admin

Platform admin accounts cannot be created through the API.
Run this command directly on your server or local machine:

    python scripts/create_admin.py \
      --email admin@elitecoach.ai \
      --name "Your Name" \
      --password "YourStrongPassword123!"

Requirements:
- Must be run with DATABASE_URL set in your environment
- Password minimum 8 characters
- Email must be unique
- Run this ONCE after first deployment to seed the first admin
- Additional admins can be created by an existing platform_admin 
  via POST /api/v1/admin/tutors/onboard with role: platform_admin