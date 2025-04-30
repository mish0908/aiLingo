from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash

# ------------------------------------------------------------------
# CRUD / auth helpers
# ------------------------------------------------------------------

def create_user(username: str, email: str, password: str):
    """Create and return a new user.
    Returns None if username or email already exists."""
    username = username.strip()
    email    = email.strip().lower()

    if not username or not email or not password:
        return None

    if User.query.filter((User.username == username) | (User.email == email)).first():
        return None

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def authenticate(identifier: str, password: str):
    """Return user if identifier (username or email) and password match, else None."""
    identifier = identifier.strip()
    user = User.query.filter((User.username == identifier) | (User.email == identifier)).first()
    if user and user.check_password(password):
        return user
    return None


def get_user(user_id: int):
    """Fetch user by primary key."""
    return User.query.get(user_id)