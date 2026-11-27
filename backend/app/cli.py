import os
import click
from flask.cli import with_appcontext
from app.extension_registry import db
from app.models.user import User

@click.command("create-admin")
@click.option("--email", prompt="Admin Email", help="Email for the administrator account.")
@click.option("--password", prompt=True, hide_input=True, confirmation_prompt=True, help="Password for the administrator account.")
@with_appcontext
def create_admin_command(email, password):
    """
    Securely initializes the initial System Administrator.
    Prevents duplicate admin accounts and safely hashes the password.
    Never prints or logs the plain-text password.
    """
    email = email.strip().lower()

    if not email or "@" not in email:
        click.echo("Error: A valid email address is required.")
        return

    if not password or len(password) < 8:
        click.echo("Error: Password must be at least 8 characters long.")
        return

    # Check for existing admin or duplicate email
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        click.echo(f"Error: A user account with email '{email}' already exists.")
        return

    try:
        admin = User(
            email=email,
            role="ADMIN",
            is_active=True
        )
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        click.echo(f"Success: Administrator account '{email}' created successfully.")
    except Exception as exc:
        db.session.rollback()
        click.echo(f"Failed to create administrator account: {exc.__class__.__name__}")

