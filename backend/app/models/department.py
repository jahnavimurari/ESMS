from datetime import datetime, timezone
from sqlalchemy import Integer, String, Text, Boolean, DateTime
from app.extension_registry import db

class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(Integer, primary_key=True, autoincrement=True)
    name = db.Column(String(100), unique=True, nullable=False, index=True)
    code = db.Column(String(20), unique=True, nullable=False, index=True)
    description = db.Column(Text, nullable=True)
    is_active = db.Column(Boolean, default=True, nullable=False)
    created_at = db.Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    employees = db.relationship("Employee", back_populates="department")

    def to_dict(self, include_employee_count=False):
        """Returns dictionary representation of department."""
        data = {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "description": self.description,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_employee_count:
            data["employee_count"] = len(self.employees) if self.employees else 0
        return data

    def __repr__(self):
        return f"<Department {self.code} - {self.name}>"

