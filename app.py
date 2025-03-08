import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, IntegerField, SelectField, SubmitField, SelectMultipleField, StringField, TextAreaField
from wtforms.validators import DataRequired, NumberRange
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from datetime import datetime
from translations import translations

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads/'  # Folder for storing files
app.config['ALLOWED_EXTENSIONS'] = {'pdf', 'doc', 'docx', 'txt', 'xlsx'}

# Initialize CSRF protection
csrf = CSRFProtect(app)

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
            session['language'] = request.form['language']
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
                return redirect(url_for('settings', clear_input=1))
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