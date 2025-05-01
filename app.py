import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, IntegerField, SelectField, SubmitField, SelectMultipleField, StringField, TextAreaField, FileField
from wtforms.validators import DataRequired, NumberRange
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from translations import translations
import csv
import io
import zipfile
from werkzeug.datastructures import FileStorage
from flask_wtf.csrf import CSRFError, generate_csrf

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Folder for storing files
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'txt', 'xlsx'}

# Session configuration
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True if using HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Initialize CSRF protection with updated settings
csrf = CSRFProtect(app)
csrf.init_app(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

def init_db():
    with app.app_context():
        # Ensure instance directory exists
        if not os.path.exists('instance'):
            os.makedirs('instance')
        # Create database if it doesn't exist
        db.create_all()
        
        # Return True if database exists after initialization
        return os.path.exists('instance/inventory.db')

# Language handling
def get_language():
    return session.get('language', 'en')

def get_translation(key):
    language = get_language()
    return translations.get(language, {}).get(key, translations['en'].get(key, key))

@app.context_processor
def inject_translations():
    return dict(t=get_translation)

@app.route('/')
def index():
    return redirect(url_for('dashboard'))

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    min_stock_level = db.Column(db.Integer, nullable=False, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', name='fk_item_category'), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('location.id', name='fk_item_location'), nullable=True)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id', name='fk_item_material'), nullable=True)
    color_id = db.Column(db.Integer, db.ForeignKey('color.id', name='fk_item_color'), nullable=True)

    material = db.relationship('Material', backref=db.backref('items', lazy=True))
    color = db.relationship('Color', backref=db.backref('items', lazy=True))
    category = db.relationship('Category', backref=db.backref('items', lazy=True))
    location = db.relationship('Location', backref=db.backref('items', lazy=True))

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('document_category.id', name='fk_document_category'), nullable=True)
    file_path = db.Column(db.String(200), nullable=False)
    
    category = db.relationship('DocumentCategory', backref=db.backref('documents', lazy=True))

class ProjectItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    item = db.relationship('Item', backref=db.backref('project_items', lazy=True))

class ProjectDocument(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False)
    
    document = db.relationship('Document', backref=db.backref('project_documents', lazy=True))

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    items = db.relationship('ProjectItem', backref='project', lazy=True, cascade='all, delete-orphan')
    documents = db.relationship('ProjectDocument', backref='project', lazy=True, cascade='all, delete-orphan')

class ItemForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    min_stock_level = IntegerField('Minimum Stock Level', validators=[DataRequired()], default=0)
    category = SelectField('Category', coerce=int)
    location = SelectField('Location', coerce=int)
    material = SelectField('Material', coerce=int)
    color = SelectField('Color', coerce=int)
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(ItemForm, self).__init__(*args, **kwargs)
        # Set translated labels
        self.name.label.text = get_translation('item_name')
        self.quantity.label.text = get_translation('quantity')
        self.min_stock_level.label.text = get_translation('min_stock_level')
        self.category.label.text = get_translation('category')
        self.location.label.text = get_translation('location')
        self.material.label.text = get_translation('material')
        self.color.label.text = get_translation('color')
        self.submit.label.text = get_translation('save')
        
        # Add None option (value 0) at the beginning of the choices
        self.material.choices = [(0, get_translation('none'))] + [(m.id, m.name) for m in Material.query.all()]
        self.color.choices = [(0, get_translation('none'))] + [(c.id, c.name) for c in Color.query.all()]
        self.category.choices = [(0, get_translation('none'))] + [(c.id, c.name) for c in Category.query.all()]
        self.location.choices = [(0, get_translation('none'))] + [(l.id, l.name) for l in Location.query.all()]

class DocumentForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    category = SelectField('Category', coerce=int)
    file = StringField('File')
    submit = SubmitField('Upload')

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        self.category.choices = [(0, 'None')] + [(c.id, c.name) for c in DocumentCategory.query.all()]

class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    items = SelectMultipleField('Items', coerce=int)
    item_quantities = StringField('Item Quantities')  # Will be handled with JavaScript
    documents = SelectMultipleField('Documents', coerce=int)
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        self.name.label.text = get_translation('project_name')
        self.description.label.text = get_translation('description')
        self.items.label.text = get_translation('required_items')
        self.documents.label.text = get_translation('related_documents')
        self.submit.label.text = get_translation('save')
        self.items.choices = [(item.id, f"{item.name} (Available: {item.quantity})") for item in Item.query.all()]
        self.documents.choices = [(doc.id, doc.name) for doc in Document.query.all()]

class SettingsForm(FlaskForm):
    material = StringField('New Material')
    color = StringField('New Color')
    category = StringField('New Category')
    location = StringField('New Location')
    document_category = StringField('New Document Category')
    submit_material = SubmitField('Add Material')
    submit_color = SubmitField('Add Color')
    submit_category = SubmitField('Add Category')
    submit_location = SubmitField('Add Location')
    submit_document_category = SubmitField('Add Document Category')

class UseItemForm(FlaskForm):
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=1)])
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super(UseItemForm, self).__init__(*args, **kwargs)
        self.quantity.label.text = get_translation('quantity')
        self.submit.label.text = get_translation('save')

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Color(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class DocumentCategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

class Location(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

@app.route('/dashboard')
def dashboard():
    # Calculate total quantities
    total_quantity = db.session.query(db.func.sum(Item.quantity)).scalar() or 0
    total_documents = Document.query.count()
    total_projects = Project.query.count()

    # Get all items for low stock alert (including warning levels)
    low_stock_items = Item.query.filter(
        Item.quantity <= Item.min_stock_level * 1.25  # Show items within 25% of minimum
    ).order_by(Item.quantity.asc()).all()
    low_stock_count = len([item for item in low_stock_items if item.quantity < item.min_stock_level])

    # Get recent activities
    recent_activities = []
    for item in Item.query.order_by(Item.id.desc()).limit(5).all():
        recent_activities.append({
            'item_id': item.id,
            'item_name': item.name,
            'action': get_translation('stock_update'),
            'quantity': item.quantity,
            'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })

    return render_template('dashboard.html',
                         total_quantity=total_quantity,
                         total_documents=total_documents,
                         total_projects=total_projects,
                         low_stock_items=low_stock_items,
                         low_stock_count=low_stock_count,
                         recent_activities=recent_activities)

@app.route('/inventory', methods=['GET'])
def inventory():
    query = request.args.get('search', '')
    items = Item.query.filter(Item.name.contains(query)).all()
    form = ItemForm()  # Create an instance of the form
    return render_template('inventory.html', items=items, query=query, form=form)

@app.route('/add_item', methods=['GET', 'POST'])
def add_item():
    form = ItemForm()

    if form.validate_on_submit():
        new_item = Item(
            name=form.name.data,
            quantity=form.quantity.data,
            min_stock_level=form.min_stock_level.data,
            category_id=None if form.category.data == 0 else form.category.data,
            location_id=None if form.location.data == 0 else form.location.data,
            material_id=None if form.material.data == 0 else form.material.data,
            color_id=None if form.color.data == 0 else form.color.data
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Item added successfully!', 'success')
        return redirect(url_for('inventory'))
    return render_template('add_item.html', form=form)

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    form = ItemForm(obj=item)

    if form.validate_on_submit():
        item.name = form.name.data
        item.quantity = form.quantity.data
        item.min_stock_level = form.min_stock_level.data
        item.category_id = None if form.category.data == 0 else form.category.data
        item.location_id = None if form.location.data == 0 else form.location.data
        item.material_id = None if form.material.data == 0 else form.material.data
        item.color_id = None if form.color.data == 0 else form.color.data

        db.session.commit()
        flash('Item updated successfully!', 'success')
        return redirect(url_for('inventory'))

    # Set initial values
    if item.material_id is None:
        form.material.data = 0
    else:
        form.material.data = item.material_id

    if item.color_id is None:
        form.color.data = 0
    else:
        form.color.data = item.color_id

    if item.category_id is None:
        form.category.data = 0
    else:
        form.category.data = item.category_id

    if item.location_id is None:
        form.location.data = 0
    else:
        form.location.data = item.location_id

    return render_template('edit_item.html', form=form, item=item)

@app.route('/use/<int:item_id>', methods=['GET', 'POST'])
def use_item(item_id):
    item = Item.query.get_or_404(item_id)
    form = UseItemForm()

    if form.validate_on_submit():
        quantity = form.quantity.data
        action = request.form.get('action')

        if action == 'subtract':
            if quantity > item.quantity:
                flash('Not enough items in stock!', 'error')
                return redirect(url_for('use_item', item_id=item_id))
            item.quantity -= quantity
            flash('Items removed successfully!', 'success')
        else:  # action == 'add'
            item.quantity += quantity
            flash('Stock added successfully!', 'success')

        db.session.commit()
        return redirect(url_for('inventory'))

    return render_template('use_item.html', item=item, form=form)

@app.route('/delete_item/<int:item_id>', methods=['GET', 'POST'])
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    db.session.delete(item)
    db.session.commit()
    flash('Item deleted!', 'danger')
    return redirect(url_for('inventory'))

@app.route('/documents', methods=['GET'])
def documents():
    query = request.args.get('search', '')  # Get the search query from the URL
    documents = Document.query.join(Document.category, isouter=True).filter(
        db.or_(
            Document.name.contains(query),
            db.or_(
                DocumentCategory.name.contains(query),
                db.and_(query != '', Document.category == None)  # Match None categories when searching for 'None'
            )
        )
    ).all()
    form = DocumentForm()
    return render_template('documents.html', documents=documents, query=query, form=form)

@app.route('/upload_document', methods=['GET', 'POST'])
def upload_document():
    form = DocumentForm()
    if form.validate_on_submit():
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            file.save(file_path)

            document = Document(
                name=form.name.data,
                category_id=None if form.category.data == 0 else form.category.data,
                file_path=filename
            )
            db.session.add(document)
            db.session.commit()
            flash('Document uploaded successfully!', 'success')
            return redirect(url_for('documents'))
        else:
            flash('Invalid file type.', 'danger')
    return render_template('upload_document.html', form=form)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/uploads/<path:filename>')
def download_document(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/edit_document/<int:document_id>', methods=['GET', 'POST'])
def edit_document(document_id):
    document = Document.query.get_or_404(document_id)
    form = DocumentForm(obj=document)

    if form.validate_on_submit():
        document.name = form.name.data
        document.category_id = None if form.category.data == 0 else form.category.data
        db.session.commit()
        flash('Document updated successfully!', 'success')
        return redirect(url_for('documents'))

    if document.category_id is None:
        form.category.data = 0
    else:
        form.category.data = document.category_id

    return render_template('edit_document.html', form=form, document=document)

@app.route('/projects', methods=['GET'])
def projects():
    query = request.args.get('search', '')
    projects = Project.query.filter(Project.name.contains(query) | Project.description.contains(query)).all()
    return render_template('projects.html', projects=projects, query=query)

@app.route('/add_project', methods=['GET', 'POST'])
def add_project():
    form = ProjectForm()
    if form.validate_on_submit():
        new_project = Project(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(new_project)
        
        # Handle items and their quantities
        quantities = request.form.getlist('quantities[]')
        selected_items = request.form.getlist('items')
        
        for item_id, quantity in zip(selected_items, quantities):
            item_id = int(item_id)
            quantity = int(quantity)
            if quantity > 0:
                project_item = ProjectItem(
                    project=new_project,
                    item_id=item_id,
                    quantity=quantity
                )
                db.session.add(project_item)
        
        # Handle documents
        for doc_id in form.documents.data:
            project_doc = ProjectDocument(
                project=new_project,
                document_id=doc_id
            )
            db.session.add(project_doc)
        
        db.session.commit()
        flash('Project created successfully!', 'success')
        return redirect(url_for('projects'))
    
    return render_template('add_project.html', form=form)

@app.route('/use_item_in_project/<int:project_id>', methods=['GET'])
def use_item_in_project(project_id):
    project = Project.query.get_or_404(project_id)
    materials = project.materials_needed.split(',')
    for material in materials:
        item = Item.query.filter_by(name=material.strip()).first()
        if item and item.quantity > 0:
            item.quantity -= 1
            db.session.commit()
    flash('Materials updated for the project!', 'success')
    return redirect(url_for('projects'))

@app.route('/delete_document/<int:document_id>', methods=['GET', 'POST'])
def delete_document(document_id):
    document = Document.query.get_or_404(document_id)

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], document.file_path)

    if os.path.exists(file_path):
        os.remove(file_path)

    db.session.delete(document)
    db.session.commit()
    flash('Document deleted!', 'danger')
    return redirect(url_for('documents'))

@app.route('/delete_project/<int:project_id>', methods=['GET', 'POST'])
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)

    try:
        db.session.delete(project)
        db.session.commit()
        flash('Project deleted successfully!', 'success')
    except:
        db.session.rollback()
        flash('There was an issue deleting the project.', 'danger')

    return redirect(url_for('projects'))

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    form = SettingsForm()
    
    if request.method == 'POST':
        if 'language' in request.form:
            # Fixed CSRF validation - no need for manual validation as Flask-WTF handles it
            session['language'] = request.form['language']
            flash('Language updated successfully!', 'success')
            return redirect(url_for('settings'))
        
        if 'primary_color' in request.form:
            session['primary_color'] = request.form['primary_color']
            session['secondary_color'] = request.form['secondary_color']
            flash('Theme colors updated successfully!', 'success')
            return redirect(url_for('settings'))
        
        try:
            # Handle other form submissions (categories, materials, etc.)
            if form.submit_category.data and form.category.data:
                category = Category(name=form.category.data)
                db.session.add(category)
                db.session.commit()
                flash('Category added successfully!', 'success')
                return redirect(url_for('settings'))
            elif form.submit_material.data and form.material.data:
                material = Material(name=form.material.data)
                db.session.add(material)
                db.session.commit()
                flash('Material added successfully!', 'success')
            elif form.submit_color.data and form.color.data:
                color = Color(name=form.color.data)
                db.session.add(color)
                db.session.commit()
                flash('Color added successfully!', 'success')
            elif form.submit_location.data and form.location.data:
                location = Location(name=form.location.data)
                db.session.add(location)
                db.session.commit()
                flash('Location added successfully!', 'success')
            elif form.submit_document_category.data and form.document_category.data:
                doc_category = DocumentCategory(name=form.document_category.data)
                db.session.add(doc_category)
                db.session.commit()
                flash('Document category added successfully!', 'success')

        except Exception as e:
            db.session.rollback()
            if 'UNIQUE constraint failed' in str(e):
                flash('This item already exists!', 'error')
            else:
                flash('An error occurred while adding the item.', 'error')

    # Get all categories, materials, colors, locations, and document categories
    categories = Category.query.all()
    materials = Material.query.all()
    colors = Color.query.all()
    locations = Location.query.all()
    document_categories = DocumentCategory.query.all()

    return render_template('settings.html',
                         categories=categories,
                         materials=materials,
                         colors=colors,
                         locations=locations,
                         document_categories=document_categories,
                         form=form,
                         current_language=get_language())

@app.route('/delete_material/<int:id>', methods=['POST'])
def delete_material(id):
    material = Material.query.get_or_404(id)
    db.session.delete(material)
    db.session.commit()
    flash('Material deleted!', 'danger')
    return redirect(url_for('settings'))

@app.route('/delete_color/<int:id>', methods=['POST'])
def delete_color(id):
    color = Color.query.get_or_404(id)
    db.session.delete(color)
    db.session.commit()
    flash('Color deleted!', 'danger')
    return redirect(url_for('settings'))

@app.route('/delete_category/<int:id>', methods=['POST'])
def delete_category(id):
    category = Category.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('Category deleted!', 'danger')
    return redirect(url_for('settings'))

@app.route('/delete_document_category/<int:id>', methods=['POST'])
def delete_document_category(id):
    category = DocumentCategory.query.get_or_404(id)
    db.session.delete(category)
    db.session.commit()
    flash('Document category deleted!', 'danger')
    return redirect(url_for('settings'))

@app.route('/delete_location/<int:id>', methods=['POST'])
def delete_location(id):
    location = Location.query.get_or_404(id)
    db.session.delete(location)
    db.session.commit()
    flash('Location deleted!', 'danger')
    return redirect(url_for('settings'))

@app.context_processor
def inject_theme_colors():
    return {
        'primary_color': session.get('primary_color', '#C4DFE6'),
        'secondary_color': session.get('secondary_color', '#66A5AD')
    }

@app.context_processor
def inject_csrf_token():
    return dict(csrf_token=lambda: '<input type="hidden" name="csrf_token" value="{0}">'.format(generate_csrf()))

@app.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    form = ProjectForm(obj=project)

    if form.validate_on_submit():
        project.name = form.name.data
        project.description = form.description.data
        
        # Clear existing items and documents
        for item in project.items:
            db.session.delete(item)
        for doc in project.documents:
            db.session.delete(doc)
        
        # Add new items and their quantities
        quantities = request.form.getlist('quantities[]')
        selected_items = request.form.getlist('items')
        
        for item_id, quantity in zip(selected_items, quantities):
            item_id = int(item_id)
            quantity = int(quantity)
            if quantity > 0:
                project_item = ProjectItem(
                    project=project,
                    item_id=item_id,
                    quantity=quantity
                )
                db.session.add(project_item)
        
        # Add new documents
        for doc_id in form.documents.data:
            project_doc = ProjectDocument(
                project=project,
                document_id=doc_id
            )
            db.session.add(project_doc)
        
        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('projects'))
    
    # Set initial values for items and documents
    form.items.data = [item.item_id for item in project.items]
    form.documents.data = [doc.document_id for doc in project.documents]
    
    # Prepare items and documents for JSON serialization
    items_data = [{'id': item.item_id, 'quantity': item.quantity} for item in project.items]
    documents_data = [{'id': doc.document_id} for doc in project.documents]
    
    return render_template('edit_project.html', 
                         form=form, 
                         project=project,
                         items_data=items_data,
                         documents_data=documents_data)

@app.route('/export_csv')
def export_csv():
    try:
        # Create a memory file to store all CSV files
        memory_file = io.BytesIO()
        with zipfile.ZipFile(memory_file, 'w') as zf:
            # Export items
            items_csv = io.StringIO()
            items_writer = csv.writer(items_csv)
            items_writer.writerow(['id', 'name', 'quantity', 'min_stock_level', 'category_id', 'location_id', 'material_id', 'color_id'])
            for item in Item.query.all():
                items_writer.writerow([
                    item.id, item.name, item.quantity, item.min_stock_level,
                    item.category_id, item.location_id, item.material_id, item.color_id
                ])
            zf.writestr('items.csv', items_csv.getvalue())

            # Export categories
            categories_csv = io.StringIO()
            categories_writer = csv.writer(categories_csv)
            categories_writer.writerow(['id', 'name'])
            for category in Category.query.all():
                categories_writer.writerow([category.id, category.name])
            zf.writestr('categories.csv', categories_csv.getvalue())

            # Export locations
            locations_csv = io.StringIO()
            locations_writer = csv.writer(locations_csv)
            locations_writer.writerow(['id', 'name'])
            for location in Location.query.all():
                locations_writer.writerow([location.id, location.name])
            zf.writestr('locations.csv', locations_csv.getvalue())

            # Export materials
            materials_csv = io.StringIO()
            materials_writer = csv.writer(materials_csv)
            materials_writer.writerow(['id', 'name'])
            for material in Material.query.all():
                materials_writer.writerow([material.id, material.name])
            zf.writestr('materials.csv', materials_csv.getvalue())

            # Export colors
            colors_csv = io.StringIO()
            colors_writer = csv.writer(colors_csv)
            colors_writer.writerow(['id', 'name'])
            for color in Color.query.all():
                colors_writer.writerow([color.id, color.name])
            zf.writestr('colors.csv', colors_csv.getvalue())

            # Export document categories
            doc_categories_csv = io.StringIO()
            doc_categories_writer = csv.writer(doc_categories_csv)
            doc_categories_writer.writerow(['id', 'name'])
            for doc_category in DocumentCategory.query.all():
                doc_categories_writer.writerow([doc_category.id, doc_category.name])
            zf.writestr('document_categories.csv', doc_categories_csv.getvalue())

            # Export documents
            documents_csv = io.StringIO()
            documents_writer = csv.writer(documents_csv)
            documents_writer.writerow(['id', 'name', 'category_id', 'file_path'])
            for document in Document.query.all():
                documents_writer.writerow([document.id, document.name, document.category_id, document.file_path])
            zf.writestr('documents.csv', documents_csv.getvalue())

            # Export projects
            projects_csv = io.StringIO()
            projects_writer = csv.writer(projects_csv)
            projects_writer.writerow(['id', 'name', 'description'])
            for project in Project.query.all():
                projects_writer.writerow([project.id, project.name, project.description])
            zf.writestr('projects.csv', projects_csv.getvalue())

            # Export project items
            project_items_csv = io.StringIO()
            project_items_writer = csv.writer(project_items_csv)
            project_items_writer.writerow(['id', 'project_id', 'item_id', 'quantity'])
            for project_item in ProjectItem.query.all():
                project_items_writer.writerow([
                    project_item.id, project_item.project_id, 
                    project_item.item_id, project_item.quantity
                ])
            zf.writestr('project_items.csv', project_items_csv.getvalue())

            # Export project documents
            project_documents_csv = io.StringIO()
            project_documents_writer = csv.writer(project_documents_csv)
            project_documents_writer.writerow(['id', 'project_id', 'document_id'])
            for project_document in ProjectDocument.query.all():
                project_documents_writer.writerow([
                    project_document.id, project_document.project_id, 
                    project_document.document_id
                ])
            zf.writestr('project_documents.csv', project_documents_csv.getvalue())

        # Reset the file pointer to the beginning
        memory_file.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return Response(
            memory_file.getvalue(),
            mimetype='application/zip',
            headers={'Content-Disposition': f'attachment;filename=inventory_export_{timestamp}.zip'}
        )
    except Exception as e:
        flash(f'Error exporting data: {str(e)}', 'error')
        return redirect(url_for('settings'))

@app.route('/import_csv', methods=['POST'])
def import_csv():
    # Create uploads folder if it doesn't exist
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Reset any pending transaction
    db.session.rollback()
    
    try:
        if 'import_file' not in request.files:
            flash('No file part', 'error')
            return redirect(url_for('settings'))
        
        uploaded_file = request.files['import_file']
        if uploaded_file.filename == '':
            flash('No selected file', 'error')
            return redirect(url_for('settings'))
        
        if not uploaded_file.filename.endswith('.zip'):
            flash('Only ZIP files are allowed', 'error')
            return redirect(url_for('settings'))
        
        # Save the file to a temporary location
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], 'temp_import.zip')
        uploaded_file.save(temp_path)
        print(f"Saved uploaded file to {temp_path}")
        
        # Create a clean directory for extraction
        extract_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'extracted')
        if os.path.exists(extract_dir):
            import shutil
            shutil.rmtree(extract_dir)
        os.makedirs(extract_dir)
        print(f"Created extraction directory: {extract_dir}")
        
        # Extract the ZIP file - using the Python standard library
        with zipfile.ZipFile(temp_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
            print(f"Extracted files: {os.listdir(extract_dir)}")
        
        # Create a basic import for categories
        categories_file = os.path.join(extract_dir, 'categories.csv')
        if os.path.exists(categories_file):
            print(f"Found categories file: {categories_file}")
            try:
                # Read and display file content for debugging
                with open(categories_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"Categories file content (first 200 chars): {content[:200]}")
                
                # Import categories
                with open(categories_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader)  # Skip header
                    print(f"Categories header: {header}")
                    count = 0
                    for row in reader:
                        if len(row) > 1 and row[1]:  # Assuming 2nd column is name
                            category_name = row[1].strip()
                            print(f"Processing category: {category_name}")
                            existing = Category.query.filter_by(name=category_name).first()
                            if not existing:
                                category = Category(name=category_name)
                                db.session.add(category)
                                count += 1
                    db.session.commit()
                    print(f"Added {count} categories")
                    flash(f"Added {count} categories", "success")
            except Exception as e:
                print(f"Error processing categories: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Create a basic import for materials
        materials_file = os.path.join(extract_dir, 'materials.csv')
        if os.path.exists(materials_file):
            print(f"Found materials file: {materials_file}")
            try:
                # Import materials
                with open(materials_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader)  # Skip header
                    print(f"Materials header: {header}")
                    count = 0
                    for row in reader:
                        if len(row) > 1 and row[1]:  # Assuming 2nd column is name
                            material_name = row[1].strip()
                            print(f"Processing material: {material_name}")
                            existing = Material.query.filter_by(name=material_name).first()
                            if not existing:
                                material = Material(name=material_name)
                                db.session.add(material)
                                count += 1
                    db.session.commit()
                    print(f"Added {count} materials")
                    flash(f"Added {count} materials", "success")
            except Exception as e:
                print(f"Error processing materials: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Create a basic import for colors
        colors_file = os.path.join(extract_dir, 'colors.csv')
        if os.path.exists(colors_file):
            print(f"Found colors file: {colors_file}")
            try:
                # Import colors
                with open(colors_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader)  # Skip header
                    print(f"Colors header: {header}")
                    count = 0
                    for row in reader:
                        if len(row) > 1 and row[1]:  # Assuming 2nd column is name
                            color_name = row[1].strip()
                            print(f"Processing color: {color_name}")
                            existing = Color.query.filter_by(name=color_name).first()
                            if not existing:
                                color = Color(name=color_name)
                                db.session.add(color)
                                count += 1
                    db.session.commit()
                    print(f"Added {count} colors")
                    flash(f"Added {count} colors", "success")
            except Exception as e:
                print(f"Error processing colors: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Create a basic import for locations
        locations_file = os.path.join(extract_dir, 'locations.csv')
        if os.path.exists(locations_file):
            print(f"Found locations file: {locations_file}")
            try:
                # Import locations
                with open(locations_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader)  # Skip header
                    print(f"Locations header: {header}")
                    count = 0
                    for row in reader:
                        if len(row) > 1 and row[1]:  # Assuming 2nd column is name
                            location_name = row[1].strip()
                            print(f"Processing location: {location_name}")
                            existing = Location.query.filter_by(name=location_name).first()
                            if not existing:
                                location = Location(name=location_name)
                                db.session.add(location)
                                count += 1
                    db.session.commit()
                    print(f"Added {count} locations")
                    flash(f"Added {count} locations", "success")
            except Exception as e:
                print(f"Error processing locations: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Create a basic import for document categories
        doc_categories_file = os.path.join(extract_dir, 'document_categories.csv')
        if os.path.exists(doc_categories_file):
            print(f"Found document categories file: {doc_categories_file}")
            try:
                # Import document categories
                with open(doc_categories_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader)  # Skip header
                    print(f"Document categories header: {header}")
                    count = 0
                    for row in reader:
                        if len(row) > 1 and row[1]:  # Assuming 2nd column is name
                            doc_category_name = row[1].strip()
                            print(f"Processing document category: {doc_category_name}")
                            existing = DocumentCategory.query.filter_by(name=doc_category_name).first()
                            if not existing:
                                doc_category = DocumentCategory(name=doc_category_name)
                                db.session.add(doc_category)
                                count += 1
                    db.session.commit()
                    print(f"Added {count} document categories")
                    flash(f"Added {count} document categories", "success")
            except Exception as e:
                print(f"Error processing document categories: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Now import items
        items_file = os.path.join(extract_dir, 'items.csv')
        if os.path.exists(items_file):
            print(f"Found items file: {items_file}")
            try:
                # Read and display file content for debugging
                with open(items_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"Items file content (first 200 chars): {content[:200]}")
                
                # Import items
                with open(items_file, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    header = next(reader)  # Skip header
                    print(f"Items header: {header}")
                    
                    # Find the index of each column
                    name_idx = header.index('name') if 'name' in header else 1
                    quantity_idx = header.index('quantity') if 'quantity' in header else 2
                    min_stock_idx = header.index('min_stock_level') if 'min_stock_level' in header else 3
                    
                    count = 0
                    for row in reader:
                        if len(row) > name_idx and row[name_idx]:
                            try:
                                item_name = row[name_idx].strip()
                                print(f"Processing item: {item_name}")
                                
                                # Skip if item already exists
                                if Item.query.filter_by(name=item_name).first():
                                    print(f"Item {item_name} already exists, skipping.")
                                    continue
                                
                                # Get quantity and min_stock
                                quantity = 0
                                if len(row) > quantity_idx and row[quantity_idx]:
                                    try:
                                        quantity = int(row[quantity_idx])
                                    except ValueError:
                                        print(f"Invalid quantity for {item_name}: {row[quantity_idx]}")
                                
                                min_stock = 0
                                if len(row) > min_stock_idx and row[min_stock_idx]:
                                    try:
                                        min_stock = int(row[min_stock_idx])
                                    except ValueError:
                                        print(f"Invalid min_stock for {item_name}: {row[min_stock_idx]}")
                                
                                # Create a new item
                                item = Item(
                                    name=item_name,
                                    quantity=quantity,
                                    min_stock_level=min_stock
                                )
                                db.session.add(item)
                                count += 1
                                
                                # Commit every 10 items to avoid long transactions
                                if count % 10 == 0:
                                    db.session.commit()
                                    print(f"Committed batch, total so far: {count}")
                            except Exception as e:
                                print(f"Error processing item {row}: {str(e)}")
                                continue
                    
                    # Final commit
                    db.session.commit()
                    print(f"Added {count} items")
                    flash(f"Added {count} items", "success")
            except Exception as e:
                print(f"Error processing items: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Clean up
        try:
            import shutil
            shutil.rmtree(extract_dir)
            os.remove(temp_path)
            print("Cleaned up temporary files")
        except Exception as e:
            print(f"Error cleaning up: {str(e)}")
        
        return redirect(url_for('settings'))
        
    except Exception as e:
        db.session.rollback()
        flash(f"Import error: {str(e)}", "error")
        print(f"General import error: {str(e)}")
        import traceback
        traceback.print_exc()
        return redirect(url_for('settings'))

# Handle CSRF errors more gracefully
@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash('Security token expired or invalid. Please try again.', 'error')
    return redirect(request.referrer or url_for('dashboard'))