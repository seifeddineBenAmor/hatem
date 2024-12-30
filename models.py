from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(20), unique=True, nullable=True)
    name = db.Column(db.String(50), nullable=False)
    familyName = db.Column(db.String(50), nullable=False)
    is_confirmed = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id', ondelete='SET NULL'), nullable=True)  # Allow NULL values
    program = db.relationship('Program', backref=db.backref('users', lazy=True))  # Keep the relationship
    gender = db.Column(db.String(10), nullable=False)
    remarks = db.Column(db.Text, nullable=True)
    dateOfBirth = db.Column(db.Date, nullable=True)
    expire_date = db.Column(db.Date, nullable=True)
    Photo = db.Column(db.String(255), nullable=False)
    def __repr__(self):
        return f'<User {self.name}>'


class Break(db.Model):
    Id = db.Column(db.Integer, primary_key=True)  # Match capitalization with DB
    duration = db.Column(db.String(255), nullable=False)
    VidPath = db.Column(db.String(255), nullable=False)  # Ensure consistency with DB

    def __repr__(self):
        return f'<Break {self.duration}>'

class Category(db.Model):
    Id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    numberOfInstances = db.Column(db.Integer, default=0)
    icone_Path=db.Column(db.String(255), nullable=False)
    icone_Path_female=db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Category {self.name}>'

class Exercices(db.Model):
    __tablename__ = 'exercices'

    code = db.Column(db.String(255), primary_key=True)
    name = db.Column(db.Text, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.Id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    videoPath = db.Column(db.Text, nullable=False)
    videoPath_female = db.Column(db.Text, nullable=False)
    category = db.relationship('Category', backref='exercises')  

    @staticmethod
    def generate_code(category_id, name):
        category = Category.query.get(category_id)
        if category is None:
            raise ValueError('Invalid category ID')

        instance_count = len(category.exercises.all())
        return f"{category.name[:2].upper()}_{name[:1].upper()}_{instance_count + 1}"

    def __repr__(self):
        return f'<Exercice {self.name}>'

class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    creator = db.Column(db.String(255), nullable=False)

    def __repr__(self):
        return f'<Program {self.name}>'

class ProgramDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'), nullable=False)
    exercice_code = db.Column(db.String(255), db.ForeignKey('exercices.code'), nullable=True)
    break_id = db.Column(db.Integer, db.ForeignKey('break.Id'), nullable=True)
    sequence = db.Column(db.Integer, nullable=False)
    day = db.Column(db.Integer, nullable=False)
    type = db.Column(db.Enum('exercise', 'break'), nullable=False)

    def __repr__(self):
        return f'<ProgramDetails Program {self.program_id} Item {self.id}>'
