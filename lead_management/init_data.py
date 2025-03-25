import os
import sys
import django

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lead_management.settings')
django.setup()

# Import models
from django.contrib.auth import get_user_model
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
            "daily_salary": 200.00,
            "is_staff": True
        },
        {
            "username": "teamlead1",
            "email": "teamlead1@example.com",
            "password": "password",
            "first_name": "Sarah",
            "last_name": "Williams",
            "role": "team_leader",
            "daily_salary": 150.00,
            "is_staff": True
        },
        {
            "username": "sales1",
            "email": "sales1@example.com",
            "password": "password",
            "first_name": "John",
            "last_name": "Smith",
            "role": "sales_rep",
            "daily_salary": 100.00,
            "is_staff": False
        },
        {
            "username": "sales2",
            "email": "sales2@example.com",
            "password": "password",
            "first_name": "Emma",
            "last_name": "Davis",
            "role": "sales_rep",
            "daily_salary": 100.00,
            "is_staff": False
        }
    ]
    
    # Get the admin user to set as manager
    try:
        admin_user = User.objects.get(username="admin")
    except User.DoesNotExist:
        admin_user = None
    
    created_users = []
    for user_data in users:
        user, created = User.objects.get_or_create(
            username=user_data["username"],
            defaults={
                "email": user_data["email"],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "role": user_data["role"],
                "daily_salary": user_data["daily_salary"],
                "is_staff": user_data["is_staff"]
            }
        )
        
        if created:
            user.set_password(user_data["password"])
            if user_data["role"] == "manager":
                user.manager = admin_user
            elif user_data["role"] == "team_leader":
                # Find a manager to assign as this user's manager
                manager = User.objects.filter(role="manager").first()
                if manager:
                    user.manager = manager
            elif user_data["role"] == "sales_rep":
                # Find a team leader to assign as this user's manager
                team_leader = User.objects.filter(role="team_leader").first()
                if team_leader:
                    user.manager = team_leader
            user.save()
            created_users.append(user)
    
    print(f"✓ Created {len(created_users)} users")
    
    print("Initial data created successfully!")

if __name__ == "__main__":
    create_initial_data()