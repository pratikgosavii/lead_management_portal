import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lead_management.settings')
django.setup()

# Import models
from django.contrib.auth import get_user_model
from accounts.models import UserProfile
from leads.models import LeadSource, LeadStatus, Lead
from clients.models import Client
from projects.models import ProjectStatus, Project
from payments.models import PaymentMethod

User = get_user_model()

def create_initial_data():
    print("Creating initial data...")
    
    # Create lead sources
    lead_sources = [
        {"name": "Website", "description": "Leads from company website"},
        {"name": "Referral", "description": "Referred by existing clients"},
        {"name": "Social Media", "description": "Leads from social media platforms"},
        {"name": "Email Campaign", "description": "From email marketing campaigns"},
        {"name": "Trade Show", "description": "From industry trade shows"},
    ]
    
    for source in lead_sources:
        LeadSource.objects.get_or_create(name=source["name"], defaults={"description": source["description"]})
    
    print("✓ Created lead sources")
    
    # Create lead statuses
    lead_statuses = [
        {"name": "New", "description": "New leads that need initial contact", "is_converted": False, "order": 1},
        {"name": "Contacted", "description": "Leads that have been contacted", "is_converted": False, "order": 2},
        {"name": "Qualified", "description": "Qualified leads with potential", "is_converted": False, "order": 3},
        {"name": "Proposal", "description": "Leads that have received a proposal", "is_converted": False, "order": 4},
        {"name": "Negotiation", "description": "In negotiation phase", "is_converted": False, "order": 5},
        {"name": "Won", "description": "Successfully converted leads", "is_converted": True, "order": 6},
        {"name": "Lost", "description": "Lost opportunities", "is_converted": False, "order": 7},
    ]
    
    for status in lead_statuses:
        LeadStatus.objects.get_or_create(
            name=status["name"], 
            defaults={
                "description": status["description"],
                "is_converted": status["is_converted"],
                "order": status["order"]
            }
        )
    
    print("✓ Created lead statuses")
    
    # Create project statuses
    project_statuses = [
        {"name": "Not Started", "description": "Project has not started yet", "order": 1},
        {"name": "In Progress", "description": "Project is currently in progress", "order": 2},
        {"name": "On Hold", "description": "Project is temporarily on hold", "order": 3},
        {"name": "Completed", "description": "Project has been completed", "order": 4},
        {"name": "Cancelled", "description": "Project has been cancelled", "order": 5},
    ]
    
    for status in project_statuses:
        ProjectStatus.objects.get_or_create(
            name=status["name"], 
            defaults={
                "description": status["description"],
                "order": status["order"]
            }
        )
    
    print("✓ Created project statuses")
    
    # Create payment methods
    payment_methods = [
        {"name": "Credit Card", "description": "Payment via credit card"},
        {"name": "Bank Transfer", "description": "Payment via bank transfer"},
        {"name": "PayPal", "description": "Payment via PayPal"},
        {"name": "Cash", "description": "Payment in cash"},
        {"name": "Check", "description": "Payment by check"},
    ]
    
    for method in payment_methods:
        PaymentMethod.objects.get_or_create(
            name=method["name"], 
            defaults={"description": method["description"]}
        )
    
    print("✓ Created payment methods")
    
    # Create team members (users)
    users = [
        {
            "username": "manager1",
            "email": "manager1@example.com",
            "password": "password",
            "first_name": "Mark",
            "last_name": "Johnson",
            "role": "manager",
            "is_staff": True,
            "profile": {
                "phone_number": "+1234567890",
                "address": "123 Manager St, Business City",
                "daily_rate": 200.00
            }
        },
        {
            "username": "teamlead1",
            "email": "teamlead1@example.com",
            "password": "password",
            "first_name": "Sarah",
            "last_name": "Williams",
            "role": "team_leader",
            "is_staff": True,
            "profile": {
                "phone_number": "+1987654321",
                "address": "456 Leader Ave, Sales Town",
                "daily_rate": 150.00
            }
        },
        {
            "username": "sales1",
            "email": "sales1@example.com",
            "password": "password",
            "first_name": "John",
            "last_name": "Smith",
            "role": "sales_rep",
            "is_staff": False,
            "profile": {
                "phone_number": "+1122334455",
                "address": "789 Sales Rd, Prospect City",
                "daily_rate": 100.00
            }
        },
        {
            "username": "sales2",
            "email": "sales2@example.com",
            "password": "password",
            "first_name": "Emma",
            "last_name": "Davis",
            "role": "sales_rep",
            "is_staff": False,
            "profile": {
                "phone_number": "+1555666777",
                "address": "321 Rep Blvd, Lead Village",
                "daily_rate": 100.00
            }
        }
    ]
    
    # Get the admin user to set as manager
    try:
        admin_user = User.objects.get(username="Admin")
        print(f"Found admin user: {admin_user.username}")
    except User.DoesNotExist:
        admin_user = None
        print("Admin user not found")
    
    created_users = []
    for user_data in users:
        profile_data = user_data.pop('profile', {})
        
        user, created = User.objects.get_or_create(
            username=user_data["username"],
            defaults={
                "email": user_data["email"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "role": user_data["role"],
                "is_staff": user_data["is_staff"]
            }
        )
        
        if created:
            user.set_password(user_data["password"])
            user.save()
            created_users.append(user)
            
            # Create or update user profile
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "phone_number": profile_data.get("phone_number", ""),
                    "address": profile_data.get("address", ""),
                    "daily_rate": profile_data.get("daily_rate", 0)
                }
            )
    
    # Set manager relationships after all users are created
    if created_users:
        # Find users by role
        managers = User.objects.filter(role="manager")
        team_leaders = User.objects.filter(role="team_leader")
        sales_reps = User.objects.filter(role="sales_rep")
        
        # Assign admin as manager for managers
        for manager in managers:
            if admin_user:
                print(f"Setting {admin_user.username} as manager for {manager.username}")
                # No direct manager relationship in CustomUser, handle via other means if needed
        
        # Assign managers to team leaders
        for team_leader in team_leaders:
            if managers.exists():
                manager = managers.first()
                print(f"Setting {manager.username} as manager for {team_leader.username}")
                # No direct manager relationship in CustomUser, handle via other means if needed
        
        # Assign team leaders to sales reps
        for sales_rep in sales_reps:
            if team_leaders.exists():
                team_leader = team_leaders.first()
                print(f"Setting {team_leader.username} as manager for {sales_rep.username}")
                # No direct manager relationship in CustomUser, handle via other means if needed
    
    print(f"✓ Created {len(created_users)} users")
    
    # Create sample leads
    if User.objects.exists() and LeadSource.objects.exists() and LeadStatus.objects.exists():
        leads = [
            {
                "name": "John Potential",
                "company": "Acme Corp",
                "phone": "+1234567890",
                "email": "john@acmecorp.com",
                "address": "123 Business St, City",
                "notes": "Interested in our premium package"
            },
            {
                "name": "Sarah Prospect",
                "company": "XYZ Industries",
                "phone": "+1987654321",
                "email": "sarah@xyzind.com",
                "address": "456 Industry Ave, Town",
                "notes": "Requested a product demo"
            },
            {
                "name": "Mike Customer",
                "company": "Global Solutions",
                "phone": "+1122334455",
                "email": "mike@globalsolutions.com",
                "address": "789 Global Rd, City",
                "notes": "Looking for a customized solution"
            }
        ]
        
        created_leads = []
        creator = User.objects.first()
        assigned_to = User.objects.filter(role="sales_rep").first() or creator
        source = LeadSource.objects.first()
        status = LeadStatus.objects.filter(name="New").first() or LeadStatus.objects.first()
        
        for lead_data in leads:
            lead, created = Lead.objects.get_or_create(
                name=lead_data["name"],
                defaults={
                    "company": lead_data["company"],
                    "phone": lead_data["phone"],
                    "email": lead_data["email"],
                    "address": lead_data["address"],
                    "notes": lead_data["notes"],
                    "created_by": creator,
                    "assigned_to": assigned_to,
                    "source": source,
                    "status": status
                }
            )
            
            if created:
                created_leads.append(lead)
        
        print(f"✓ Created {len(created_leads)} leads")
    
    print("Initial data created successfully!")

if __name__ == "__main__":
    create_initial_data()